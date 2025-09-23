# 🚀 OpenAI Deployment Guide

This guide covers deploying your AI Cover Letter Assistant to Streamlit Community Cloud using OpenAI's API.

## 📋 Prerequisites

1. **OpenAI API Account**
   - Sign up at [platform.openai.com](https://platform.openai.com)
   - Add billing information (required for API access)
   - Generate an API key from the API Keys section

2. **GitHub Repository**
   - Your code should be in a public or private GitHub repository
   - Ensure all files are committed and pushed

## 🔑 OpenAI API Setup

### Step 1: Get Your API Key

1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Click "Create new secret key"
3. Give it a name (e.g., "Streamlit Cover Letter App")
4. Copy the API key immediately (you won't see it again)

### Step 2: Cost Estimation

The app uses:
- **gpt-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **text-embedding-3-small**: ~$0.02 per 1M tokens

Typical usage per cover letter:
- Resume processing: ~$0.001-0.005
- Cover letter generation: ~$0.01-0.05
- **Total per cover letter: ~$0.02-0.10**

For 50 cover letters/month: ~$1-5/month

## 🌐 Streamlit Community Cloud Deployment

### Step 1: Create Streamlit App

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Connect your GitHub repository
4. Set:
   - **Repository**: your-username/cover-letter-assistant
   - **Branch**: main
   - **Main file path**: app.py
   - **App URL**: choose a custom subdomain

### Step 2: Configure Secrets

In your Streamlit app settings, add these secrets:

```toml
[auth]
admin_password = "your-secure-admin-password"
invitation_secret = "your-long-random-secret-key-min-32-chars"

[openai]
api_key = "sk-your-openai-api-key-here"

[security]
session_timeout_hours = 24
max_login_attempts = 3

[invited_users]
"your.email@example.com" = "Your Name"
"colleague@company.com" = "Colleague Name"
```

### Step 3: Deploy

1. Click "Deploy!" 
2. Wait for the build to complete
3. Your app will be available at: `https://your-app-name.streamlit.app`

## 🧪 Testing Your Deployment

### Step 1: Basic Functionality

1. **Access the app** at your Streamlit URL
2. **Enter an invited email** address
3. **Upload a test PDF** resume
4. **Paste a job description**
5. **Generate a cover letter**

### Step 2: Verify Features

- [ ] Authentication works with invited emails
- [ ] File upload accepts PDF files
- [ ] Vector database creates successfully
- [ ] Cover letter generation works
- [ ] PDF download functions properly
- [ ] User preferences are saved
- [ ] Admin dashboard is accessible

## 🔒 Security Best Practices

### API Key Security

- **Never commit API keys** to your repository
- **Use Streamlit secrets** for production deployment
- **Rotate API keys** periodically
- **Monitor API usage** on OpenAI dashboard

### Access Control

- **Keep invitation list updated** - remove ex-employees
- **Use strong admin passwords** - consider a password manager
- **Monitor authentication logs** - check for suspicious activity
- **Set session timeouts** appropriately for your organization

### Rate Limiting

The app includes built-in rate limiting:
- 5 authentication attempts per 15 minutes
- File upload validation
- User session management

## 📊 Monitoring and Maintenance

### OpenAI Usage Monitoring

1. Check [OpenAI Usage Dashboard](https://platform.openai.com/usage)
2. Set up billing alerts
3. Monitor for unusual usage spikes

### App Health Monitoring

1. **Streamlit Cloud Dashboard**: Monitor app status and logs
2. **User Feedback**: Collect feedback on cover letter quality
3. **Performance**: Monitor response times and errors

### Regular Maintenance

- **Weekly**: Check user feedback and app logs
- **Monthly**: Review OpenAI costs and usage patterns
- **Quarterly**: Update invited users list
- **As needed**: Update model versions or prompts

## 🔧 Troubleshooting

### Common Issues

**"OpenAI API key not found"**
```
Solution: Check secrets.toml configuration in Streamlit app settings
```

**"Rate limit exceeded"**
```
Solution: Wait or upgrade your OpenAI plan
```

**"Token limit exceeded"**
```
Solution: Reduce resume/job description length or update prompts
```

**"User not invited"**
```
Solution: Add email to [invited_users] section in secrets
```

### Cost Management

**Unexpected high costs:**
1. Check OpenAI usage dashboard
2. Look for long prompts or frequent requests
3. Consider switching to gpt-3.5-turbo for cost savings
4. Implement additional rate limiting if needed

**To reduce costs:**
- Use shorter, more focused prompts
- Cache embeddings when possible
- Set monthly spending limits on OpenAI

## 🔄 Switching Between Local and Cloud

### For Local Development (Ollama)

1. Uncomment Ollama imports in `app.py`
2. Comment out OpenAI imports
3. Update model constants to use Ollama models
4. Run `ollama serve` locally

### For Production (OpenAI)

1. Use the current OpenAI configuration
2. Ensure API key is set in secrets
3. Deploy to Streamlit Community Cloud

## 📞 Support

### OpenAI Issues
- [OpenAI Help Center](https://help.openai.com)
- [OpenAI Community](https://community.openai.com)
- Check [OpenAI Status](https://status.openai.com)

### Streamlit Issues
- [Streamlit Documentation](https://docs.streamlit.io)
- [Streamlit Community](https://discuss.streamlit.io)
- [Streamlit GitHub](https://github.com/streamlit/streamlit)

### App-Specific Issues
- Check app logs in Streamlit Cloud dashboard
- Review security audit logs
- Test with different browsers/devices

---

**You're ready for production! 🎉 Your AI Cover Letter Assistant is now deployed with enterprise-grade security and OpenAI's powerful models.**