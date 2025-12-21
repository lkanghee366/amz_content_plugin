#!/usr/bin/env python3
"""
Test WordPress connection
"""
from wordpress_api import WordPressAPI

print("\n" + "="*60)
print("WordPress Connection Test")
print("="*60)

# Test MountainTidesWine
print("\nTesting MountainTidesWine...")
wp = WordPressAPI(
    site_url="https://www.mountaintideswine.com",
    username="admin",
    app_password="IFJ5 sDd8 AFQe Z9cq BGmi 84bD"
)

result = wp.test_connection()
print(f"Result: {'✓ Success' if result else '✗ Failed'}")

print("\n" + "="*60 + "\n")
