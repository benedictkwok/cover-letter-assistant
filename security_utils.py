"""
Security utilities for the invitation-only cover letter assistant.
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Security audit log file
AUDIT_LOG_FILE = "./security_audit.log"

def setup_security_logging():
    """Set up security-specific logging."""
    security_logger = logging.getLogger('security')
    security_logger.setLevel(logging.INFO)
    
    # Create file handler for security events
    handler = logging.FileHandler(AUDIT_LOG_FILE)
    formatter = logging.Formatter(
        '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    security_logger.addHandler(handler)
    
    return security_logger

def log_security_event(event_type: str, user_email: str, details: Dict = None):
    """Log security-related events for audit purposes."""
    security_logger = setup_security_logging()
    
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "event_type": event_type,
        "user_email": user_email,
        "details": details or {}
    }
    
    security_logger.info(json.dumps(log_entry))

def log_authentication_attempt(email: str, success: bool, ip_address: str = None):
    """Log authentication attempts."""
    event_type = "AUTH_SUCCESS" if success else "AUTH_FAILURE"
    details = {"ip_address": ip_address} if ip_address else {}
    log_security_event(event_type, email, details)

def log_file_access(user_email: str, file_path: str, action: str):
    """Log file access events."""
    log_security_event("FILE_ACCESS", user_email, {
        "file_path": file_path,
        "action": action
    })

def log_directory_access(user_email: str, directory: str):
    """Log directory access events."""
    log_security_event("DIRECTORY_ACCESS", user_email, {
        "directory": directory
    })

def validate_file_type(filename: str, allowed_extensions: List[str] = None) -> bool:
    """Validate uploaded file type."""
    if allowed_extensions is None:
        allowed_extensions = ['.pdf', '.doc', '.docx', '.txt']
    
    file_ext = os.path.splitext(filename.lower())[1]
    return file_ext in allowed_extensions

def sanitize_user_input(user_input: str, max_length: int = 10000) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not user_input:
        return ""
    
    # Limit length
    sanitized = user_input[:max_length]
    
    # Remove potential script tags and other dangerous content
    dangerous_patterns = [
        '<script', '</script>', 'javascript:', 'data:',
        'vbscript:', 'onload=', 'onerror=', 'onclick='
    ]
    
    for pattern in dangerous_patterns:
        sanitized = sanitized.replace(pattern, '')
    
    return sanitized.strip()

def check_rate_limit(user_email: str, action: str, max_requests: int = 10, 
                    time_window_minutes: int = 60) -> bool:
    """Simple rate limiting implementation."""
    rate_limit_file = f"./rate_limits_{action}.json"
    current_time = datetime.now()
    
    # Load existing rate limit data
    rate_data = {}
    if os.path.exists(rate_limit_file):
        try:
            with open(rate_limit_file, 'r') as f:
                rate_data = json.load(f)
        except Exception:
            rate_data = {}
    
    # Clean old entries
    user_requests = rate_data.get(user_email, [])
    cutoff_time = current_time.timestamp() - (time_window_minutes * 60)
    user_requests = [req for req in user_requests if req > cutoff_time]
    
    # Check if limit exceeded
    if len(user_requests) >= max_requests:
        log_security_event("RATE_LIMIT_EXCEEDED", user_email, {
            "action": action,
            "request_count": len(user_requests),
            "max_allowed": max_requests
        })
        return False
    
    # Add current request
    user_requests.append(current_time.timestamp())
    rate_data[user_email] = user_requests
    
    # Save updated rate limit data
    try:
        with open(rate_limit_file, 'w') as f:
            json.dump(rate_data, f)
    except Exception as e:
        logging.error(f"Error saving rate limit data: {e}")
    
    return True

def get_security_stats() -> Dict:
    """Get security statistics for monitoring."""
    stats = {
        "total_auth_attempts": 0,
        "successful_logins": 0,
        "failed_logins": 0,
        "file_accesses": 0,
        "rate_limit_violations": 0
    }
    
    if not os.path.exists(AUDIT_LOG_FILE):
        return stats
    
    try:
        with open(AUDIT_LOG_FILE, 'r') as f:
            for line in f:
                if "AUTH_SUCCESS" in line:
                    stats["successful_logins"] += 1
                    stats["total_auth_attempts"] += 1
                elif "AUTH_FAILURE" in line:
                    stats["failed_logins"] += 1
                    stats["total_auth_attempts"] += 1
                elif "FILE_ACCESS" in line:
                    stats["file_accesses"] += 1
                elif "RATE_LIMIT_EXCEEDED" in line:
                    stats["rate_limit_violations"] += 1
    except Exception as e:
        logging.error(f"Error reading security audit log: {e}")
    
    return stats

def check_daily_cover_letter_limit(user_email: str, daily_limit: int = 5) -> Dict:
    """
    Check if user has exceeded their daily cover letter generation limit.
    
    Args:
        user_email: User's email address
        daily_limit: Maximum cover letters per day (default: 5)
    
    Returns:
        Dict with keys: 'allowed', 'remaining', 'used_today', 'reset_time'
    """
    usage_file = "./daily_usage.json"
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Load existing usage data
    usage_data = {}
    if os.path.exists(usage_file):
        try:
            with open(usage_file, 'r') as f:
                usage_data = json.load(f)
        except Exception:
            usage_data = {}
    
    # Clean old entries (keep only today's data)
    if current_date not in usage_data:
        usage_data = {current_date: {}}
    else:
        # Remove entries from previous days
        usage_data = {current_date: usage_data.get(current_date, {})}
    
    # Get user's usage for today
    today_usage = usage_data[current_date].get(user_email, 0)
    
    # Check if limit exceeded
    allowed = today_usage < daily_limit
    remaining = max(0, daily_limit - today_usage)
    
    # Calculate reset time (midnight)
    from datetime import date, timedelta
    tomorrow = date.today() + timedelta(days=1)
    reset_time = datetime.combine(tomorrow, datetime.min.time())
    
    return {
        'allowed': allowed,
        'remaining': remaining,
        'used_today': today_usage,
        'reset_time': reset_time.isoformat(),
        'daily_limit': daily_limit
    }

def record_cover_letter_generation(user_email: str) -> bool:
    """
    Record a cover letter generation for the user.
    
    Args:
        user_email: User's email address
    
    Returns:
        bool: True if recorded successfully, False otherwise
    """
    usage_file = "./daily_usage.json"
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Load existing usage data
    usage_data = {}
    if os.path.exists(usage_file):
        try:
            with open(usage_file, 'r') as f:
                usage_data = json.load(f)
        except Exception:
            usage_data = {}
    
    # Initialize today's data if needed
    if current_date not in usage_data:
        usage_data[current_date] = {}
    
    # Increment user's count
    current_count = usage_data[current_date].get(user_email, 0)
    usage_data[current_date][user_email] = current_count + 1
    
    # Save updated usage data
    try:
        with open(usage_file, 'w') as f:
            json.dump(usage_data, f, indent=2)
        
        # Log the generation event
        log_security_event("COVER_LETTER_GENERATED", user_email, {
            "daily_count": usage_data[current_date][user_email],
            "date": current_date
        })
        
        return True
    except Exception as e:
        logging.error(f"Error saving daily usage data: {e}")
        return False

def get_daily_usage_stats() -> Dict:
    """Get daily usage statistics for all users."""
    usage_file = "./daily_usage.json"
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    if not os.path.exists(usage_file):
        return {"total_today": 0, "users_today": 0, "usage_by_user": {}}
    
    try:
        with open(usage_file, 'r') as f:
            usage_data = json.load(f)
        
        today_data = usage_data.get(current_date, {})
        
        return {
            "total_today": sum(today_data.values()),
            "users_today": len(today_data),
            "usage_by_user": today_data,
            "date": current_date
        }
    except Exception as e:
        logging.error(f"Error reading daily usage stats: {e}")
        return {"total_today": 0, "users_today": 0, "usage_by_user": {}}

def get_admin_users() -> List[str]:
    """Get list of admin user emails."""
    try:
        # Try to get from Streamlit secrets first
        import streamlit as st
        if hasattr(st, 'secrets') and 'admin_users' in st.secrets:
            return list(st.secrets['admin_users'])
    except Exception:
        pass
    
    # Default admin users (you can modify this list)
    default_admins = []
    
    # Try to read from invited users and find admin level users
    try:
        if os.path.exists("./invited_users.json"):
            with open("./invited_users.json", 'r') as f:
                users_data = json.load(f)
                admin_emails = [
                    email for email, data in users_data.get("invited_users", {}).items()
                    if isinstance(data, dict) and data.get("access_level") == "admin"
                ]
                return admin_emails
    except Exception as e:
        logging.error(f"Error reading admin users: {e}")
    
    return default_admins

def reset_user_daily_limit(user_email: str) -> bool:
    """Reset a user's daily cover letter limit (admin function)."""
    usage_file = "./daily_usage.json"
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Load existing usage data
        usage_data = {}
        if os.path.exists(usage_file):
            with open(usage_file, 'r') as f:
                usage_data = json.load(f)
        
        # Reset user's count for today
        if current_date in usage_data:
            if user_email in usage_data[current_date]:
                del usage_data[current_date][user_email]
        
        # Save updated data
        with open(usage_file, 'w') as f:
            json.dump(usage_data, f, indent=2)
        
        # Log the admin action
        log_security_event("ADMIN_LIMIT_RESET", user_email, {
            "date": current_date,
            "admin_action": True
        })
        
        return True
    except Exception as e:
        logging.error(f"Error resetting daily limit for {user_email}: {e}")
        return False