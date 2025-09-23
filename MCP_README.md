# Cover Letter Assistant - MCP Usage Analytics Server

This MCP (Model Context Protocol) server provides privacy-focused usage analytics for the Cover Letter Assistant application. It exposes aggregated usage statistics without any personal user data.

## Features

- **Privacy-First**: No personal data, resume content, or user identification exposed
- **Aggregated Statistics**: System-wide usage metrics and trends
- **Real-time Analytics**: Current system health and recent activity
- **Company Insights**: Popular companies (aggregated data only)

## Available Tools

### 1. `get_usage_statistics`
Returns comprehensive usage statistics including:
- Total users and generations
- Success rates and performance metrics
- Daily activity trends (last 30 days)
- Popular companies (aggregated)
- Hourly usage patterns

### 2. `get_recent_activity`
Returns recent activity summary including:
- Last 24 hours statistics
- Comparison with previous period
- Growth metrics

### 3. `get_system_health`
Returns system health indicators:
- Overall system status
- Success rate
- Performance metrics
- Uptime indicators

## Setup

1. Install MCP dependencies:
```bash
pip install -r mcp_requirements.txt
```

2. Ensure the main application database exists:
```bash
# The MCP server reads from usage_tracking.db created by the main app
# Make sure your Streamlit app has run at least once to create the database
```

3. Run the MCP server:
```bash
python mcp_server.py
```

## Configuration

The server can be configured in Claude Desktop or other MCP clients using the provided `mcp_config.json`:

```json
{
  "mcpServers": {
    "cover-letter-analytics": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/your/cover-letter-assistant"
    }
  }
}
```

## Privacy Guarantee

This MCP server is designed with privacy as the top priority:
- ✅ No user emails or personal identifiers exposed
- ✅ No resume content or personal data accessible
- ✅ Only aggregated, anonymized statistics provided
- ✅ Company names are aggregated without user association
- ✅ All data is statistical summaries only

## Example Usage

Once connected to an MCP client, you can:

```
Get overall usage statistics:
Tool: get_usage_statistics

Check recent activity:
Tool: get_recent_activity

Monitor system health:
Tool: get_system_health
```

## Data Sources

The server reads from the `usage_tracking.db` SQLite database created by the main Streamlit application. Ensure the main app has been run and has generated some usage data before using the MCP server.