#!/usr/bin/env python3
"""
Test WordPress connection
"""
from wordpress_api import WordPressAPI

print("\n" + "="*60)
print("WordPress Connection Test")
print("="*60)

# Test ProKitchenReview
print("\nTesting ProKitchenReview...")
wp = WordPressAPI(
    site_url="https://prokitchenreview.com",
    username="admin",
    app_password="5A03 TYh3 3BdE mKV9 pvWw zPc8"
)

result = wp.test_connection()
print(f"Result: {'✓ Success' if result else '✗ Failed'}")

print("\n" + "="*60 + "\n")
