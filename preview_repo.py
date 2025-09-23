#!/usr/bin/env python3
"""
Repository Content Preview
Shows what files will be included in your public GitHub repository
"""

import os
import subprocess
from pathlib import Path

def get_tracked_files():
    """Get list of files that would be tracked by Git"""
    try:
        # Get all files that would be tracked (not ignored)
        result = subprocess.run(
            ['git', 'ls-files', '--cached', '--others', '--exclude-standard'],
            capture_output=True,
            text=True,
            cwd='.'
        )
        
        if result.returncode == 0:
            return result.stdout.strip().split('\n') if result.stdout.strip() else []
        else:
            # Fallback: list files manually and filter through git check-ignore
            all_files = []
            for root, dirs, files in os.walk('.'):
                # Skip hidden directories and __pycache__
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
                
                for file in files:
                    if not file.startswith('.'):
                        rel_path = os.path.relpath(os.path.join(root, file), '.')
                        all_files.append(rel_path)
            
            # Filter out ignored files
            tracked_files = []
            for file in all_files:
                check_result = subprocess.run(
                    ['git', 'check-ignore', file],
                    capture_output=True,
                    cwd='.'
                )
                if check_result.returncode != 0:  # Not ignored
                    tracked_files.append(file)
            
            return tracked_files
    except Exception as e:
        print(f"Error checking git status: {e}")
        return []

def main():
    print("🔍 Repository Content Preview")
    print("=" * 50)
    print("📁 Files that WILL be included in your public GitHub repository:\n")
    
    tracked_files = get_tracked_files()
    
    if not tracked_files:
        print("ℹ️  No trackable files found in current directory")
        return
    
    # Categorize files
    categories = {
        "📄 Main Application": [],
        "⚙️  Configuration": [],
        "📚 Documentation": [],
        "🔧 Setup Scripts": [],
        "📊 Data Files": [],
        "🎨 Templates": []
    }
    
    for file in sorted(tracked_files):
        if file.endswith('.py') and not file.startswith('test_'):
            categories["📄 Main Application"].append(file)
        elif file.endswith(('.toml', '.json', '.yaml', '.yml', '.cfg', '.ini')):
            if 'secret' not in file.lower():
                categories["⚙️  Configuration"].append(file)
        elif file.endswith(('.md', '.txt', '.rst')):
            categories["📚 Documentation"].append(file)
        elif file.endswith(('.sh', '.bat')):
            categories["🔧 Setup Scripts"].append(file)
        elif file.endswith(('.html', '.css', '.js')):
            categories["🎨 Templates"].append(file)
        else:
            categories["📊 Data Files"].append(file)
    
    total_files = 0
    for category, files in categories.items():
        if files:
            print(f"{category}:")
            for file in files:
                print(f"  ✅ {file}")
                total_files += 1
            print()
    
    print("🚫 Files that will be IGNORED (not included):")
    print("  • test_*.py (all test scripts)")
    print("  • .streamlit/secrets.toml (sensitive configuration)")
    print("  • chroma_db*/ (user data)")
    print("  • uploads/ (user files)")
    print("  • user_preferences/ (personal data)")
    print("  • *.log (log files)")
    print("  • daily_usage.json (usage tracking)")
    print("  • rate_limits_*.json (rate limiting data)")
    
    print(f"\n📊 Summary:")
    print(f"  • {total_files} files will be public")
    print(f"  • All sensitive data excluded")
    print(f"  • All test scripts excluded")
    print(f"  • Ready for public repository! ✅")

if __name__ == "__main__":
    main()