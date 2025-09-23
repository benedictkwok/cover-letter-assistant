#!/usr/bin/env python3
"""
MCP Server for Cover Letter Assistant Usage Analytics
Provides privacy-focused usage statistics without exposing personal data.
"""

import asyncio
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import Resource, Tool, TextContent, ImageContent, EmbeddedResource
import mcp.types as types
from pydantic import AnyUrl
import mcp.server.stdio


class UsageAnalyticsServer:
    def __init__(self):
        self.db_path = "usage_tracking.db"
        
    def get_aggregated_stats(self) -> Dict[str, Any]:
        """Get aggregated usage statistics without personal information."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total aggregated statistics
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
            
            # Daily activity for last 30 days (no personal info)
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
            
            # Popular companies (aggregated, no user info)
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
            
            # Hourly usage patterns (no personal info)
            cursor.execute('''
                SELECT 
                    strftime('%H', timestamp) as hour,
                    COUNT(*) as generations
                FROM usage_logs 
                WHERE action_type = 'cover_letter_generation'
                AND success = 1
                AND timestamp >= date('now', '-7 days')
                GROUP BY strftime('%H', timestamp)
                ORDER BY hour
            ''')
            
            hourly_patterns = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_stats": {
                    "total_users": total_stats[0] or 0,
                    "total_generations": total_stats[1] or 0,
                    "avg_length": round(total_stats[2] or 0, 2),
                    "avg_processing_time": round(total_stats[3] or 0, 2),
                    "successful_generations": total_stats[4] or 0,
                    "failed_generations": total_stats[5] or 0,
                    "success_rate": round((total_stats[4] / total_stats[1] * 100) if total_stats[1] > 0 else 0, 2)
                },
                "daily_activity": [
                    {"date": row[0], "generations": row[1], "active_users": row[2]} 
                    for row in daily_activity
                ],
                "popular_companies": [
                    {"company": row[0], "applications": row[1]} 
                    for row in popular_companies
                ],
                "hourly_patterns": [
                    {"hour": row[0], "generations": row[1]} 
                    for row in hourly_patterns
                ]
            }
            
        except Exception as e:
            return {"error": f"Failed to get stats: {str(e)}"}
    
    def get_recent_activity_summary(self) -> Dict[str, Any]:
        """Get recent activity summary (last 24 hours) without personal data."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Activity in last 24 hours
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_today,
                    COUNT(DISTINCT user_email) as unique_users_today,
                    AVG(cover_letter_length) as avg_length_today,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_today
                FROM usage_logs 
                WHERE action_type = 'cover_letter_generation'
                AND timestamp >= datetime('now', '-24 hours')
            ''')
            
            today_stats = cursor.fetchone()
            
            # Compare with previous 24 hours
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_yesterday,
                    COUNT(DISTINCT user_email) as unique_users_yesterday
                FROM usage_logs 
                WHERE action_type = 'cover_letter_generation'
                AND timestamp >= datetime('now', '-48 hours')
                AND timestamp < datetime('now', '-24 hours')
            ''')
            
            yesterday_stats = cursor.fetchone()
            
            conn.close()
            
            return {
                "last_24_hours": {
                    "total_generations": today_stats[0] or 0,
                    "unique_users": today_stats[1] or 0,
                    "avg_length": round(today_stats[2] or 0, 2),
                    "successful_generations": today_stats[3] or 0
                },
                "previous_24_hours": {
                    "total_generations": yesterday_stats[0] or 0,
                    "unique_users": yesterday_stats[1] or 0
                },
                "growth": {
                    "generation_change": (today_stats[0] or 0) - (yesterday_stats[0] or 0),
                    "user_change": (today_stats[1] or 0) - (yesterday_stats[1] or 0)
                }
            }
            
        except Exception as e:
            return {"error": f"Failed to get recent activity: {str(e)}"}


# Initialize the MCP server
server = Server("cover-letter-usage-analytics")
analytics = UsageAnalyticsServer()


@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools for usage analytics."""
    return [
        Tool(
            name="get_usage_statistics",
            description="Get comprehensive usage statistics for the cover letter assistant (aggregated, no personal data)",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_recent_activity",
            description="Get recent activity summary for the last 24 hours compared to previous period",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_system_health",
            description="Get system health metrics including success rates and performance",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> List[types.TextContent]:
    """Handle tool calls for usage analytics."""
    
    if name == "get_usage_statistics":
        stats = analytics.get_aggregated_stats()
        return [
            types.TextContent(
                type="text", 
                text=json.dumps(stats, indent=2)
            )
        ]
    
    elif name == "get_recent_activity":
        activity = analytics.get_recent_activity_summary()
        return [
            types.TextContent(
                type="text", 
                text=json.dumps(activity, indent=2)
            )
        ]
    
    elif name == "get_system_health":
        stats = analytics.get_aggregated_stats()
        
        # Calculate health metrics
        total_stats = stats.get("total_stats", {})
        health = {
            "system_status": "healthy" if total_stats.get("success_rate", 0) > 95 else "degraded",
            "success_rate": total_stats.get("success_rate", 0),
            "avg_processing_time": total_stats.get("avg_processing_time", 0),
            "total_users": total_stats.get("total_users", 0),
            "uptime_indicator": "operational" if total_stats.get("total_generations", 0) > 0 else "no_activity"
        }
        
        return [
            types.TextContent(
                type="text", 
                text=json.dumps(health, indent=2)
            )
        ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server."""
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="cover-letter-usage-analytics",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())