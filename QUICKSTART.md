# 🚀 Quick Start Guide

Get your AI Cover Letter Assistant up and running in minutes!

## Option 1: Local Development (Recommended for Testing)

### Step 1: Setup
```bash
# Clone the repository (replace with your repo URL)
git clone <your-repo-url>
cd cover-letter-assistant

# Run the setup script
./setup.sh

# Or manually install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Users
Edit `invited_users.json` to add your email:
```json
{
  "invited_users": {
    "your.email@example.com": {
      "name": "Your Name",
      "invited_date": "2025-01-15",
      "status": "active",
      "access_level": "user",
      "notes": "Primary user"
    }
  }
}
```

### Step 3: Install Ollama & Models
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

### Step 4: Run the App
```bash
# Start the main application
streamlit run app.py

# Optional: Start admin dashboard (on port 8502)
streamlit run admin_dashboard.py --server.port 8502
```

### Step 5: Test
1. Open browser to `http://localhost:8501`
2. Enter your configured email address
3. Upload a PDF resume
4. Paste a job description
5. Generate your cover letter!

## Option 2: Production Deployment (Streamlit Community Cloud)

### Step 1: GitHub Setup
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial commit: AI Cover Letter Assistant"

# Push to GitHub
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub repository
3. Set main file: `app.py`
4. Add secrets in app settings:

```toml
[auth]
admin_password = "your-secure-admin-password"
invitation_secret = "your-long-random-secret-key"

[invited_users]
"user1@example.com" = "John Doe"
"user2@example.com" = "Jane Smith"
```

### Step 3: Set Up Ollama Server
You'll need an accessible Ollama server. Options:
- Use a cloud VM with Ollama installed
- Use Ollama's cloud service (when available)
- Set up on your own server with public IP

Set environment variable:
```
OLLAMA_BASE_URL=http://your-ollama-server:11434
```

### Step 4: Deploy
Click "Deploy" in Streamlit Community Cloud dashboard.

## 🔧 Troubleshooting

### Common Issues

**"Module not found" errors**
```bash
pip install -r requirements.txt
```

**"Ollama connection failed"**
```bash
# Check if Ollama is running
ollama list

# Start Ollama if needed
ollama serve
```

**"User not invited" errors**
- Check email spelling in `invited_users.json`
- Verify JSON syntax is valid
- Restart the app after configuration changes

**Rate limiting errors**
- Wait 15 minutes for authentication limits to reset
- Check `rate_limits_*.json` files and delete if needed

### Verification
Run the test script to check your setup:
```bash
python test_setup.py
```

## 📱 Quick Demo

1. **Prepare test data**:
   - A PDF resume
   - A job description copied from any job posting

2. **Access the app**:
   - Enter your invited email address
   - Upload your resume PDF
   - Paste the job description

3. **Generate cover letter**:
   - Optionally specify key strengths to highlight
   - Click "Generate Cover Letter"
   - Edit the result as needed
   - Download as PDF or text

4. **See personalization in action**:
   - Use the app multiple times
   - Notice how it learns your preferences
   - Check the "Learning Dashboard" in the sidebar

## 🎯 Next Steps

### For Administrators
- Set up the admin dashboard for user management
- Configure monitoring and alerts
- Set up regular backups of user data
- Review security audit logs periodically

### For Users
- Upload your latest resume
- Try different job descriptions
- Experiment with specifying different strengths
- Use the editing feature to teach the AI your preferences

### For Developers
- Customize the AI prompts in `app.py`
- Add new features or integrations
- Modify the UI/UX as needed
- Enhance security features

## 📞 Need Help?

- Check the full [README.md](README.md) for detailed documentation
- Review [DEPLOYMENT.md](DEPLOYMENT.md) for deployment specifics
- Run `python test_setup.py` to diagnose issues
- Check the security audit logs for authentication problems

---

**You're all set! 🎉 Start generating amazing cover letters with AI assistance!**