import streamlit as st
import os
import logging
import uuid
import tempfile
import shutil
import json
import re
import hashlib
import hmac
import sqlite3
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
# Ollama imports (local deployment)
# from langchain_ollama import OllamaEmbeddings, ChatOllama
# import ollama
# OpenAI imports (cloud deployment)
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.retrievers.multi_query import MultiQueryRetriever
import openai
# LLM Guard imports (optional for enhanced security)
try:
    from llm_guard import scan_output, scan_prompt
    from llm_guard.input_scanners import Anonymize, PromptInjection, TokenLimit, Toxicity
    from llm_guard.output_scanners import Deanonymize, NoRefusal, Relevance, Sensitive
    from llm_guard.vault import Vault
    LLM_GUARD_AVAILABLE = True
except ImportError:
    LLM_GUARD_AVAILABLE = False
    print("⚠️ LLM Guard not available - using basic security measures")

from security_utils import (
    log_authentication_attempt, log_file_access, log_directory_access,
    validate_file_type, sanitize_user_input, check_rate_limit, get_security_stats,
    check_daily_cover_letter_limit, record_cover_letter_generation, get_daily_usage_stats,
    get_admin_users, reset_user_daily_limit
)

# Initialize LLM Guard if available
if LLM_GUARD_AVAILABLE:
    try:
        vault = Vault()
        # Use simpler scanners that don't require heavy models
        input_scanners = [TokenLimit(), PromptInjection()]
        output_scanners = [NoRefusal()]
    except Exception as e:
        print(f"⚠️ LLM Guard initialization failed: {e}")
        LLM_GUARD_AVAILABLE = False
        input_scanners = []
        output_scanners = []
else:
    input_scanners = []
    output_scanners = []


# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure OpenAI API
try:
    # Try to get API key from Streamlit secrets (production)
    if hasattr(st, 'secrets') and 'openai' in st.secrets:
        openai.api_key = st.secrets['openai']['api_key']
        os.environ['OPENAI_API_KEY'] = st.secrets['openai']['api_key']
    # Fallback to environment variable (local development)
    elif 'OPENAI_API_KEY' in os.environ:
        openai.api_key = os.environ['OPENAI_API_KEY']
    else:
        st.error("⚠️ OpenAI API key not found. Please set it in secrets.toml or environment variables.")
        st.stop()
except Exception as e:
    logging.warning(f"OpenAI API key configuration warning: {e}")

# Constants
# Ollama models (local deployment)
# MODEL_NAME = "qwen3:8b"
# EMBEDDING_MODEL = "nomic-embed-text"

# OpenAI models (cloud deployment)
MODEL_NAME = "gpt-4o-mini"  # Cost-effective OpenAI model
EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI embedding model

BASE_PERSIST_DIRECTORY = "./faiss_db_multiuser"
USER_PREFERENCES_DIR = "./user_preferences"
INVITED_USERS_FILE = "./invited_users.json"


def load_invited_users():
    """Load the list of invited users from JSON file and Streamlit secrets."""
    invited_users = {}
    
    # Load from JSON file
    if os.path.exists(INVITED_USERS_FILE):
        try:
            with open(INVITED_USERS_FILE, 'r') as f:
                data = json.load(f)
                invited_users.update(data.get('invited_users', {}))
        except Exception as e:
            logging.error(f"Error loading invited users from file: {e}")
    
    # Load from Streamlit secrets (for production)
    try:
        if hasattr(st, 'secrets') and 'invited_users' in st.secrets:
            secrets_users = dict(st.secrets['invited_users'])
            # Convert to the expected format
            for email, name in secrets_users.items():
                invited_users[email] = {
                    "name": name,
                    "invited_date": "2025-01-15",  # Default date
                    "status": "active",
                    "access_level": "user"
                }
    except Exception as e:
        logging.error(f"Error loading invited users from secrets: {e}")
    
    return invited_users


def is_user_invited(email):
    """Check if a user email is in the invited users list."""
    invited_users = load_invited_users()
    return email.lower() in [user_email.lower() for user_email in invited_users.keys()]


def get_user_info(email):
    """Get user information from invited users list."""
    invited_users = load_invited_users()
    for user_email, user_info in invited_users.items():
        if user_email.lower() == email.lower():
            return user_info
    return None


def validate_email_format(email):
    """Validate email format using regex."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None


def create_session_token(email):
    """Create a secure session token for the user."""
    timestamp = datetime.now().isoformat()
    data = f"{email}:{timestamp}"
    try:
        secret_key = st.secrets.get('auth', {}).get('invitation_secret', 'default-secret-key')
    except:
        secret_key = 'default-secret-key'
    
    token = hmac.new(
        secret_key.encode(),
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return f"{token}:{timestamp}"


def verify_session_token(email, token):
    """Verify a session token is valid and not expired."""
    try:
        token_hash, timestamp_str = token.split(':', 1)
        timestamp = datetime.fromisoformat(timestamp_str)
        
        # Check if token is expired (24 hours by default)
        try:
            timeout_hours = st.secrets.get('security', {}).get('session_timeout_hours', 24)
        except:
            timeout_hours = 24
            
        if datetime.now() - timestamp > timedelta(hours=timeout_hours):
            return False
        
        # Verify token
        data = f"{email}:{timestamp_str}"
        try:
            secret_key = st.secrets.get('auth', {}).get('invitation_secret', 'default-secret-key')
        except:
            secret_key = 'default-secret-key'
            
        expected_token = hmac.new(
            secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(token_hash, expected_token)
    except Exception as e:
        logging.error(f"Error verifying session token: {e}")
        return False


def show_authentication_page():
    """Display the authentication page for invitation-only access."""
    st.title("🔐 Resume Assistant - Invitation Only")
    st.markdown("---")
    
    st.info("🎯 This application is invitation-only. Please enter your invited email address to access the resume assistant.")
    
    with st.form("authentication_form"):
        email = st.text_input("📧 Email Address", placeholder="your.email@example.com")
        submit_button = st.form_submit_button("🚀 Access Application")
        
        if submit_button:
            if not email:
                st.error("❌ Please enter your email address.")
                log_authentication_attempt("", False)
                return False
            
            if not validate_email_format(email):
                st.error("❌ Please enter a valid email address.")
                log_authentication_attempt(email, False)
                return False
            
            # Check rate limiting
            if not check_rate_limit(email, "authentication", max_requests=5, time_window_minutes=15):
                st.error("❌ Too many authentication attempts. Please try again later.")
                return False
            
            if not is_user_invited(email):
                st.error("❌ Sorry, your email is not on the invited users list. Please contact the administrator for access.")
                st.info("💡 If you believe this is an error, please double-check your email address spelling.")
                log_authentication_attempt(email, False)
                return False
            
            # Successful authentication
            user_info = get_user_info(email)
            st.success(f"✅ Welcome, {user_info.get('name', email)}! Access granted.")
            
            # Create session
            st.session_state.authenticated = True
            st.session_state.user_email = email.lower()
            st.session_state.user_info = user_info
            st.session_state.session_token = create_session_token(email.lower())
            st.session_state.auth_timestamp = datetime.now()
            
            # Log successful access
            log_authentication_attempt(email, True)
            logging.info(f"User authenticated successfully: {email}")
            
            st.rerun()
    
    # Show contact information
    st.markdown("---")
    with st.expander("ℹ️ Need Access?"):
        st.markdown("""
        **This is an invitation-only application.** 
        
        If you need access to the Resume Assistant:
        1. Contact the application administrator
        2. Provide your email address to be added to the invited users list
        3. Wait for confirmation before attempting to access the application
        
        **Features available to invited users:**
        - AI-powered cover letter generation
        - Resume analysis and optimization
        - Personalized writing style learning
        - Secure data storage and privacy
        """)
    
    return False


def check_authentication():
    """Check if user is authenticated and session is valid."""
    if not st.session_state.get('authenticated', False):
        return False
    
    email = st.session_state.get('user_email')
    token = st.session_state.get('session_token')
    
    if not email or not token:
        return False
    
    # Verify user is still invited
    if not is_user_invited(email):
        st.session_state.authenticated = False
        return False
    
    # Verify session token
    if not verify_session_token(email, token):
        st.session_state.authenticated = False
        return False
    
    return True


def logout_user():
    """Log out the current user and clear session."""
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'user_email' in st.session_state:
        del st.session_state.user_email
    if 'user_info' in st.session_state:
        del st.session_state.user_info
    if 'session_token' in st.session_state:
        del st.session_state.session_token
    if 'auth_timestamp' in st.session_state:
        del st.session_state.auth_timestamp


def initialize_user_session():
    """Initialize user session with authenticated email-based ID."""
    # Use authenticated email as the permanent user ID
    if st.session_state.get('authenticated') and st.session_state.get('user_email'):
        user_email = st.session_state.user_email
        # Create a safe user ID from email for directory names
        safe_user_id = user_email.replace('@', '_at_').replace('.', '_').replace('+', '_plus_')
        
        if 'user_id' not in st.session_state:
            st.session_state.user_id = safe_user_id
            st.session_state.session_start = datetime.now()
            st.session_state.extracted_email = user_email
            st.session_state.permanent_user_id = user_email
            logging.info(f"Authenticated user session created: {user_email} -> {safe_user_id}")
    else:
        # Fallback for unauthenticated access (shouldn't happen in production)
        if 'user_id' not in st.session_state:
            st.session_state.user_id = str(uuid.uuid4())[:8]
            st.session_state.session_start = datetime.now()
    
    # Initialize session state variables
    if 'vector_db_ready' not in st.session_state:
        st.session_state.vector_db_ready = False
    if 'uploaded_file_processed' not in st.session_state:
        st.session_state.uploaded_file_processed = False
    if 'extracted_email' not in st.session_state:
        st.session_state.extracted_email = None
    if 'permanent_user_id' not in st.session_state:
        st.session_state.permanent_user_id = None


def extract_email_from_resume(file_content):
    """Extract email address from resume content to use as permanent user ID."""
    # Simple regex to find email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, file_content)
    return emails[0] if emails else None


def get_user_permanent_id(uploaded_file):
    """Get permanent user ID from email in resume, fallback to session ID."""
    if uploaded_file and hasattr(st.session_state, 'extracted_email'):
        return st.session_state.extracted_email
    return st.session_state.user_id


def initialize_user_preferences():
    """Initialize user preferences directory."""
    if not os.path.exists(USER_PREFERENCES_DIR):
        os.makedirs(USER_PREFERENCES_DIR)


def load_user_preferences(user_email):
    """Load user preferences from file."""
    preferences_file = os.path.join(USER_PREFERENCES_DIR, f"{user_email.replace('@', '_at_').replace('.', '_')}.json")
    
    if os.path.exists(preferences_file):
        try:
            with open(preferences_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading user preferences: {e}")
    
    # Default preferences structure
    return {
        "user_email": user_email,
        "preferred_highlights": [],
        "writing_style_patterns": {
            "common_phrases": [],
            "sentence_structure_preferences": [],
            "tone_indicators": []
        },
        "edit_patterns": {
            "commonly_removed_words": [],
            "commonly_added_phrases": [],
            "formatting_preferences": []
        },
        "job_application_history": [],
        "last_updated": datetime.now().isoformat(),
        "usage_count": 0
    }


def save_user_preferences(user_email, preferences):
    """Save user preferences to file."""
    preferences_file = os.path.join(USER_PREFERENCES_DIR, f"{user_email.replace('@', '_at_').replace('.', '_')}.json")
    preferences["last_updated"] = datetime.now().isoformat()
    
    try:
        with open(preferences_file, 'w') as f:
            json.dump(preferences, f, indent=2)
        logging.info(f"User preferences saved for {user_email}")
    except Exception as e:
        logging.error(f"Error saving user preferences: {e}")


def analyze_user_edits(original_text, edited_text):
    """Analyze the differences between original and edited text to learn user patterns."""
    import difflib
    
    logging.info("DEBUG: Starting edit analysis")
    logging.info(f"DEBUG: Original text length: {len(original_text)}")
    logging.info(f"DEBUG: Edited text length: {len(edited_text)}")
    
    # Split into words for analysis
    original_words = original_text.split()
    edited_words = edited_text.split()
    
    logging.info(f"DEBUG: Original words count: {len(original_words)}")
    logging.info(f"DEBUG: Edited words count: {len(edited_words)}")
    
    # Find differences
    differ = difflib.SequenceMatcher(None, original_words, edited_words)
    
    edit_patterns = {
        "removals": [],
        "additions": [],
        "replacements": []
    }
    
    for tag, i1, i2, j1, j2 in differ.get_opcodes():
        if tag == 'delete':
            removed_words = original_words[i1:i2]
            edit_patterns["removals"].extend(removed_words)
            logging.info(f"DEBUG: REMOVED words: {removed_words}")
        elif tag == 'insert':
            added_words = edited_words[j1:j2]
            edit_patterns["additions"].extend(added_words)
            logging.info(f"DEBUG: ADDED words: {added_words}")
        elif tag == 'replace':
            replacement = {
                "from": " ".join(original_words[i1:i2]),
                "to": " ".join(edited_words[j1:j2])
            }
            edit_patterns["replacements"].append(replacement)
            logging.info(f"DEBUG: REPLACED: '{replacement['from']}' -> '{replacement['to']}'")
    
    logging.info(f"DEBUG: Final edit patterns: {edit_patterns}")
    return edit_patterns


def update_user_preferences_with_session_data(user_email, highlights, original_letter, edited_letter, job_description):
    """Update user preferences based on current session data."""
    logging.info(f"DEBUG: update_user_preferences_with_session_data called for user: {user_email}")
    logging.info(f"DEBUG: Has original_letter: {bool(original_letter)}")
    logging.info(f"DEBUG: Has edited_letter: {bool(edited_letter)}")
    logging.info(f"DEBUG: Letters are different: {original_letter != edited_letter if original_letter and edited_letter else 'N/A'}")
    
    preferences = load_user_preferences(user_email)
    
    # Update preferred highlights
    if highlights:
        for highlight in highlights:
            if highlight not in preferences["preferred_highlights"]:
                preferences["preferred_highlights"].append(highlight)
    
    # Analyze edits if both texts exist
    if original_letter and edited_letter and original_letter != edited_letter:
        logging.info("DEBUG: Analyzing user edits...")
        edit_patterns = analyze_user_edits(original_letter, edited_letter)
        
        # Update edit patterns
        preferences["edit_patterns"]["commonly_removed_words"].extend(edit_patterns["removals"])
        preferences["edit_patterns"]["commonly_added_phrases"].extend(edit_patterns["additions"])
        
        logging.info(f"DEBUG: Updated preferences with {len(edit_patterns['removals'])} removed words and {len(edit_patterns['additions'])} added phrases")
        
        # Keep only unique items and limit size
        preferences["edit_patterns"]["commonly_removed_words"] = list(set(
            preferences["edit_patterns"]["commonly_removed_words"][-50:]  # Keep last 50
        ))
        preferences["edit_patterns"]["commonly_added_phrases"] = list(set(
            preferences["edit_patterns"]["commonly_added_phrases"][-50:]  # Keep last 50
        ))
    
    # Add to job application history
    job_entry = {
        "date": datetime.now().isoformat(),
        "job_company": job_description[:100] + "..." if len(job_description) > 100 else job_description,
        "highlights_used": highlights,
        "session_id": st.session_state.user_id
    }
    preferences["job_application_history"].append(job_entry)
    
    # Keep only last 20 applications
    preferences["job_application_history"] = preferences["job_application_history"][-20:]
    
    # Update usage count
    preferences["usage_count"] += 1
    
    # Save updated preferences
    save_user_preferences(user_email, preferences)
    
    return preferences


def generate_personalized_prompt_additions(user_email):
    """Generate additional prompt context based on user preferences."""
    preferences = load_user_preferences(user_email)
    
    logging.info(f"DEBUG: Loading preferences for user: {user_email}")
    logging.info(f"DEBUG: Preferences loaded: {preferences}")
    
    prompt_additions = []
    
    # Add preferred highlights context
    if preferences["preferred_highlights"]:
        prompt_additions.append(f"The user typically likes to highlight these strengths: {', '.join(preferences['preferred_highlights'][-5:])}")
    
    # Add writing style preferences
    if preferences["edit_patterns"]["commonly_added_phrases"]:
        common_phrases = [phrase for phrase in preferences["edit_patterns"]["commonly_added_phrases"] if len(phrase.split()) > 1][-3:]
        if common_phrases:
            prompt_additions.append(f"The user often includes phrases like: {', '.join(common_phrases)}")
    
    # Add words/phrases the user typically removes
    if preferences["edit_patterns"]["commonly_removed_words"]:
        avoided_words = preferences["edit_patterns"]["commonly_removed_words"][-5:]
        prompt_additions.append(f"The user typically avoids these words/phrases: {', '.join(avoided_words)}")
    
    result = "\n".join(prompt_additions) if prompt_additions else ""
    logging.info(f"DEBUG: Generated prompt additions: {result}")
    
    return result


def check_user_has_resume_data(user_id):
    """Check if user has existing FAISS resume data."""
    try:
        user_persist_dir, _ = get_user_directories(user_id)
        faiss_index_path = os.path.join(user_persist_dir, "index.faiss")
        faiss_docstore_path = os.path.join(user_persist_dir, "index.pkl")  # Fixed: FAISS saves as index.pkl
        return os.path.exists(faiss_index_path) and os.path.exists(faiss_docstore_path)
    except Exception:
        return False


def get_user_directories(user_id):
    """Get user-specific directory paths with enhanced security validation."""
    # Validate that user_id corresponds to authenticated user
    if st.session_state.get('authenticated'):
        authenticated_user_id = st.session_state.get('user_email', '').replace('@', '_at_').replace('.', '_').replace('+', '_plus_')
        if user_id != authenticated_user_id:
            logging.warning(f"Security violation: User {st.session_state.get('user_email')} attempting to access directories for {user_id}")
            raise ValueError("Unauthorized access to user directories")
    
    # Sanitize user_id to prevent directory traversal attacks
    safe_user_id = re.sub(r'[^a-zA-Z0-9_.-]', '_', str(user_id))
    if '..' in safe_user_id or '/' in safe_user_id or '\\' in safe_user_id:
        raise ValueError("Invalid user_id format")
    
    user_persist_dir = os.path.join(BASE_PERSIST_DIRECTORY, f"user_{safe_user_id}")
    user_uploads_dir = os.path.join("./uploads", f"user_{safe_user_id}")
    
    # Create directories if they don't exist
    os.makedirs(user_persist_dir, exist_ok=True)
    os.makedirs(user_uploads_dir, exist_ok=True)
    
    # Log directory access for audit purposes
    user_email = st.session_state.get('user_email', 'unknown')
    log_directory_access(user_email, user_persist_dir)
    logging.info(f"User {user_email} accessing directories: {user_persist_dir}")
    
    return user_persist_dir, user_uploads_dir


def save_uploaded_file(uploaded_file, user_id):
    """Save uploaded file to user-specific directory with enhanced security."""
    # Validate file type
    if not validate_file_type(uploaded_file.name):
        st.error("❌ Invalid file type. Please upload PDF, DOC, DOCX, or TXT files only.")
        return None
    
    # Check rate limiting for file uploads
    user_email = st.session_state.get('user_email', 'unknown')
    if not check_rate_limit(user_email, "file_upload", max_requests=10, time_window_minutes=60):
        st.error("❌ Too many file uploads. Please try again later.")
        return None
    
    user_persist_dir, user_uploads_dir = get_user_directories(user_id)
    
    # Sanitize filename to prevent path traversal
    safe_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', uploaded_file.name)
    file_path = os.path.join(user_uploads_dir, safe_filename)
    
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    # Log file access
    log_file_access(user_email, file_path, "upload")
    
    # For authenticated users, we already know their email
    if st.session_state.get('authenticated') and st.session_state.get('user_email'):
        user_email = st.session_state.user_email
        st.session_state.extracted_email = user_email
        st.session_state.permanent_user_id = user_email
        
        # Initialize user preferences
        initialize_user_preferences()
        preferences = load_user_preferences(user_email)
        st.session_state.user_preferences = preferences
        
        # Show personalization info to user
        if preferences["usage_count"] > 0:
            st.success(f"✨ Welcome back! We've loaded your preferences from {preferences['usage_count']} previous sessions.")
        else:
            st.info("🎉 Welcome! This appears to be your first time using the assistant. We'll learn your preferences as you use the app.")
        
        logging.info(f"File uploaded for authenticated user: {user_email}")
        return file_path
    
    # Fallback: Try to extract email from the uploaded file (legacy behavior)
    try:
        loader = PyPDFLoader(file_path=file_path)
        data = loader.load()
        if data:
            file_content = " ".join([doc.page_content for doc in data])
            extracted_email = extract_email_from_resume(file_content)
            if extracted_email:
                st.session_state.extracted_email = extracted_email
                st.session_state.permanent_user_id = extracted_email
                logging.info(f"Extracted email from resume: {extracted_email}")
                
                # Initialize user preferences
                initialize_user_preferences()
                preferences = load_user_preferences(extracted_email)
                st.session_state.user_preferences = preferences
                
                # Show personalization info to user
                if preferences["usage_count"] > 0:
                    st.success(f"✨ Welcome back! We've loaded your preferences from {preferences['usage_count']} previous sessions.")
                else:
                    st.info("🆕 New user detected! We'll start learning your preferences to personalize future cover letters.")
            else:
                st.warning("⚠️ No email found in resume. Using session-based preferences only.")
    except Exception as e:
        logging.error(f"Error extracting email from resume: {e}")
        st.warning("⚠️ Could not extract email from resume. Using session-based preferences only.")
    
    logging.info(f"File saved for user {user_id}: {file_path}")
    return file_path


def ingest_uploaded_file(file_path):
    """Load uploaded documents (PDF or other formats)."""
    if os.path.exists(file_path):
        try:
            loader = PyPDFLoader(file_path=file_path)
            data = loader.load()
            logging.info("File loaded successfully.")
            return data
        except Exception as e:
            logging.error(f"Error loading file: {str(e)}")
            st.error(f"Error loading file: {str(e)}")
            return None
    else:
        logging.error(f"File not found at path: {file_path}")
        st.error("File not found.")
        return None


def split_documents(documents):
    """Split documents into smaller chunks optimized for short documents (2-page resume + 1-page job desc)."""
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
    chunks = text_splitter.split_documents(documents)
    logging.info("Documents split into chunks.")
    return chunks


def load_user_vector_db(user_id, uploaded_file_path=None):
    """Load or create user-specific vector database."""
    try:
        user_persist_dir, _ = get_user_directories(user_id)
        user_collection_name = f"resume_{user_id}"
        
        # OpenAI embedding setup (cloud deployment)
        embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)

        # Check if user already has a vector database
        faiss_index_path = os.path.join(user_persist_dir, "index.faiss")
        faiss_docstore_path = os.path.join(user_persist_dir, "index.pkl")  # Fixed: FAISS saves as index.pkl, not docstore.pkl
        
        logging.info(f"Checking for FAISS files: {faiss_index_path}, {faiss_docstore_path}")
        
        if os.path.exists(faiss_index_path) and os.path.exists(faiss_docstore_path):
            logging.info(f"Loading existing FAISS database for user {user_id}")
            vector_db = FAISS.load_local(
                user_persist_dir,
                embedding,
                allow_dangerous_deserialization=True
            )
            logging.info(f"Successfully loaded existing vector database for user {user_id}")
            return vector_db
        elif uploaded_file_path:
            logging.info(f"Creating new vector database from file: {uploaded_file_path}")
            # Create new vector database from uploaded file
            data = ingest_uploaded_file(uploaded_file_path)
            if data is None:
                logging.error("Failed to ingest uploaded file")
                return None

            # Split the documents into chunks
            chunks = split_documents(data)
            logging.info(f"Split document into {len(chunks)} chunks")

            vector_db = FAISS.from_documents(
                documents=chunks,
                embedding=embedding
            )
            # Save the FAISS index
            logging.info(f"Saving FAISS database to: {user_persist_dir}")
            try:
                vector_db.save_local(user_persist_dir)
                logging.info(f"FAISS save_local completed")
                
                # List all files in the directory to see what was actually created
                if os.path.exists(user_persist_dir):
                    files_created = os.listdir(user_persist_dir)
                    logging.info(f"Files in {user_persist_dir}: {files_created}")
                else:
                    logging.error(f"Directory {user_persist_dir} does not exist after save_local")
                
            except Exception as save_error:
                logging.error(f"Error saving FAISS database: {str(save_error)}")
                return None
            
            # Verify files were created
            if os.path.exists(faiss_index_path) and os.path.exists(faiss_docstore_path):
                logging.info(f"Successfully created and saved vector database for user {user_id}")
            else:
                logging.error(f"FAISS files not found after saving: {faiss_index_path}, {faiss_docstore_path}")
                # Try to find what files were actually created
                if os.path.exists(user_persist_dir):
                    actual_files = os.listdir(user_persist_dir)
                    logging.error(f"Actual files created: {actual_files}")
                return None
                
            return vector_db
        else:
            logging.warning(f"No vector database or file found for user {user_id}")
            return None
            
    except Exception as e:
        logging.error(f"Error in load_user_vector_db: {str(e)}")
        return None


# Usage Tracking Functions
def init_usage_db():
    """Initialize the usage tracking database."""
    db_path = "usage_tracking.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create usage_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            company_name TEXT,
            job_title TEXT,
            cover_letter_length INTEGER,
            processing_time_seconds REAL,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT
        )
    ''')
    
    # Create usage_summary table for quick stats
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_summary (
            user_email TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            first_use DATETIME,
            last_use DATETIME,
            total_cover_letters INTEGER DEFAULT 0,
            total_processing_time REAL DEFAULT 0,
            avg_cover_letter_length REAL DEFAULT 0
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("Usage tracking database initialized")


def log_cover_letter_generation(user_email, user_id, company_name=None, job_title=None, 
                               cover_letter_length=0, processing_time=0, success=True, error_message=None):
    """Log a cover letter generation event."""
    try:
        db_path = "usage_tracking.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Insert usage log
        cursor.execute('''
            INSERT INTO usage_logs 
            (user_email, user_id, action_type, company_name, job_title, 
             cover_letter_length, processing_time_seconds, success, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_email, user_id, 'cover_letter_generation', company_name, job_title,
              cover_letter_length, processing_time, success, error_message))
        
        # Update usage summary
        cursor.execute('''
            INSERT OR REPLACE INTO usage_summary 
            (user_email, user_id, first_use, last_use, total_cover_letters, 
             total_processing_time, avg_cover_letter_length)
            VALUES (
                ?, ?, 
                COALESCE((SELECT first_use FROM usage_summary WHERE user_email = ?), CURRENT_TIMESTAMP),
                CURRENT_TIMESTAMP,
                COALESCE((SELECT total_cover_letters FROM usage_summary WHERE user_email = ?), 0) + 1,
                COALESCE((SELECT total_processing_time FROM usage_summary WHERE user_email = ?), 0) + ?,
                (COALESCE((SELECT total_cover_letters * avg_cover_letter_length FROM usage_summary WHERE user_email = ?), 0) + ?) / 
                (COALESCE((SELECT total_cover_letters FROM usage_summary WHERE user_email = ?), 0) + 1)
            )
        ''', (user_email, user_id, user_email, user_email, user_email, processing_time, 
              user_email, cover_letter_length, user_email))
        
        conn.commit()
        conn.close()
        logging.info(f"Usage logged for user {user_email}: {company_name} - {success}")
        
    except Exception as e:
        logging.error(f"Error logging usage: {str(e)}")


def get_user_usage_stats(user_email):
    """Get usage statistics for a specific user."""
    try:
        db_path = "usage_tracking.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get summary stats
        cursor.execute('''
            SELECT total_cover_letters, total_processing_time, avg_cover_letter_length,
                   first_use, last_use
            FROM usage_summary WHERE user_email = ?
        ''', (user_email,))
        
        summary = cursor.fetchone()
        
        # Get recent activity (last 10 generations)
        cursor.execute('''
            SELECT timestamp, company_name, job_title, cover_letter_length, success
            FROM usage_logs 
            WHERE user_email = ? AND action_type = 'cover_letter_generation'
            ORDER BY timestamp DESC LIMIT 10
        ''', (user_email,))
        
        recent_activity = cursor.fetchall()
        
        conn.close()
        
        return {
            'summary': summary,
            'recent_activity': recent_activity
        }
        
    except Exception as e:
        logging.error(f"Error getting usage stats: {str(e)}")
        return None


def get_daily_usage_count(user_email, date=None):
    """Get the number of cover letters generated by a user on a specific date."""
    if date is None:
        date = datetime.now().date()
    
    try:
        db_path = "usage_tracking.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM usage_logs 
            WHERE user_email = ? 
            AND action_type = 'cover_letter_generation'
            AND success = 1
            AND DATE(timestamp) = ?
        ''', (user_email, date))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
        
    except Exception as e:
        logging.error(f"Error getting daily usage count: {str(e)}")
        return 0


def get_all_usage_stats():
    """Get comprehensive usage statistics for admin dashboard."""
    try:
        db_path = "usage_tracking.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Total stats
        cursor.execute('''
            SELECT 
                COUNT(DISTINCT user_email) as total_users,
                COUNT(*) as total_generations,
                AVG(cover_letter_length) as avg_length,
                AVG(processing_time_seconds) as avg_processing_time,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_generations,
                SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_generations
            FROM usage_logs 
            WHERE action_type = 'cover_letter_generation'
        ''')
        
        total_stats = cursor.fetchone()
        
        # Daily activity for last 30 days
        cursor.execute('''
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as generations,
                COUNT(DISTINCT user_email) as active_users
            FROM usage_logs 
            WHERE action_type = 'cover_letter_generation'
            AND timestamp >= date('now', '-30 days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''')
        
        daily_activity = cursor.fetchall()
        
        # Top users
        cursor.execute('''
            SELECT 
                user_email,
                total_cover_letters,
                total_processing_time,
                first_use,
                last_use
            FROM usage_summary
            ORDER BY total_cover_letters DESC
            LIMIT 20
        ''')
        
        top_users = cursor.fetchall()
        
        # Recent activity
        cursor.execute('''
            SELECT 
                timestamp,
                user_email,
                company_name,
                job_title,
                cover_letter_length,
                processing_time_seconds,
                success
            FROM usage_logs 
            WHERE action_type = 'cover_letter_generation'
            ORDER BY timestamp DESC
            LIMIT 50
        ''')
        
        recent_activity = cursor.fetchall()
        
        # Most popular companies
        cursor.execute('''
            SELECT 
                company_name,
                COUNT(*) as applications
            FROM usage_logs 
            WHERE action_type = 'cover_letter_generation'
            AND company_name IS NOT NULL
            AND success = 1
            GROUP BY company_name
            ORDER BY applications DESC
            LIMIT 20
        ''')
        
        popular_companies = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_stats': total_stats,
            'daily_activity': daily_activity,
            'top_users': top_users,
            'recent_activity': recent_activity,
            'popular_companies': popular_companies
        }
        
    except Exception as e:
        logging.error(f"Error getting all usage stats: {str(e)}")
        return None


def show_admin_dashboard():
    """Display admin dashboard with usage analytics."""
    st.header("📊 Usage Analytics Dashboard")
    st.markdown("---")
    
    # Check if user is admin (you can customize this logic)
    user_email = st.session_state.get('user_email', '')
    admin_emails = ['admin@company.com', 'tsztkwok@gmail.com']  # Add your admin emails here
    
    if user_email not in admin_emails:
        st.error("❌ Access denied. Admin privileges required.")
        return
    
    # Get usage statistics
    stats = get_all_usage_stats()
    if not stats:
        st.error("❌ Unable to load usage statistics.")
        return
    
    # Total Statistics
    st.subheader("📈 Overall Statistics")
    total_stats = stats['total_stats']
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", total_stats[0])
    with col2:
        st.metric("Total Generations", total_stats[1])
    with col3:
        success_rate = (total_stats[4] / total_stats[1] * 100) if total_stats[1] > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    with col4:
        avg_processing = total_stats[3] or 0
        st.metric("Avg Processing Time", f"{avg_processing:.2f}s")
    
    # Daily Activity Chart
    st.subheader("📅 Daily Activity (Last 30 Days)")
    if stats['daily_activity']:
        import pandas as pd
        df_daily = pd.DataFrame(stats['daily_activity'], columns=['Date', 'Generations', 'Active Users'])
        st.line_chart(df_daily.set_index('Date')[['Generations', 'Active Users']])
    
    # Top Users
    st.subheader("👥 Top Users")
    if stats['top_users']:
        for i, user in enumerate(stats['top_users'][:10], 1):
            with st.expander(f"{i}. {user[0]} ({user[1]} generations)"):
                st.write(f"**Total Processing Time:** {user[2]:.2f}s")
                st.write(f"**First Use:** {user[3]}")
                st.write(f"**Last Use:** {user[4]}")
    
    # Recent Activity
    st.subheader("🕒 Recent Activity")
    if stats['recent_activity']:
        for activity in stats['recent_activity'][:20]:
            timestamp, email, company, job_title, length, proc_time, success = activity
            status = "✅" if success else "❌"
            company_info = f" - {company}" if company else ""
            job_info = f" ({job_title})" if job_title else ""
            st.write(f"{status} {timestamp} | {email}{company_info}{job_info} | {length} chars | {proc_time:.2f}s")
    
    # Popular Companies
    st.subheader("🏢 Most Popular Companies")
    if stats['popular_companies']:
        col1, col2 = st.columns(2)
        with col1:
            for company, count in stats['popular_companies'][:10]:
                st.write(f"**{company}:** {count} applications")
        with col2:
            # You could add a chart here if you import matplotlib or plotly
            pass


def create_retriever(vector_db, llm):
    """Create a multi-query retriever."""
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI language model assistant. Use the following user question to retrieve relevant documents from a vector database.\nQuestion: {question}""",
    )

    retriever = MultiQueryRetriever.from_llm(
        vector_db.as_retriever(), llm, prompt=QUERY_PROMPT
    )
    logging.info("Retriever created.")
    return retriever


def create_chain(retriever, llm, user_strengths=None, user_email=None):
    """Create the chain with preserved syntax and personalized context."""
    # Build the strength instruction based on user input
    if user_strengths and user_strengths.strip():
        strength_instruction = f"PRIORITY STRENGTHS: Focus primarily on these user-specified strengths and skills: {user_strengths.strip()}"
        main_instruction = "The content of the cover letter should emphasize the user-specified priority strengths above, and supplement with other relevant areas of strength and skills found in the resume matching to the job description"
    else:
        strength_instruction = ""
        main_instruction = "The content of the cover letter focus on the top three areas of strength and skills found in the resume matching to the job description"
    
    # Add personalized context based on user preferences
    personalized_context = ""
    if user_email:
        personalized_additions = generate_personalized_prompt_additions(user_email)
        # Debug logging for personalization
        logging.info(f"DEBUG: Generating personalized prompt for user: {user_email}")
        logging.info(f"DEBUG: Personalized additions: {personalized_additions}")
        if personalized_additions:
            personalized_context = f"\nPERSONALIZATION CONTEXT: Based on the user's previous preferences:\n{personalized_additions}\nPlease incorporate these preferences naturally into the cover letter while maintaining professional tone."
            logging.info(f"DEBUG: Personalized context added to prompt: {personalized_context}")
        else:
            logging.info("DEBUG: No personalized additions generated")
    
    # RAG prompt
    template = f"""You are a Human Resource resume reviewer, your role is to assist the job applicant to create a concise cover letter based on his resume 
by answering the question based ONLY on the following context. The cover letter should ideally be less than 280 words
{strength_instruction}
{main_instruction} and provided with a career plan{personalized_context}

IMPORTANT FORMATTING INSTRUCTIONS:
- Start the cover letter directly with "Dear [Company] Hiring Manager," (replace [Company] with the actual company name from the job description)
- Do NOT include any header information like [Your Name], [Your Address], [City, State, Zip], [Email Address], [Phone Number], [Date], etc.
- Do NOT include company address information
- Begin immediately with the salutation and proceed with the cover letter content
- End with "Sincerely," followed by the candidate's actual name extracted from the resume (NOT "[Your Name]" placeholder)
- Extract the candidate's full name from the resume context and use it in the closing signature

{{context}}
Question: {{question}}
"""

    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    logging.info("Chain created with preserved syntax.")
    return chain


def clean_ai_response(response):
    """Remove <think>...</think> blocks and other unwanted AI artifacts from the response."""
    import re
    
    # Remove <think>...</think> blocks (including multiline)
    cleaned = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove any other common AI artifacts
    cleaned = re.sub(r'</?think>', '', cleaned, flags=re.IGNORECASE)
    
    # Clean up extra whitespace and newlines
    cleaned = re.sub(r'\n\s*\n\s*\n', '\n\n', cleaned)  # Replace multiple newlines with double newlines
    cleaned = cleaned.strip()  # Remove leading/trailing whitespace
    
    return cleaned


def extract_company_name(job_description):
    """Extract company name from job description using common patterns."""
    import re
    
    if not job_description:
        return "company"
    
    # Convert to lowercase for pattern matching
    text = job_description.lower()
    
    # Common patterns for company names in job descriptions
    patterns = [
        r'(?:at|join|for)\s+([A-Z][a-zA-Z\s&,.-]+?)(?:\s+(?:is|are|has|have|we|our|the|in|on|as|to|for|with|and|or|but|,|\.|!|\?))',
        r'([A-Z][a-zA-Z\s&,.-]+?)\s+(?:is|are)\s+(?:looking|seeking|hiring|recruiting)',
        r'company:\s*([A-Z][a-zA-Z\s&,.-]+?)(?:\s|$|\n)',
        r'organization:\s*([A-Z][a-zA-Z\s&,.-]+?)(?:\s|$|\n)',
        r'employer:\s*([A-Z][a-zA-Z\s&,.-]+?)(?:\s|$|\n)',
        r'about\s+([A-Z][a-zA-Z\s&,.-]+?)(?:\s|$|\n)',
        r'([A-Z][a-zA-Z\s&,.-]+?)\s+(?:team|group|department|division)',
    ]
    
    # Try each pattern on the original case text
    for pattern in patterns:
        matches = re.findall(pattern, job_description, re.IGNORECASE)
        if matches:
            company_name = matches[0].strip()
            # Clean up the company name
            company_name = re.sub(r'[^\w\s&,.-]', '', company_name)
            company_name = company_name.strip()
            if len(company_name) > 2 and len(company_name) < 50:
                # Replace spaces and special characters for filename
                clean_name = re.sub(r'[^\w]', '-', company_name)
                clean_name = re.sub(r'-+', '-', clean_name).strip('-')
                return clean_name.lower()
    
    # Fallback: look for capitalized words at the beginning
    lines = job_description.split('\n')
    for line in lines[:5]:  # Check first 5 lines
        words = line.split()
        for i, word in enumerate(words):
            if word[0].isupper() and len(word) > 2 and i < 10:
                # Check if next 1-2 words are also capitalized (could be company name)
                company_parts = [word]
                for j in range(i+1, min(i+3, len(words))):
                    next_word = words[j]
                    if next_word[0].isupper() and len(next_word) > 1:
                        company_parts.append(next_word)
                    else:
                        break
                
                if len(company_parts) >= 1:
                    company_name = ' '.join(company_parts)
                    if len(company_name) < 50:
                        clean_name = re.sub(r'[^\w]', '-', company_name)
                        clean_name = re.sub(r'-+', '-', clean_name).strip('-')
                        return clean_name.lower()
    
    return "company"


def generate_pdf(content, user_id):
    """Generate PDF from text content."""
    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Create custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        body_style = ParagraphStyle(
            'CustomBody',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=12,
            leftIndent=20,
            rightIndent=20,
            leading=14
        )
        
        # Build story
        story = []
        story.append(Paragraph("Cover Letter", title_style))
        story.append(Spacer(1, 20))
        
        # Split content into paragraphs and add them
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), body_style))
                story.append(Spacer(1, 12))
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%B %d, %Y")
        story.append(Spacer(1, 20))
        story.append(Paragraph(f"Generated on: {timestamp}", styles['Normal']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        return None


def clear_user_session():
    """Clear current user session and data."""
    if 'user_id' in st.session_state:
        user_id = st.session_state.user_id
        user_persist_dir, user_uploads_dir = get_user_directories(user_id)
        
        # Remove user data directories
        try:
            if os.path.exists(user_persist_dir):
                shutil.rmtree(user_persist_dir)
            if os.path.exists(user_uploads_dir):
                shutil.rmtree(user_uploads_dir)
            logging.info(f"Cleared data for user {user_id}")
        except Exception as e:
            logging.error(f"Error clearing user data: {str(e)}")
    
    # Clear session state
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    st.rerun()


def main():
    # Initialize usage tracking database
    init_usage_db()
    
    # Check authentication first
    if not check_authentication():
        if not show_authentication_page():
            return
    
    # Add logout option to sidebar
    with st.sidebar:
        st.markdown("---")
        user_info = st.session_state.get('user_info', {})
        user_name = user_info.get('name', st.session_state.get('user_email', 'User'))
        st.success(f"👤 Welcome, {user_name}")
        
        # Admin dashboard access
        user_email = st.session_state.get('user_email', '')
        admin_emails = ['admin@company.com', 'tsztkwok@gmail.com']  # Add your admin emails here
        if user_email in admin_emails:
            st.markdown("---")
            if st.button("📊 Admin Dashboard"):
                st.session_state.show_admin = True
                st.rerun()
        
        if st.button("🚪 Logout"):
            logout_user()
            st.rerun()
    
    # Show admin dashboard if requested
    if st.session_state.get('show_admin', False):
        show_admin_dashboard()
        if st.button("🔙 Back to Main App"):
            st.session_state.show_admin = False
            st.rerun()
        return
    
    st.title("🎯 AI Cover Letter Assistant")
    st.markdown("*Invitation-only access • Secure & Personalized*")
    
    # Initialize user session
    initialize_user_session()
    
    # Check if we have an email but no preferences loaded (e.g., after page refresh)
    if (hasattr(st.session_state, 'extracted_email') and 
        st.session_state.extracted_email and 
        not hasattr(st.session_state, 'user_preferences')):
        try:
            logging.info(f"Reloading preferences for existing user: {st.session_state.extracted_email}")
            preferences = load_user_preferences(st.session_state.extracted_email)
            st.session_state.user_preferences = preferences
            st.session_state.permanent_user_id = st.session_state.extracted_email
        except Exception as e:
            logging.error(f"Error reloading user preferences: {e}")
    
    # Sidebar with session info
    with st.sidebar:
        st.header("Session Info")
        st.write(f"**Session ID:** {st.session_state.user_id}")
        st.write(f"**Started:** {st.session_state.session_start.strftime('%H:%M:%S')}")
        
        if st.button("🗑️ Clear Session"):
            clear_user_session()
        
        # Daily Usage Stats
        st.write("---")
        daily_status = check_daily_cover_letter_limit(st.session_state.user_id)
        st.header("📊 Daily Usage")
        
        # Usage progress bar
        usage_percentage = (daily_status['used_today'] / daily_status['daily_limit']) * 100
        st.progress(usage_percentage / 100)
        st.write(f"**{daily_status['used_today']}/{daily_status['daily_limit']}** cover letters used today")
        
        if daily_status['remaining'] > 0:
            st.success(f"✅ {daily_status['remaining']} generations remaining")
        else:
            st.error("🚫 Daily limit reached")
            st.caption(f"Resets at midnight")
        
        # Admin override (if user is in admin list)
        user_email = getattr(st.session_state, 'extracted_email', None)
        if user_email and user_email in get_admin_users():
            st.write("---")
            with st.expander("🔧 Admin Override", expanded=False):
                if st.button("🔓 Reset My Daily Limit"):
                    if reset_user_daily_limit(st.session_state.user_id):
                        st.success("✅ Daily limit reset!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to reset limit")
        
        # User Preferences Dashboard
        user_email = getattr(st.session_state, 'extracted_email', None)
        
        # Debug information
        st.write("---")
        st.write("**Debug Info:**")
        st.write(f"Email extracted: {user_email}")
        st.write(f"Has preferences: {hasattr(st.session_state, 'user_preferences')}")
        if hasattr(st.session_state, 'user_preferences'):
            st.write(f"Usage count: {st.session_state.user_preferences.get('usage_count', 0)}")
        
        if user_email and hasattr(st.session_state, 'user_preferences'):
            with st.expander("📊 Your Learning Dashboard", expanded=False):
                prefs = st.session_state.user_preferences
                st.write(f"**Email:** {user_email}")
                st.write(f"**Sessions:** {prefs['usage_count']}")
                st.write(f"**Last Updated:** {prefs.get('last_updated', 'N/A')[:10]}")
                
                if prefs["preferred_highlights"]:
                    st.write("**Frequent Strengths:**")
                    for highlight in prefs["preferred_highlights"][-5:]:
                        st.write(f"• {highlight}")
                
                if prefs["job_application_history"]:
                    st.write(f"**Recent Applications:** {len(prefs['job_application_history'])}")
                
                if st.button("🧹 Reset Learning Data"):
                    try:
                        # Reset preferences but keep the email
                        new_prefs = load_user_preferences(user_email)
                        new_prefs["usage_count"] = 0
                        save_user_preferences(user_email, new_prefs)
                        st.session_state.user_preferences = new_prefs
                        st.success("Learning data reset successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error resetting data: {e}")
        
        st.write("---")
        st.write("**How to use:**")
        st.write("1. Upload your resume (PDF)")
        st.write("2. Enter job description")
        st.write("3. Add specific strengths (optional)")
        st.write("4. Generate cover letter")
        st.write("5. Edit and save for learning")
    
    # Step 1: File Upload
    st.header("Step 1: Upload Your Resume")
    
    uploaded_file = st.file_uploader(
        "Choose your resume file", 
        type=['pdf'],
        help="Upload your resume in PDF format. This will be processed and stored securely for your session only."
    )
    
    # Check if user already has resume data
    has_existing_resume = check_user_has_resume_data(st.session_state.user_id)
    
    if has_existing_resume and uploaded_file is None:
        st.success("✅ Resume already processed!")
        st.session_state.vector_db_ready = True
    elif uploaded_file is not None:
        if not st.session_state.uploaded_file_processed:
            with st.spinner("Processing your resume..."):
                try:
                    # Save uploaded file
                    file_path = save_uploaded_file(uploaded_file, st.session_state.user_id)
                    
                    # Create vector database
                    vector_db = load_user_vector_db(st.session_state.user_id, file_path)
                    if vector_db is not None:
                        st.session_state.uploaded_file_processed = True
                        st.session_state.vector_db_ready = True
                        st.success("✅ Resume processed successfully!")
                        # Trigger rerun to show Step 2
                        st.rerun()
                    else:
                        st.error("❌ Failed to process resume.")
                except Exception as e:
                    st.error(f"❌ Error processing resume: {str(e)}")
        else:
            st.success("✅ Resume already processed!")
    else:
        # No existing resume and no uploaded file
        if not has_existing_resume:
            st.session_state.vector_db_ready = False
            st.info("📄 Please upload your resume above to get started with cover letter generation.")
    
    # Step 2: Job Description and Cover Letter Generation
    if st.session_state.vector_db_ready:
        st.header("Step 2: Generate Cover Letter")
        
        # Show user preferences info if available
        user_email = getattr(st.session_state, 'extracted_email', None)
        if user_email and hasattr(st.session_state, 'user_preferences'):
            prefs = st.session_state.user_preferences
            if prefs["preferred_highlights"]:
                with st.expander("💡 Your Previously Used Strengths", expanded=False):
                    st.write("Based on your history, you often highlight:")
                    for highlight in prefs["preferred_highlights"][-5:]:  # Show last 5
                        st.write(f"• {highlight}")
        
        # Job description input
        user_input = st.text_area(
            "Copy and paste the job description:", 
            height=400,
            help="Paste the complete job description here. The system will match it against your resume."
        )
        
        # User strengths input with personalized suggestions
        placeholder_text = ""
        if user_email and hasattr(st.session_state, 'user_preferences'):
            prefs = st.session_state.user_preferences
            if prefs["preferred_highlights"]:
                placeholder_text = f"e.g., {', '.join(prefs['preferred_highlights'][-3:])}"
        
        user_strengths = st.text_area(
            "Enter specific strengths/skills you want to highlight (optional):", 
            height=150,
            placeholder=placeholder_text,
            help="Enter any specific strengths, skills, or experiences you want to emphasize in your cover letter. These will take priority over automatically detected strengths."
        )
        
        # Store current values in session state for learning
        if user_input:
            st.session_state.current_job_description = user_input
        if user_strengths:
            st.session_state.current_user_strengths = user_strengths
        
        if user_input:
            # Input validation
            if LLM_GUARD_AVAILABLE and input_scanners:
                try:
                    sanitized_prompt, results_valid, results_score = scan_prompt(input_scanners, user_input)
                    if any(not result for result in results_valid.values()):
                        st.warning("⚠️ Input validation issue detected. Please review your job description.")
                        st.write(f"Validation scores: {results_score}")
                        return
                except Exception as e:
                    st.warning(f"⚠️ Security scanning temporarily unavailable: {str(e)}")
                    # Continue with basic validation
            
            # Basic input sanitization (always performed)
            sanitized_input = sanitize_user_input(user_input, max_length=10000)
            if len(sanitized_input) != len(user_input):
                st.warning("⚠️ Input has been sanitized for security.")
            
            # Check daily usage limit
            daily_status = check_daily_cover_letter_limit(st.session_state.user_id)
            
            # Display usage information
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Used Today", daily_status['used_today'])
            with col2:
                st.metric("📈 Remaining", daily_status['remaining'])
            with col3:
                st.metric("🎯 Daily Limit", daily_status['daily_limit'])
            
            if daily_status['remaining'] == 0:
                st.error("🚫 Daily limit reached! You've generated your maximum of 5 cover letters today.")
                st.info(f"⏰ Your limit resets at midnight. Next reset: {daily_status['reset_time'][:10]}")
                return
            
            # Generate cover letter
            if st.button("🚀 Generate Cover Letter", type="primary"):
                with st.spinner("Generating your personalized cover letter..."):
                    try:
                        # Initialize the language model
                        # Ollama (local deployment)
                        # llm = ChatOllama(model=MODEL_NAME)
                        
                        # OpenAI (cloud deployment)
                        llm = ChatOpenAI(model=MODEL_NAME, temperature=0.7)

                        # Load the user's vector database
                        vector_db = load_user_vector_db(st.session_state.user_id)
                        if vector_db is None:
                            st.error("❌ Failed to load your resume data.")
                            st.info("💡 Please try uploading your resume again in Step 1 above.")
                            st.info("🔍 If the issue persists, check the browser console for detailed error messages.")
                            return

                        # Create the retriever
                        retriever = create_retriever(vector_db, llm)

                        # Get user email for personalization
                        user_email = getattr(st.session_state, 'extracted_email', None)
                        
                        # Create the chain with personalization
                        chain = create_chain(retriever, llm, user_strengths, user_email)

                        # Extract company name and job title for tracking
                        company_name = extract_company_name(job_description) if job_description else None
                        job_title_pattern = r'(?:job title|position|role):\s*([^\n\r]+)|([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:Engineer|Developer|Manager|Analyst|Specialist|Director|Coordinator)))'
                        job_title_match = re.search(job_title_pattern, job_description, re.IGNORECASE) if job_description else None
                        job_title = job_title_match.group(1) or job_title_match.group(2) if job_title_match else None
                        
                        # Measure processing time
                        start_time = datetime.now()
                        
                        # Get the response
                        response = chain.invoke(input=user_input)

                        # Calculate processing time
                        processing_time = (datetime.now() - start_time).total_seconds()

                        # Clean the response to remove AI artifacts like <think>...</think>
                        cleaned_response = clean_ai_response(response)
                        
                        # Log the usage
                        cover_letter_length = len(cleaned_response) if cleaned_response else 0
                        log_cover_letter_generation(
                            user_email=st.session_state.get('user_email', 'unknown'),
                            user_id=st.session_state.user_id,
                            company_name=company_name,
                            job_title=job_title,
                            cover_letter_length=cover_letter_length,
                            processing_time=processing_time,
                            success=True
                        )
                        
                        # Store the cleaned cover letter in session state
                        st.session_state.generated_cover_letter = cleaned_response
                        st.session_state.original_cover_letter = cleaned_response  # Store original for learning
                        
                        # Record the generation for daily usage tracking
                        if record_cover_letter_generation(st.session_state.user_id):
                            # Update the daily status display
                            updated_status = check_daily_cover_letter_limit(st.session_state.user_id)
                            st.success(f"✅ Cover letter generated! You have {updated_status['remaining']} generations remaining today.")
                        
                        # Show personalization info if available
                        if user_email and hasattr(st.session_state, 'user_preferences'):
                            prefs = st.session_state.user_preferences
                            if prefs["usage_count"] > 0:
                                st.info(f"✨ This cover letter was personalized based on patterns from your {prefs['usage_count']} previous applications!")
                        
                    except Exception as e:
                        # Log the failed generation attempt
                        log_cover_letter_generation(
                            user_email=st.session_state.get('user_email', 'unknown'),
                            user_id=st.session_state.user_id,
                            company_name=None,
                            job_title=None,
                            cover_letter_length=0,
                            processing_time=0,
                            success=False,
                            error_message=str(e)
                        )
                        
                        st.error(f"❌ An error occurred: {str(e)}")
                        logging.error(f"Error generating cover letter for user {st.session_state.user_id}: {str(e)}")
    
    # Display and edit cover letter if one has been generated
    if hasattr(st.session_state, 'generated_cover_letter') and st.session_state.generated_cover_letter:
        st.header("📄 Your Generated Cover Letter")
        st.markdown("---")
        
        # Editable text area with the generated cover letter
        edited_cover_letter = st.text_area(
            "Edit your cover letter:",
            value=st.session_state.generated_cover_letter,
            height=400,
            help="You can edit the generated cover letter here. Make any changes you'd like before downloading."
        )
        
        # Save button with learning capability
        if st.button("💾 Save Changes", type="primary"):
            st.session_state.generated_cover_letter = edited_cover_letter
            
            # Learn from user preferences if email is available
            user_email = getattr(st.session_state, 'extracted_email', None)
            if user_email:
                try:
                    # Get the original letter and current highlights for learning
                    original_letter = getattr(st.session_state, 'original_cover_letter', '')
                    current_highlights = getattr(st.session_state, 'current_user_strengths', [])
                    if isinstance(current_highlights, str):
                        current_highlights = [s.strip() for s in current_highlights.split(',') if s.strip()]
                    
                    # Get job description for context
                    job_description = getattr(st.session_state, 'current_job_description', '')
                    
                    # Update user preferences with current session data
                    updated_preferences = update_user_preferences_with_session_data(
                        user_email, 
                        current_highlights, 
                        original_letter, 
                        edited_cover_letter, 
                        job_description
                    )
                    
                    # Update session state
                    st.session_state.user_preferences = updated_preferences
                    
                    # Show learning feedback
                    if original_letter != edited_cover_letter:
                        st.info("🧠 Great! I've learned from your edits to improve future cover letters.")
                    
                except Exception as e:
                    logging.error(f"Error updating user preferences: {e}")
            
            st.success("✅ Cover letter saved successfully!")
            st.rerun()
        
        # Update session state with edited version
        st.session_state.final_cover_letter = edited_cover_letter
        
        # Download buttons
        col1, col2 = st.columns(2)
        
        # Extract company name for filename
        company_name = "company"
        if hasattr(st.session_state, 'current_job_description') and st.session_state.current_job_description:
            company_name = extract_company_name(st.session_state.current_job_description)
        
        with col1:
            # Text download
            st.download_button(
                label="📄 Download as Text",
                data=edited_cover_letter,
                file_name=f"cover-letter-{company_name}.txt",
                mime="text/plain"
            )
        
        with col2:
            # PDF download
            pdf_data = generate_pdf(edited_cover_letter, st.session_state.user_id)
            if pdf_data:
                st.download_button(
                    label="📁 Download as PDF",
                    data=pdf_data,
                    file_name=f"cover-letter-{company_name}.pdf",
                    mime="application/pdf"
                )
            else:
                st.error("❌ Failed to generate PDF")
        
        # Clear cover letter button
        if st.button("🗑️ Generate New Cover Letter"):
            if 'generated_cover_letter' in st.session_state:
                del st.session_state.generated_cover_letter
            if 'final_cover_letter' in st.session_state:
                del st.session_state.final_cover_letter
            st.rerun()
    
    # Instructions
    if st.session_state.vector_db_ready:
        if not user_input:
            st.info("👆 Please enter the job description to generate your cover letter.")
    # Note: Upload message is already shown in Step 1 section above


if __name__ == "__main__":
    main()