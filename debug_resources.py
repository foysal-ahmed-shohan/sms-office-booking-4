#!/usr/bin/env python3
"""Debug resource types from OfficeRND"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.officernd_service import officernd_service

def debug_resources():
    """Check what resource types are available"""
    # Get Atlanta location ID
    locations = officernd_service.get_locations()
    atlanta_id = None
    for loc in locations:
        if loc['name'].lower() == 'atlanta':
            atlanta_id = loc['id']
            break
    
    if not atlanta_id:
        print("Atlanta location not found")
        return
    
    print(f"Atlanta location ID: {atlanta_id}")
    
    # Get all resources for Atlanta
    resources = officernd_service.get_resources(location_id=atlanta_id)
    
    print(f"\nTotal resources in Atlanta: {len(resources)}")
    print("\nResource types found:")
    
    # Group by type
    types_map = {}
    for res in resources:
        res_type = res.get('type', 'unknown')
        if res_type not in types_map:
            types_map[res_type] = []
        types_map[res_type].append(res)
    
    # Show each type
    for res_type, items in sorted(types_map.items()):
        print(f"\n{res_type}: {len(items)} resources")
        for i, res in enumerate(items[:3]):  # Show first 3 of each type
            print(f"  - {res['name']}")
            if res.get('description'):
                print(f"    Description: {res['description']}")
        if len(items) > 3:
            print(f"  ... and {len(items) - 3} more")

if __name__ == "__main__":
    debug_resources()