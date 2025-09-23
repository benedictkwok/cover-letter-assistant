#!/usr/bin/env python3
"""
VS Code MCP Interface
A simple interface to interact with the MCP server from within VS Code
"""

import json
import sys
from mcp_server import UsageAnalyticsServer

def print_header(title):
    """Print a formatted header."""
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)

def print_json(data):
    """Print JSON data in a formatted way."""
    print(json.dumps(data, indent=2))

def main():
    """Main interface for MCP server interaction."""
    if len(sys.argv) < 2:
        print_header("Cover Letter Assistant - MCP Server Interface")
        print("\nUsage: python vscode_mcp_interface.py <command>")
        print("\nAvailable commands:")
        print("  stats     - Get comprehensive usage statistics")
        print("  recent    - Get recent activity summary")
        print("  health    - Get system health metrics")
        print("  all       - Get all available data")
        print("\nExample:")
        print("  python vscode_mcp_interface.py stats")
        return

    command = sys.argv[1].lower()
    server = UsageAnalyticsServer()

    try:
        if command == "stats":
            print_header("Usage Statistics")
            stats = server.get_aggregated_stats()
            print_json(stats)
            
        elif command == "recent":
            print_header("Recent Activity (Last 24 Hours)")
            recent = server.get_recent_activity_summary()
            print_json(recent)
            
        elif command == "health":
            print_header("System Health")
            stats = server.get_aggregated_stats()
            total_stats = stats.get("total_stats", {})
            health = {
                "system_status": "healthy" if total_stats.get("success_rate", 0) > 95 else "degraded",
                "success_rate": total_stats.get("success_rate", 0),
                "avg_processing_time": total_stats.get("avg_processing_time", 0),
                "total_users": total_stats.get("total_users", 0),
                "uptime_indicator": "operational" if total_stats.get("total_generations", 0) > 0 else "no_activity"
            }
            print_json(health)
            
        elif command == "all":
            print_header("Complete Usage Analytics Report")
            
            print("\n📊 USAGE STATISTICS")
            print("-" * 40)
            stats = server.get_aggregated_stats()
            print_json(stats)
            
            print("\n📅 RECENT ACTIVITY")
            print("-" * 40)
            recent = server.get_recent_activity_summary()
            print_json(recent)
            
            print("\n🏥 SYSTEM HEALTH")
            print("-" * 40)
            total_stats = stats.get("total_stats", {})
            health = {
                "system_status": "healthy" if total_stats.get("success_rate", 0) > 95 else "degraded",
                "success_rate": total_stats.get("success_rate", 0),
                "avg_processing_time": total_stats.get("avg_processing_time", 0),
                "total_users": total_stats.get("total_users", 0),
                "uptime_indicator": "operational" if total_stats.get("total_generations", 0) > 0 else "no_activity"
            }
            print_json(health)
            
        else:
            print(f"❌ Unknown command: {command}")
            print("Available commands: stats, recent, health, all")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())