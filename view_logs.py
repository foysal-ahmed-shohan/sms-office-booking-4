#!/usr/bin/env python3
"""
Utility script to view and monitor log files
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def tail_logs(log_file="logs/app.log", lines=50, follow=False):
    """Tail the log file"""
    if not Path(log_file).exists():
        print(f"Log file not found: {log_file}")
        return
    
    if follow:
        # Use tail -f for real-time monitoring
        try:
            subprocess.run(["tail", "-f", log_file])
        except KeyboardInterrupt:
            print("\nStopped monitoring logs")
    else:
        # Show last N lines
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            for line in all_lines[-lines:]:
                print(line.rstrip())


def search_logs(log_file="logs/app.log", pattern=None):
    """Search for patterns in logs"""
    if not Path(log_file).exists():
        print(f"Log file not found: {log_file}")
        return
    
    with open(log_file, 'r') as f:
        for line in f:
            if pattern.lower() in line.lower():
                print(line.rstrip())


def show_errors(log_file="logs/app.log"):
    """Show only error logs"""
    if not Path(log_file).exists():
        print(f"Log file not found: {log_file}")
        return
    
    print("=== ERROR LOGS ===")
    with open(log_file, 'r') as f:
        for line in f:
            if "ERROR" in line or "CRITICAL" in line:
                print(line.rstrip())


def show_sms_activity(log_file="logs/app.log"):
    """Show SMS related activity"""
    if not Path(log_file).exists():
        print(f"Log file not found: {log_file}")
        return
    
    print("=== SMS ACTIVITY ===")
    with open(log_file, 'r') as f:
        for line in f:
            if any(keyword in line for keyword in ["SMS", "From:", "To:", "Body:", "SID:"]):
                print(line.rstrip())


def clear_logs(log_file="logs/app.log"):
    """Clear the log file"""
    if not Path(log_file).exists():
        print(f"Log file not found: {log_file}")
        return
    
    confirm = input(f"Are you sure you want to clear {log_file}? (y/N): ")
    if confirm.lower() == 'y':
        open(log_file, 'w').close()
        print(f"Cleared {log_file}")
    else:
        print("Cancelled")


def main():
    parser = argparse.ArgumentParser(description="SMS Service Log Viewer")
    parser.add_argument("-f", "--follow", action="store_true", help="Follow log file in real-time")
    parser.add_argument("-n", "--lines", type=int, default=50, help="Number of lines to show (default: 50)")
    parser.add_argument("-s", "--search", help="Search for pattern in logs")
    parser.add_argument("-e", "--errors", action="store_true", help="Show only error logs")
    parser.add_argument("--sms", action="store_true", help="Show SMS activity")
    parser.add_argument("--clear", action="store_true", help="Clear log file")
    parser.add_argument("--file", default="logs/app.log", help="Log file path (default: logs/app.log)")
    
    args = parser.parse_args()
    
    if args.search:
        search_logs(args.file, args.search)
    elif args.errors:
        show_errors(args.file)
    elif args.sms:
        show_sms_activity(args.file)
    elif args.clear:
        clear_logs(args.file)
    else:
        tail_logs(args.file, args.lines, args.follow)


if __name__ == "__main__":
    main()