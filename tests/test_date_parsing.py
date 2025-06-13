#!/usr/bin/env python3
"""Test date parsing functionality"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.date_utils import parse_user_datetime, datetime_to_officernd_format, format_datetime_for_display

def test_date_parsing():
    """Test various date and time formats"""
    print("\n" + "="*70)
    print("DATE PARSING TEST")
    print("="*70)
    
    test_cases = [
        # (date, time, expected_success)
        ("Dec 25, 2025", "2pm", True),
        ("25 Dec 2025", "14:00", True),
        ("December 25, 2025", "2:30pm", True),
        ("2025-12-25", "14:30", True),
        ("12/25/2025", "2 pm", True),
        ("dec 25 2025", "2PM", True),
        ("4 dec 2025", "1pm", True),
        ("invalid date", "2pm", False),
        ("Dec 25, 2025", "invalid time", False),
    ]
    
    for date_str, time_str, should_succeed in test_cases:
        print(f"\nTesting: '{date_str}' at '{time_str}'")
        
        dt = parse_user_datetime(date_str, time_str)
        
        if dt:
            print(f"✅ Parsed successfully: {dt}")
            print(f"   OfficeRND format: {datetime_to_officernd_format(dt)}")
            print(f"   Display format: {format_datetime_for_display(dt)}")
            if not should_succeed:
                print("   ⚠️  WARNING: Expected to fail but succeeded")
        else:
            print("❌ Failed to parse")
            if should_succeed:
                print("   ⚠️  WARNING: Expected to succeed but failed")
    
    # Test end time parsing
    print("\n\nTesting time ranges:")
    print("-" * 50)
    
    # Test with end time
    start_dt = parse_user_datetime("Dec 30, 2025", "2pm")
    end_dt = parse_user_datetime("Dec 30, 2025", "4pm")
    
    if start_dt and end_dt:
        print(f"Start: {datetime_to_officernd_format(start_dt)}")
        print(f"End: {datetime_to_officernd_format(end_dt)}")
        print(f"Duration: {(end_dt - start_dt).total_seconds() / 3600} hours")
    else:
        print("Failed to parse time range")

if __name__ == "__main__":
    test_date_parsing()