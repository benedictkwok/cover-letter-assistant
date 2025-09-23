#!/usr/bin/env python3
"""
Test script for the MCP server functionality
"""

import json
import sqlite3
from datetime import datetime
import sys
import os

# Add the current directory to the path to import our MCP server
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import UsageAnalyticsServer

def create_test_data():
    """Create some test data in the usage tracking database."""
    print("Creating test data...")
    
    # Initialize the database
    db_path = "usage_tracking.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables if they don't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            user_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            company_name TEXT,
            job_title TEXT,
            cover_letter_length INTEGER,
            processing_time_seconds REAL,
            success BOOLEAN DEFAULT TRUE,
            error_message TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usage_summary (
            user_email TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            first_use DATETIME,
            last_use DATETIME,
            total_cover_letters INTEGER DEFAULT 0,
            total_processing_time REAL DEFAULT 0,
            avg_cover_letter_length REAL DEFAULT 0
        )
    ''')
    
    # Insert test data
    test_data = [
        ('test1@example.com', 'user1', 'cover_letter_generation', 'Apple Inc.', 'Software Engineer', 450, 2.5, True),
        ('test2@example.com', 'user2', 'cover_letter_generation', 'Google', 'Product Manager', 380, 1.8, True),
        ('test1@example.com', 'user1', 'cover_letter_generation', 'Microsoft', 'Data Scientist', 420, 2.1, True),
        ('test3@example.com', 'user3', 'cover_letter_generation', 'Amazon', 'DevOps Engineer', 0, 0, False),
    ]
    
    for data in test_data:
        cursor.execute('''
            INSERT INTO usage_logs 
            (user_email, user_id, action_type, company_name, job_title, 
             cover_letter_length, processing_time_seconds, success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    conn.commit()
    conn.close()
    print("Test data created successfully!")

def test_mcp_server():
    """Test the MCP server functionality."""
    print("\nTesting MCP server functionality...")
    
    # Initialize the analytics server
    analytics = UsageAnalyticsServer()
    
    # Test get_aggregated_stats
    print("\n1. Testing get_aggregated_stats()...")
    stats = analytics.get_aggregated_stats()
    print(f"Stats retrieved: {json.dumps(stats, indent=2)}")
    
    # Test get_recent_activity_summary
    print("\n2. Testing get_recent_activity_summary()...")
    recent = analytics.get_recent_activity_summary()
    print(f"Recent activity: {json.dumps(recent, indent=2)}")
    
    print("\n✅ MCP server functionality test completed!")

def main():
    """Run the complete test."""
    print("🧪 Testing Cover Letter Assistant MCP Server")
    print("=" * 50)
    
    # Create test data
    create_test_data()
    
    # Test MCP server functionality
    test_mcp_server()
    
    print("\n🎉 All tests completed successfully!")
    print("\nYou can now use the MCP server with:")
    print("python mcp_server.py")

if __name__ == "__main__":
    main()