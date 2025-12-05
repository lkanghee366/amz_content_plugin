#!/usr/bin/env python3
"""Test brand extraction from Amazon API"""
import os
from dotenv import load_dotenv
from amazon_api import AmazonProductAPI

load_dotenv()

print("=" * 70)
print("TESTING BRAND EXTRACTION")
print("=" * 70)

api = AmazonProductAPI(
    access_key=os.getenv('AMAZON_ACCESS_KEY'),
    secret_key=os.getenv('AMAZON_SECRET_KEY'),
    partner_tag=os.getenv('AMAZON_PARTNER_TAG'),
    region=os.getenv('AMAZON_REGION', 'us-east-1')
)

products = api.search_products('best coffee maker', max_results=5)

print(f"\n✅ Found {len(products)} products\n")

for i, p in enumerate(products, 1):
    print(f"{i}. ASIN: {p['asin']}")
    print(f"   Brand: '{p['brand']}'")
    print(f"   Title: {p['title'][:60]}...")
    print(f"   Price: {p['price']}")
    print()

print("=" * 70)
