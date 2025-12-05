#!/usr/bin/env python3
"""
Debug script to test Amazon API directly
"""
import os
from dotenv import load_dotenv
from amazon.paapi import AmazonAPI

# Load environment
load_dotenv()

print("=" * 60)
print("AMAZON PA-API DEBUG TEST")
print("=" * 60)

# Get credentials
access_key = os.getenv('AMAZON_ACCESS_KEY')
secret_key = os.getenv('AMAZON_SECRET_KEY')
partner_tag = os.getenv('AMAZON_PARTNER_TAG')
country = "US"

print(f"\n✓ Access Key: {access_key[:10]}...")
print(f"✓ Secret Key: {secret_key[:10]}...")
print(f"✓ Partner Tag: {partner_tag}")
print(f"✓ Country: {country}")

# Initialize API
try:
    amazon = AmazonAPI(
        access_key=access_key,
        secret_key=secret_key,
        partner_tag=partner_tag,
        country=country
    )
    print("\n✅ Amazon API initialized successfully!")
except Exception as e:
    print(f"\n❌ Failed to initialize: {e}")
    exit(1)

# Test search
keyword = "coffee maker"
print(f"\n🔍 Searching for: '{keyword}'")
print("-" * 60)

try:
    # Method 1: Simple search (no resources specified)
    print("\n[TEST 1] Simple search without resources:")
    result1 = amazon.search_items(keywords=keyword, item_count=3)
    print(f"  Type: {type(result1)}")
    print(f"  Has 'items' attr: {hasattr(result1, 'items')}")
    
    # Check if items is a method or attribute
    items_attr = getattr(result1, 'items', None)
    print(f"  'items' is callable: {callable(items_attr)}")
    
    # Get items list
    items_list = result1.items() if callable(items_attr) else items_attr
    
    if items_list:
        print(f"  Number of items: {len(items_list)}")
        print(f"  First item ASIN: {items_list[0].asin if items_list else 'N/A'}")
        
        # Check what attributes the item has
        if items_list:
            item = items_list[0]
            print(f"\n  Available attributes on first item:")
            for attr in dir(item):
                if not attr.startswith('_'):
                    print(f"    - {attr}")
    else:
        print("  ⚠️ No items returned!")
    
    # Method 2: Search with resources
    print("\n[TEST 2] Search WITH resources:")
    resources = [
        "ItemInfo.Title",
        "ItemInfo.Features",
        "Images.Primary.Large",
        "Offers.Listings.Price"
    ]
    
    result2 = amazon.search_items(
        keywords=keyword, 
        item_count=3,
        resources=resources
    )
    print(f"  Type: {type(result2)}")
    
    items_attr2 = getattr(result2, 'items', None)
    items_list2 = result2.items() if callable(items_attr2) else items_attr2
    
    if items_list2:
        print(f"  Number of items: {len(items_list2)}")
        
        for i, item in enumerate(items_list2[:2], 1):
            print(f"\n  Item #{i}:")
            print(f"    ASIN: {item.asin if hasattr(item, 'asin') else 'N/A'}")
            
            # Title
            if hasattr(item, 'item_info') and item.item_info:
                if hasattr(item.item_info, 'title') and item.item_info.title:
                    print(f"    Title: {item.item_info.title.display_value[:60]}...")
                else:
                    print(f"    Title: N/A (no title attribute)")
            else:
                print(f"    Title: N/A (no item_info)")
            
            # URL
            if hasattr(item, 'detail_page_url'):
                print(f"    URL: {item.detail_page_url[:50]}...")
            else:
                print(f"    URL: N/A")
            
            # Image
            if hasattr(item, 'images') and item.images:
                if hasattr(item.images, 'primary') and item.images.primary:
                    if hasattr(item.images.primary, 'large') and item.images.primary.large:
                        print(f"    Image: {item.images.primary.large.url[:50]}...")
                    else:
                        print(f"    Image: N/A (no large)")
                else:
                    print(f"    Image: N/A (no primary)")
            else:
                print(f"    Image: N/A (no images)")
            
            # Price
            if hasattr(item, 'offers') and item.offers:
                if hasattr(item.offers, 'listings') and item.offers.listings:
                    listing = item.offers.listings[0]
                    if hasattr(listing, 'price') and listing.price:
                        print(f"    Price: {listing.price.display_amount}")
                    else:
                        print(f"    Price: N/A (no price)")
                else:
                    print(f"    Price: N/A (no listings)")
            else:
                print(f"    Price: N/A (no offers)")
            
            # Features
            if hasattr(item, 'item_info') and item.item_info:
                if hasattr(item.item_info, 'features') and item.item_info.features:
                    features = item.item_info.features.display_values[:3]
                    print(f"    Features ({len(features)}):")
                    for f in features:
                        print(f"      - {f[:60]}...")
                else:
                    print(f"    Features: N/A")
            else:
                print(f"    Features: N/A (no item_info)")
    else:
        print("  ⚠️ No items returned!")
        
except Exception as e:
    print(f"\n❌ Search failed: {e}")
    import traceback
    print("\nFull traceback:")
    print(traceback.format_exc())

print("\n" + "=" * 60)
print("DEBUG TEST COMPLETE")
print("=" * 60)
