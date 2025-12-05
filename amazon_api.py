"""
Amazon Product Advertising API Handler
Using custom paapi_client (no external library needed)
"""
import logging
import sys
import os

# Add parent directory to path to import paapi_client
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import paapi_client


def _first_string(value):
    """Return the first non-empty string found in a nested PA-API structure."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        for item in value:
            candidate = _first_string(item)
            if candidate:
                return candidate
        return ""
    if isinstance(value, dict):
        # Prefer common semantic keys before scanning entire dict
        for key in ("DisplayValue", "DisplayValues", "Label", "Name", "Value", "value"):
            if key in value:
                candidate = _first_string(value[key])
                if candidate:
                    return candidate
        for nested_value in value.values():
            candidate = _first_string(nested_value)
            if candidate:
                return candidate
    return ""

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AmazonProductAPI:
    """Amazon PA-API wrapper for product search using custom client"""
    
    def __init__(self, access_key: str, secret_key: str, partner_tag: str, region: str = "us-east-1"):
        """Initialize Amazon PA-API client"""
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.region = region
        
        logging.info(f"✅ Amazon PA-API initialized (custom client) for region: {region}")

    @staticmethod
    def _extract_brand(item: dict) -> str:
        """Extract brand/manufacturer information from a PA-API item payload."""
        item_info = item.get('ItemInfo') or {}

        search_paths = [
            ('ByLineInfo', 'Brand'),
            ('ByLineInfo', 'Manufacturer'),
            ('ProductInfo', 'Brand'),
            ('ProductInfo', 'Manufacturer'),
            ('ManufactureInfo', 'Brand'),
            ('ManufactureInfo', 'Manufacturer'),
        ]

        for path in search_paths:
            node = item_info
            for key in path:
                node = node.get(key) if isinstance(node, dict) else None
                if not node:
                    break
            if node:
                brand_value = _first_string(node)
                if brand_value:
                    return brand_value

        fallback_candidates = [
            item.get('Brand'),
            item.get('brand'),
            item.get('Manufacturer'),
        ]

        for candidate in fallback_candidates:
            brand_value = _first_string(candidate)
            if brand_value:
                return brand_value

        title_info = item_info.get('Title') if isinstance(item_info, dict) else {}
        title_value = _first_string(title_info)
        if title_value:
            parts = title_value.split()
            if parts:
                return parts[0]

        return ""
    
    def search_products(self, keyword: str, max_results: int = 10) -> list:
        """
        Search for products on Amazon
        
        Args:
            keyword: Search keyword
            max_results: Maximum number of results (default: 10)
        
        Returns:
            List of product dictionaries with standardized fields
        """
        try:
            logging.info(f"🔍 Searching Amazon for: '{keyword}' (max {max_results} results)")
            
            # Use custom paapi_client
            items = paapi_client.search_items(keyword, max_items=max_results)
            
            if not items:
                logging.warning(f"⚠️ No products found for keyword: {keyword}")
                return []
            
            products = []
            
            for item in items:
                try:
                    # Extract ASIN
                    asin = item.get('ASIN', '')
                    
                    # Extract URL
                    url = item.get('DetailPageURL', '')
                    
                    # Extract title
                    title = 'N/A'
                    item_info = item.get('ItemInfo', {})
                    if item_info:
                        title_obj = item_info.get('Title', {})
                        if title_obj:
                            title = title_obj.get('DisplayValue', 'N/A')
                    
                    # Extract image
                    image_url = ''
                    images = item.get('Images', {})
                    if images:
                        primary = images.get('Primary', {})
                        if primary:
                            large = primary.get('Large', {})
                            if large:
                                image_url = large.get('URL', '')
                    
                    # Extract price
                    price = ''
                    offers = item.get('Offers', {})
                    if offers:
                        listings = offers.get('Listings', [])
                        if listings and len(listings) > 0:
                            listing = listings[0]
                            price_obj = listing.get('Price', {})
                            if price_obj:
                                price = price_obj.get('DisplayAmount', '')
                    
                    # Extract rating
                    rating = ''
                    customer_reviews = item.get('CustomerReviews', {})
                    if customer_reviews:
                        star_rating = customer_reviews.get('StarRating', {})
                        if star_rating:
                            rating = star_rating.get('DisplayValue', '')
                    
                    # Extract review count
                    review_count = 0
                    if customer_reviews:
                        review_count = customer_reviews.get('Count', 0)
                    
                    # Extract features and brand
                    features = []
                    brand = ''
                    if item_info:
                        features_obj = item_info.get('Features', {})
                        if features_obj:
                            features = features_obj.get('DisplayValues', [])
                    brand = self._extract_brand(item)
                    if not brand:
                        logging.debug(f"🔎 No brand found for ASIN {asin}")
                    
                    product = {
                        'asin': asin,
                        'title': title,
                        'url': url,
                        'image_url': image_url,
                        'price': price,
                        'rating': rating,
                        'review_count': review_count,
                        'features': features,
                        'brand': brand
                    }
                    
                    products.append(product)
                    logging.info(f"✓ Found: {title[:50]}...")
                
                except Exception as e:
                    logging.warning(f"⚠️ Error parsing product item: {e}")
                    continue
            
            logging.info(f"✅ Retrieved {len(products)} products for '{keyword}'")
            return products
        
        except Exception as e:
            logging.error(f"❌ Amazon API search failed for '{keyword}': {e}")
            import traceback
            logging.error(traceback.format_exc())
            return []
    
    def get_product_details(self, asin: str) -> dict:
        """Get detailed information for a specific product by ASIN"""
        try:
            items = paapi_client.get_items([asin])
            
            if not items or len(items) == 0:
                return {}
            
            item = items[0]
            
            # Use same extraction logic as search_products
            item_info = item.get('ItemInfo', {})
            images = item.get('Images', {})
            offers = item.get('Offers', {})
            
            title = 'N/A'
            if item_info:
                title_obj = item_info.get('Title', {})
                if title_obj:
                    title = title_obj.get('DisplayValue', 'N/A')
            
            image_url = ''
            if images:
                primary = images.get('Primary', {})
                if primary:
                    large = primary.get('Large', {})
                    if large:
                        image_url = large.get('URL', '')
            
            price = ''
            if offers:
                listings = offers.get('Listings', [])
                if listings and len(listings) > 0:
                    price_obj = listings[0].get('Price', {})
                    if price_obj:
                        price = price_obj.get('DisplayAmount', '')
            
            features = []
            brand = ''
            if item_info:
                features_obj = item_info.get('Features', {})
                if features_obj:
                    features = features_obj.get('DisplayValues', [])
            brand = self._extract_brand(item)
            if not brand:
                logging.debug(f"🔎 No brand found for ASIN {item.get('ASIN', '')}")
            
            product = {
                'asin': item.get('ASIN', ''),
                'title': title,
                'url': item.get('DetailPageURL', ''),
                'image_url': image_url,
                'price': price,
                'rating': '',
                'features': features,
                'brand': brand
            }
            
            return product
        
        except Exception as e:
            logging.error(f"❌ Failed to get product details for ASIN {asin}: {e}")
            return {}
