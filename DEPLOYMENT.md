# Streamlit Community Cloud Deployment Guide

## Overview
This is an invitation-only AI Cover Letter Assistant that provides personalized cover letter generation based on user resumes and job descriptions.

## Security Features
- ✅ Invitation-only access system
- ✅ Email-based user authentication
- ✅ Data isolation per user
- ✅ Session management with secure tokens
- ✅ Directory traversal protection
- ✅ Audit logging

## Deployment to Streamlit Community Cloud

### Prerequisites
1. GitHub account
2. Streamlit Community Cloud account
3. Ollama server accessible from the internet (for LLM inference)

### Step 1: Prepare Your Repository
1. Push this code to a GitHub repository
2. Ensure `requirements.txt` and `.streamlit/config.toml` are included
3. **Important**: Do NOT commit `.streamlit/secrets.toml` to GitHub

### Step 2: Configure Secrets on Streamlit Cloud
In your Streamlit app settings, add these secrets:

```toml
[auth]
admin_password = "your-secure-admin-password"
invitation_secret = "your-long-random-secret-key"

[security]
session_timeout_hours = 24
max_login_attempts = 3

[invited_users]
"user1@example.com" = "John Doe"
"user2@example.com" = "Jane Smith"
"admin@yourcompany.com" = "Admin User"
```

### Step 3: Environment Variables
Set these environment variables in Streamlit Cloud:
- `OLLAMA_BASE_URL`: URL to your Ollama server (e.g., "http://your-server:11434")

### Step 4: Invite Users
1. Add user emails to the `invited_users` section in secrets
2. Update the `invited_users.json` file for additional configuration
3. Users can only access with pre-approved email addresses

### Step 5: Deploy
1. Connect your GitHub repository to Streamlit Community Cloud
2. Select the main branch
3. Set the main file path: `cover-letter-multi-user.py`
4. Deploy the app

## Managing Invited Users

### Adding New Users
1. Go to your Streamlit app settings
2. Add their email to the `[invited_users]` section in secrets
3. Optionally update `invited_users.json` for additional metadata

### Removing Users
1. Remove their email from the secrets
2. Their data will remain isolated but they won't be able to log in

### User Data Location
Each user's data is stored in separate directories:
- Vector DB: `./chroma_db_multiuser/user_{email_safe}/`
- Uploads: `./uploads/user_{email_safe}/`
- Preferences: `./user_preferences/{email_safe}.json`

## Security Considerations

### What's Protected
- Only invited users can access the application
- Each user can only access their own data
- Session tokens expire automatically
- File uploads are sanitized
- Directory traversal attacks are prevented

### Regular Maintenance
- Review user access regularly
- Monitor application logs
- Update dependencies periodically
- Rotate secrets if needed

## Troubleshooting

### Common Issues
1. **Users can't log in**: Check if their email is in the invited_users secrets
2. **Data not persisting**: Ensure directories have write permissions
3. **Ollama connection issues**: Verify OLLAMA_BASE_URL is correct

### Logs
Check Streamlit Cloud logs for authentication attempts and errors.

## Production Recommendations

1. **Use a dedicated Ollama server**: Don't rely on local installations
2. **Regular backups**: Backup user data directories
3. **Monitor usage**: Track application performance and user activity
4. **SSL/TLS**: Ensure your Ollama server uses HTTPS
5. **Rate limiting**: Consider implementing rate limits for API calls

## Support
For issues with the invitation system or deployment, check the application logs and ensure all secrets are properly configured.