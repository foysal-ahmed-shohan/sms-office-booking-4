#!/usr/bin/env python3
"""Test script for OfficeRND integration"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.officernd_service import officernd_service
from app.schemas.booking_schema import get_dynamic_slot_prompts
import json


def test_token_acquisition():
    """Test getting access token"""
    print("\n=== Testing Token Acquisition ===")
    token = officernd_service._get_access_token()
    if token:
        print(f"✓ Successfully obtained token: {token[:20]}...")
        return True
    else:
        print("✗ Failed to obtain token")
        return False


def test_get_locations():
    """Test fetching locations"""
    print("\n=== Testing Get Locations ===")
    locations = officernd_service.get_locations()
    
    if locations:
        print(f"✓ Found {len(locations)} locations:")
        for loc in locations[:5]:  # Show first 5
            print(f"  - {loc.get('name')} ({loc.get('city')}, {loc.get('state')})")
        return True
    else:
        print("✗ No locations found")
        return False


def test_get_resource_types():
    """Test fetching resource types"""
    print("\n=== Testing Get Resource Types ===")
    resource_types = officernd_service.get_resource_types()
    
    if resource_types:
        print(f"✓ Found {len(resource_types)} resource types:")
        for rt in resource_types:
            print(f"  - {rt.get('title')} (type: {rt.get('type')})")
        return True
    else:
        print("✗ No resource types found")
        return False


def test_location_matching():
    """Test location matching with variations"""
    print("\n=== Testing Location Matching ===")
    test_cases = [
        "New York",
        "new york",
        "NYC",
        "Atlanta",
        "Invalid City",
        "san francisco"
    ]
    
    for test_input in test_cases:
        match = officernd_service.match_location(test_input)
        if match:
            print(f"✓ '{test_input}' -> '{match.get('name')}'")
        else:
            print(f"✗ '{test_input}' -> No match")
    
    return True


def test_resource_type_matching():
    """Test resource type matching"""
    print("\n=== Testing Resource Type Matching ===")
    test_cases = [
        "meeting room",
        "conference room",
        "desk",
        "hot desk",
        "private office",
        "invalid type"
    ]
    
    for test_input in test_cases:
        match = officernd_service.match_resource_type(test_input)
        if match:
            print(f"✓ '{test_input}' -> '{match.get('title')}'")
        else:
            print(f"✗ '{test_input}' -> No match")
    
    return True


def test_dynamic_prompts():
    """Test dynamic prompt generation"""
    print("\n=== Testing Dynamic Prompts ===")
    prompts = get_dynamic_slot_prompts()
    
    print("Location prompt:")
    print(f"  {prompts['location']}")
    
    print("\nRoom type prompt:")
    print(f"  {prompts['room_type']}")
    
    return True


def test_suggestions():
    """Test suggestion formatting"""
    print("\n=== Testing Suggestions ===")
    
    location_suggestions = officernd_service.get_location_suggestions()
    print(f"Location suggestions: {location_suggestions}")
    
    resource_suggestions = officernd_service.get_resource_type_suggestions()
    print(f"Resource type suggestions: {resource_suggestions}")
    
    return True


def main():
    """Run all tests"""
    print("Starting OfficeRND Integration Tests")
    print("=" * 50)
    
    tests = [
        test_token_acquisition,
        test_get_locations,
        test_get_resource_types,
        test_location_matching,
        test_resource_type_matching,
        test_dynamic_prompts,
        test_suggestions
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with error: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")


if __name__ == "__main__":
    main()