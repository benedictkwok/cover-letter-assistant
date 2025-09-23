# VS Code MCP Integration for Cover Letter Assistant

This folder contains VS Code-specific configuration for integrating with the MCP (Model Context Protocol) server.

## Quick Start in VS Code

1. **Open the project in VS Code:**
   ```bash
   cd /Users/bkwok/dev/ai_project/project-3-11/job-assistant/cover-letter-assistant
   open -a "Visual Studio Code" .
   ```

2. **Use VS Code Tasks** (Cmd+Shift+P → "Tasks: Run Task"):
   - **Start MCP Server** - Starts the MCP server in background
   - **Test MCP Server** - Runs comprehensive server tests
   - **Get Usage Statistics** - Quick stats display
   - **Get Recent Activity** - Last 24 hours summary
   - **Run Streamlit App** - Start the main application

3. **Use the VS Code MCP Interface:**
   ```bash
   # In VS Code terminal:
   python vscode_mcp_interface.py stats
   python vscode_mcp_interface.py recent
   python vscode_mcp_interface.py health
   python vscode_mcp_interface.py all
   ```

## Available Commands

### Via VS Code Tasks
- `Cmd+Shift+P` → "Tasks: Run Task" → Select task

### Via Terminal Interface
```bash
# Get comprehensive usage statistics
python vscode_mcp_interface.py stats

# Get recent activity (last 24 hours)
python vscode_mcp_interface.py recent

# Get system health metrics
python vscode_mcp_interface.py health

# Get complete analytics report
python vscode_mcp_interface.py all
```

### Direct MCP Server
```bash
# Start MCP server for external clients
python mcp_server.py

# Run server tests
python test_mcp.py
```

## VS Code Configuration

The `.vscode/` folder contains:
- `tasks.json` - Predefined tasks for MCP operations
- `settings.json` - Python and workspace settings

## Privacy & Security

✅ **Privacy-First Design:**
- No personal user data exposed
- Only aggregated, anonymized statistics
- No resume content accessible
- Company names aggregated without user association

## Integration with AI Tools

While VS Code doesn't have native MCP support yet, you can:
1. Use the tasks and interface for quick analytics
2. Copy/paste results into AI chats for analysis
3. Use the data for monitoring and optimization

## Example Output

```json
{
  "total_stats": {
    "total_users": 5,
    "total_generations": 23,
    "success_rate": 95.7,
    "avg_processing_time": 2.1
  },
  "popular_companies": [
    {"company": "Apple Inc.", "applications": 4},
    {"company": "Google", "applications": 3}
  ]
}
```