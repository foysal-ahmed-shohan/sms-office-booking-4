#!/usr/bin/env python3
"""Test with existing member phone number"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.officernd_service import officernd_service
import logging

# Show INFO level logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_existing_members():
    """Check existing members and companies"""
    print("\n" + "="*70)
    print("EXISTING MEMBERS/COMPANIES CHECK")
    print("="*70)
    
    # Get members
    print("\nFetching members...")
    members = officernd_service.get_members()
    print(f"Found {len(members)} members")
    
    # Show members with phone numbers
    members_with_phone = [m for m in members if m.get('properties', {}).get('phone')]
    print(f"\nMembers with phone numbers: {len(members_with_phone)}")
    for member in members_with_phone[:5]:  # Show first 5
        phone = member.get('properties', {}).get('phone', '')
        print(f"  - {member.get('name')}: {phone}")
    
    # Get companies
    print("\nFetching companies...")
    companies = officernd_service.get_companies()
    print(f"Found {len(companies)} companies")
    
    # Show companies with phone numbers
    companies_with_phone = [c for c in companies if c.get('properties', {}).get('phone')]
    print(f"\nCompanies with phone numbers: {len(companies_with_phone)}")
    for company in companies_with_phone[:5]:  # Show first 5
        phone = company.get('properties', {}).get('phone', '')
        print(f"  - {company.get('name')}: {phone}")
    
    # Test phone lookup
    if members_with_phone:
        test_phone = members_with_phone[0].get('properties', {}).get('phone')
        print(f"\n\nTesting lookup for existing phone: {test_phone}")
        result = officernd_service.find_member_or_company_by_phone(test_phone)
        if result:
            print(f"✅ Found {result['type']}: {result['name']} (ID: {result['id']})")
        else:
            print("❌ Not found (this shouldn't happen)")

if __name__ == "__main__":
    test_existing_members()