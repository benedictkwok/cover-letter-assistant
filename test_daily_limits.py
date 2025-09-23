#!/usr/bin/env python3
"""
Test script for daily cover letter limit functionality
"""

import sys
import os
sys.path.append('.')

from security_utils import (
    check_daily_cover_letter_limit, 
    record_cover_letter_generation,
    get_daily_usage_stats,
    reset_user_daily_limit
)

def test_daily_limits():
    print("🧪 Testing Daily Cover Letter Limits")
    print("=" * 40)
    
    test_user = "test@example.com"
    
    # Test 1: Check initial limit
    print("\n1️⃣ Testing initial daily limit...")
    status = check_daily_cover_letter_limit(test_user)
    print(f"✅ Initial status: {status['used_today']}/{status['daily_limit']} used, {status['remaining']} remaining")
    
    # Test 2: Generate some cover letters
    print("\n2️⃣ Generating test cover letters...")
    for i in range(3):
        if record_cover_letter_generation(test_user):
            status = check_daily_cover_letter_limit(test_user)
            print(f"✅ Generated #{i+1}: {status['used_today']}/{status['daily_limit']} used, {status['remaining']} remaining")
        else:
            print(f"❌ Failed to record generation #{i+1}")
    
    # Test 3: Check if limit works
    print("\n3️⃣ Testing limit enforcement...")
    status = check_daily_cover_letter_limit(test_user)
    if status['allowed']:
        print(f"✅ User can still generate ({status['remaining']} remaining)")
    else:
        print(f"🚫 User has reached daily limit ({status['used_today']}/{status['daily_limit']})")
    
    # Test 4: Try to exceed limit
    print("\n4️⃣ Testing limit exceeded scenario...")
    for i in range(3):
        if record_cover_letter_generation(test_user):
            status = check_daily_cover_letter_limit(test_user)
            print(f"✅ Generated extra #{i+1}: {status['used_today']}/{status['daily_limit']} used")
            if not status['allowed']:
                print(f"🚫 Limit reached at {status['used_today']} generations")
                break
    
    # Test 5: Usage stats
    print("\n5️⃣ Testing usage statistics...")
    stats = get_daily_usage_stats()
    print(f"✅ Daily stats: {stats['total_today']} total, {stats['users_today']} users")
    
    # Test 6: Admin reset
    print("\n6️⃣ Testing admin reset...")
    if reset_user_daily_limit(test_user):
        status = check_daily_cover_letter_limit(test_user)
        print(f"✅ Reset successful: {status['used_today']}/{status['daily_limit']} used")
    else:
        print("❌ Reset failed")
    
    print("\n🎉 All tests completed!")

if __name__ == "__main__":
    test_daily_limits()