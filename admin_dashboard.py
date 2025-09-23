"""
Admin interface for managing invited users in the Cover Letter Assistant.
This should be deployed separately from the main app for security.
"""

import streamlit as st
import json
import os
from datetime import datetime
from security_utils import get_security_stats
import pandas as pd

# Configuration
INVITED_USERS_FILE = "./invited_users.json"
ADMIN_PASSWORD = st.secrets.get("auth", {}).get("admin_password", "admin123")

def check_admin_auth():
    """Check if admin is authenticated."""
    if not st.session_state.get('admin_authenticated', False):
        st.title("🔐 Admin Access")
        password = st.text_input("Admin Password", type="password")
        if st.button("Login"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("Invalid password")
        return False
    return True

def load_invited_users():
    """Load invited users from JSON file."""
    if os.path.exists(INVITED_USERS_FILE):
        try:
            with open(INVITED_USERS_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            st.error(f"Error loading users: {e}")
    return {
        "invited_users": {},
        "admin_emails": [],
        "app_settings": {
            "max_users": 50,
            "invitation_required": True,
            "allow_self_registration": False
        }
    }

def save_invited_users(data):
    """Save invited users to JSON file."""
    try:
        with open(INVITED_USERS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving users: {e}")
        return False

def main():
    if not check_admin_auth():
        return
    
    st.title("👥 User Management Dashboard")
    st.markdown("---")
    
    # Add logout button
    if st.button("🚪 Logout", key="logout"):
        st.session_state.admin_authenticated = False
        st.rerun()
    
    # Load current data
    user_data = load_invited_users()
    invited_users = user_data.get("invited_users", {})
    
    # Tabs for different admin functions
    tab1, tab2, tab3, tab4 = st.tabs(["👤 Manage Users", "📊 Statistics", "⚙️ Settings", "🔍 Security Audit"])
    
    with tab1:
        st.header("Manage Invited Users")
        
        # Add new user
        st.subheader("➕ Add New User")
        col1, col2 = st.columns(2)
        with col1:
            new_email = st.text_input("Email Address")
        with col2:
            new_name = st.text_input("Full Name")
        
        if st.button("Add User"):
            if new_email and new_name:
                if new_email.lower() in [email.lower() for email in invited_users.keys()]:
                    st.error("User already exists!")
                else:
                    invited_users[new_email.lower()] = {
                        "name": new_name,
                        "invited_date": datetime.now().isoformat(),
                        "status": "active",
                        "access_level": "user",
                        "notes": f"Added by admin on {datetime.now().strftime('%Y-%m-%d')}"
                    }
                    user_data["invited_users"] = invited_users
                    if save_invited_users(user_data):
                        st.success(f"✅ Added user: {new_email}")
                        st.rerun()
            else:
                st.error("Please fill in both email and name")
        
        # Current users table
        st.subheader("📋 Current Invited Users")
        if invited_users:
            # Convert to DataFrame for display
            users_df = pd.DataFrame.from_dict(invited_users, orient='index')
            users_df.index.name = 'Email'
            users_df = users_df.reset_index()
            
            # Display editable table
            edited_df = st.data_editor(
                users_df,
                column_config={
                    "Email": st.column_config.TextColumn("Email", disabled=True),
                    "name": st.column_config.TextColumn("Name"),
                    "status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["active", "inactive", "suspended"]
                    ),
                    "access_level": st.column_config.SelectboxColumn(
                        "Access Level",
                        options=["user", "admin"]
                    ),
                    "notes": st.column_config.TextColumn("Notes")
                },
                num_rows="dynamic"
            )
            
            # Save changes
            if st.button("💾 Save Changes"):
                # Convert back to dictionary format
                updated_users = {}
                for _, row in edited_df.iterrows():
                    email = row['Email']
                    updated_users[email] = {
                        "name": row['name'],
                        "invited_date": invited_users.get(email, {}).get('invited_date', datetime.now().isoformat()),
                        "status": row['status'],
                        "access_level": row['access_level'],
                        "notes": row['notes']
                    }
                
                user_data["invited_users"] = updated_users
                if save_invited_users(user_data):
                    st.success("✅ Changes saved successfully!")
                    st.rerun()
        else:
            st.info("No invited users found. Add some users above.")
    
    with tab2:
        st.header("📊 Usage Statistics")
        
        # Basic stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Invited Users", len(invited_users))
        with col2:
            active_users = sum(1 for user in invited_users.values() if user.get('status') == 'active')
            st.metric("Active Users", active_users)
        with col3:
            admin_users = sum(1 for user in invited_users.values() if user.get('access_level') == 'admin')
            st.metric("Admin Users", admin_users)
        
        # Security statistics
        st.subheader("🔒 Security Statistics")
        try:
            security_stats = get_security_stats()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Auth Attempts", security_stats["total_auth_attempts"])
                st.metric("Successful Logins", security_stats["successful_logins"])
            with col2:
                st.metric("Failed Logins", security_stats["failed_logins"])
                st.metric("Rate Limit Violations", security_stats["rate_limit_violations"])
        except Exception as e:
            st.warning(f"Could not load security statistics: {e}")
        
        # User registration timeline
        st.subheader("📈 User Registration Timeline")
        if invited_users:
            registration_dates = []
            for user_info in invited_users.values():
                try:
                    reg_date = datetime.fromisoformat(user_info.get('invited_date', ''))
                    registration_dates.append(reg_date.date())
                except:
                    continue
            
            if registration_dates:
                date_counts = pd.Series(registration_dates).value_counts().sort_index()
                st.line_chart(date_counts)
    
    with tab3:
        st.header("⚙️ Application Settings")
        
        settings = user_data.get("app_settings", {})
        
        # Editable settings
        max_users = st.number_input("Maximum Users", value=settings.get("max_users", 50), min_value=1, max_value=1000)
        invitation_required = st.checkbox("Invitation Required", value=settings.get("invitation_required", True))
        allow_self_registration = st.checkbox("Allow Self Registration", value=settings.get("allow_self_registration", False))
        
        if st.button("💾 Save Settings"):
            user_data["app_settings"] = {
                "max_users": max_users,
                "invitation_required": invitation_required,
                "allow_self_registration": allow_self_registration
            }
            if save_invited_users(user_data):
                st.success("✅ Settings saved successfully!")
                st.rerun()
        
        st.markdown("---")
        st.subheader("🔧 Admin Emails")
        admin_emails = user_data.get("admin_emails", [])
        
        # Add admin email
        new_admin_email = st.text_input("Add Admin Email")
        if st.button("Add Admin"):
            if new_admin_email and new_admin_email not in admin_emails:
                admin_emails.append(new_admin_email)
                user_data["admin_emails"] = admin_emails
                if save_invited_users(user_data):
                    st.success(f"✅ Added admin: {new_admin_email}")
                    st.rerun()
        
        # Display current admin emails
        if admin_emails:
            for i, email in enumerate(admin_emails):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(email)
                with col2:
                    if st.button("🗑️", key=f"remove_admin_{i}"):
                        admin_emails.remove(email)
                        user_data["admin_emails"] = admin_emails
                        if save_invited_users(user_data):
                            st.rerun()
    
    with tab4:
        st.header("🔍 Security Audit Log")
        
        audit_log_file = "./security_audit.log"
        if os.path.exists(audit_log_file):
            try:
                with open(audit_log_file, 'r') as f:
                    log_lines = f.readlines()
                
                # Show last 50 log entries
                st.subheader("Recent Security Events")
                for line in log_lines[-50:]:
                    if line.strip():
                        # Parse and format log line
                        try:
                            parts = line.strip().split(' - ')
                            if len(parts) >= 4:
                                timestamp = parts[0]
                                event_type = parts[2]
                                details = ' - '.join(parts[3:])
                                
                                # Color code by event type
                                if "FAILURE" in event_type or "EXCEEDED" in event_type:
                                    st.error(f"🚨 {timestamp} - {event_type}: {details}")
                                elif "SUCCESS" in event_type:
                                    st.success(f"✅ {timestamp} - {event_type}: {details}")
                                else:
                                    st.info(f"ℹ️ {timestamp} - {event_type}: {details}")
                        except:
                            st.text(line.strip())
                
                # Clear log button
                if st.button("🗑️ Clear Audit Log"):
                    open(audit_log_file, 'w').close()
                    st.success("Audit log cleared")
                    st.rerun()
                    
            except Exception as e:
                st.error(f"Error reading audit log: {e}")
        else:
            st.info("No security audit log found. Log will be created when security events occur.")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Admin Dashboard",
        page_icon="👑",
        layout="wide"
    )
    main()