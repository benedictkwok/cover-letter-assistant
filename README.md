# 🎯 AI Cover Letter Assistant - Invitation Only

An intelligent, secure, and personalized cover letter generation system built with Streamlit. This standalone application features invitation-only access, user data isolation, and personalized AI assistance. **Now supports both local Ollama and cloud OpenAI deployment!**

## ✨ Key Features

- **📊 Admin Dashboard**: Web-based analytics dashboard with real-time usage monitoring
- **👤 User Data Isolation**: Each user's data is completely separated and secure
- **🧠 Personalized AI**: Learns from user preferences and writing patterns
- **📊 Analytics & Monitoring**: Comprehensive security logging and usage statistics
- **🔒 Enhanced Security**: Rate limiting, file validation, and audit trails
- **☁️ Cloud-Ready**: Supports both Ollama (local) and OpenAI (cloud) deployment
- **🔄 Flexible LLM Backend**: Easy switching between local and cloud AI models
- **⏱️ Daily Usage Limits**: Built-in 5 cover letters per day limit with admin override
- **💰 Cost Control**: Prevents excessive OpenAI API usage with automatic tracking
- **🔌 MCP Server**: Model Context Protocol server for privacy-focused analytics integration
- **🎯 Smart Company Detection**: LLM-powered company name extraction for accurate analytics
- **📈 VS Code Integration**: Direct analytics access through VS Code with MCP client interface

## 🚀 Quick Start

### Option 1: Cloud Deployment with OpenAI (Recommended for Production)

**Perfect for Streamlit Community Cloud deployment!**

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd cover-letter-assistant
   ```

2. **Get OpenAI API Key**:
   - Sign up at [platform.openai.com](https://platform.openai.com)
   - Create an API key
   - Estimated cost: ~$0.02-0.10 per cover letter

3. **Configure secrets**:
   ```toml
   # .streamlit/secrets.toml
   [openai]
   api_key = "your-openai-api-key"
   
   [invited_users]
   "your.email@example.com" = "Your Name"
   ```

4. **Deploy to Streamlit Cloud**:
   - See [DEPLOYMENT_OPENAI.md](DEPLOYMENT_OPENAI.md) for detailed instructions

### Option 2: Local Development with Ollama

**Great for local testing and development!**

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up Ollama**:
   ```bash
   # Install Ollama
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Pull required models
   ollama pull qwen3:8b
   ollama pull nomic-embed-text
   ```

3. **Switch to Ollama mode**:
   - In `app.py`, comment out OpenAI imports and uncomment Ollama imports
   - Update model constants to use Ollama models

4. **Configure invited users**:
   - Edit `invited_users.json` to add your email addresses

5. **Run locally**:
   ```bash
   streamlit run app.py
   ```

## 📁 Project Structure

```
cover-letter-assistant/
├── app.py                      # Main Streamlit application
├── security_utils.py           # Security utilities and logging
├── admin_dashboard.py          # Admin interface (optional)
├── invited_users.json          # User configuration
├── requirements.txt            # Python dependencies
├── DEPLOYMENT.md              # Detailed deployment guide
├── README.md                  # This file
├── .streamlit/
│   ├── config.toml            # App configuration
│   └── secrets.toml           # Secrets (local only - DO NOT COMMIT)
├── .gitignore                 # Git ignore rules
└── [Runtime directories created automatically]
    ├── chroma_db_multiuser/   # User vector databases
    ├── uploads/               # User file uploads
    ├── user_preferences/      # User preference files
    └── rate_limits_*.json     # Rate limiting data
```

## 🛡️ Security Features

### Access Control
- **Email Whitelist**: Only pre-approved emails can access the system
- **Session Management**: Secure tokens with automatic expiration
- **Rate Limiting**: Prevents abuse with configurable limits
- **Audit Logging**: All security events logged for monitoring

### Data Protection
- **User Isolation**: Each user's data stored in separate directories
- **File Validation**: Only approved file types accepted
- **Path Sanitization**: Prevents directory traversal attacks
- **Secure Authentication**: HMAC-based session tokens

### Daily Usage Limits
- **5 Cover Letters Per Day**: Automatic limit to control costs and prevent abuse
- **Real-time Tracking**: Shows remaining usage in sidebar
- **Midnight Reset**: Limits automatically reset at midnight
- **Admin Override**: Administrators can reset limits when needed
- **Usage Analytics**: Track daily usage across all users

### Authentication Flow
1. User enters email address
2. System validates against invitation list
3. Creates secure session token
4. Maps user to unique data directory
5. Loads personalized preferences

## 👥 User Management

### Adding New Users

**Method 1: Streamlit Secrets (Recommended for Production)**
```toml
[invited_users]
"user1@example.com" = "John Doe"
"user2@example.com" = "Jane Smith"
```

**Method 2: JSON Configuration File**
```json
{
  "invited_users": {
    "user1@example.com": {
      "name": "John Doe",
      "invited_date": "2025-01-15",
      "status": "active",
      "access_level": "user",
      "notes": "Team member"
    }
  }
}
```

**Method 3: Admin Dashboard (Optional)**
Deploy `admin_dashboard.py` separately for a web-based management interface.

### User Data Mapping
- **Email**: Primary identifier for user authentication
- **Directory**: Safe email format used for folder names
- **Preferences**: Stored in JSON files with user patterns
- **Vector Store**: Individual FAISS instance per user

## 🔧 Configuration

### Application Settings

Edit `invited_users.json`:
```json
{
  "app_settings": {
    "max_users": 50,
    "invitation_required": true,
    "allow_self_registration": false
  }
}
```

### Security Settings

Configure in `.streamlit/secrets.toml`:
```toml
[security]
session_timeout_hours = 24
max_login_attempts = 3

[auth]
invitation_secret = "your-long-random-secret"
admin_password = "your-admin-password"
```


## 📊 Admin Dashboard

The admin dashboard provides comprehensive analytics and system monitoring for authorized administrators.

### Accessing the Dashboard

1. **Log in** with an admin email (configured in `secrets.toml`)
2. **Look for "🔧 Admin Tools"** in the sidebar
3. **Click "📊 Admin Dashboard"** to view analytics

### Dashboard Features

**📈 Usage Statistics**
- Total users and cover letter generations
- Success rates and processing times
- Daily activity trends
- Average letter length and quality metrics

**🏢 Company Analytics**
- Most popular companies (extracted via LLM)
- Application success rates by company
- Industry trends and patterns

**⏰ Activity Monitoring**
- Recent user activity (last 24 hours)
- Peak usage hours and patterns
- System health indicators

**👥 User Management**
- Top active users (anonymized)
- Daily usage limits tracking
- User engagement metrics

### Admin Configuration

Configure admin access in your `secrets.toml`:

```toml
[admin]
admin_emails = ["your.email@example.com"]
super_admin = "your.email@example.com"
allow_analytics = true
allow_user_management = true
allow_system_controls = false
```

### Security Features

- **Access Control**: Only authorized emails can access dashboard, using Auth0 for social sign-in
- **Audit Logging**: All admin actions are logged
- **Data Privacy**: No personal data or resume content exposed
- **Aggregated Views**: All statistics are anonymized and aggregated

## 🔍 Monitoring & Logs

### Security Audit Log
- Location: `security_audit.log`
- Contains: Authentication attempts, file access, rate limit violations
- Format: JSON structured logs with timestamps

### Rate Limiting
- Authentication: 5 attempts per 15 minutes
- File uploads: 10 files per hour
- Configurable per action type

### User Analytics
- Session tracking per user
- Usage patterns and preferences
- Application history logging

## 🚨 Troubleshooting

### Common Issues

**"User not invited" errors**
- Check email spelling matches exactly in configuration
- Verify email is in `invited_users.json` or secrets
- Check for case sensitivity issues

**"Failed to process resume" errors**
- Ensure Ollama is running and accessible
- Check if required models are downloaded
- Verify PDF file is not corrupted

**Rate limiting errors**
- Wait for the time window to reset
- Check `rate_limits_*.json` files for current state
- Adjust limits in security configuration

**Data not persisting**
- Check file permissions in project directory
- Ensure sufficient disk space
- Verify write access to data directories

### Debug Mode

Set logging level for detailed debugging:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Health Check

Test your setup:
1. **Ollama Connection**: `curl http://localhost:11434/api/tags`
2. **Models Available**: `ollama list`
3. **File Permissions**: Check write access to project directory
4. **Configuration**: Validate JSON syntax in config files

## 🔐 Security Best Practices

1. **Strong Secrets**: Use long, random invitation secrets
2. **Regular Monitoring**: Check security audit logs
3. **User Reviews**: Periodically review invited user list
4. **Backup Strategy**: Backup user preferences and vector data
5. **Updates**: Keep dependencies updated
6. **Network Security**: Use HTTPS in production
7. **Access Control**: Limit admin dashboard access


## 🔌 MCP Server (Model Context Protocol)

The application includes a privacy-focused MCP server that provides analytics access through VS Code and other MCP clients.

### Features

- **Privacy-First Design**: No personal data or resume content exposed
- **Aggregated Analytics**: System-wide usage metrics and trends
- **VS Code Integration**: Direct access through VS Code MCP client
- **Real-time Monitoring**: Current system health and activity

### Available Tools

**📊 `get_usage_statistics`**
- Total users and generations
- Success rates and performance
- Daily activity trends
- Popular companies (aggregated)

**⚡ `get_recent_activity`**
- Last 24 hours activity
- Growth comparisons
- User engagement metrics

**🔋 `get_system_health`**
- System status indicators
- Performance benchmarks
- Uptime monitoring

### VS Code Integration

Use the included VS Code interface for direct analytics access:

```bash
# Get usage statistics
python vscode_mcp_interface.py stats

# Check recent activity
python vscode_mcp_interface.py recent

# Monitor system health
python vscode_mcp_interface.py health
```

### MCP Server Setup

1. **Install MCP requirements**:
   ```bash
   pip install -r mcp_requirements.txt
   ```

2. **Configure VS Code** (see `.vscode/settings.json`)

3. **Run MCP server**:
   ```bash
   python mcp_server.py
   ```

For detailed MCP setup instructions, see [MCP_README.md](MCP_README.md).

## 📖 API Documentation

### Core Functions

- `check_authentication()`: Validates user session
- `load_invited_users()`: Loads user whitelist
- `save_uploaded_file()`: Handles secure file uploads
- `load_user_vector_db()`: Manages user-specific vector databases
- `generate_personalized_prompt_additions()`: Creates personalized AI context

### Security Functions

- `log_authentication_attempt()`: Audit logging
- `check_rate_limit()`: Rate limiting enforcement
- `validate_file_type()`: File type validation
- `sanitize_user_input()`: Input sanitization

## 📞 Support

### Documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Detailed deployment guide
- Security audit logs for troubleshooting
- Error messages with specific guidance

### Common Commands

```bash
# Start application
streamlit run app.py

# Start admin dashboard
streamlit run admin_dashboard.py --server.port 8502

# Check Ollama status
ollama list

# View logs
tail -f security_audit.log

# Reset user data (careful!)
rm -rf chroma_db_multiuser/ uploads/ user_preferences/
```

## 📜 License

This project is intended for internal/invited use only. Modify the invitation system as needed for your specific requirements.

## 🚀 Deployment Checklist

- [ ] Set up GitHub repository
- [ ] Configure Streamlit Community Cloud
- [ ] Add secrets to Streamlit Cloud settings
- [ ] Set up Ollama server
- [ ] Configure invited users list
- [ ] Test authentication flow
- [ ] Verify file upload functionality
- [ ] Check security logging
- [ ] Test cover letter generation
- [ ] Monitor initial usage

## 🔄 Updates & Maintenance

### Regular Tasks
- Review security audit logs weekly
- Update invited users as needed
- Monitor disk usage for user data
- Check for dependency updates monthly
- Backup user preferences and data

### Version Updates
- Test changes in development environment
- Update requirements.txt if dependencies change
- Document configuration changes
- Notify users of significant updates

---

**Ready to deploy your secure, invitation-only AI Cover Letter Assistant!** 🎯
