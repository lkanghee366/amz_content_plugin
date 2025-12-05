"""
Amazon Product Advertising API Handler
Using python-amazon-paapi library
"""
import logging
from amazon.paapi import AmazonAPI

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AmazonProductAPI:
    """Amazon PA-API wrapper for product search"""
    
    def __init__(self, access_key: str, secret_key: str, partner_tag: str, region: str = "us-east-1"):
        """Initialize Amazon PA-API client"""
        self.access_key = access_key
        self.secret_key = secret_key
        self.partner_tag = partner_tag
        self.region = region
        
        # Map region to country code for python-amazon-paapi
        region_map = {
            "us-east-1": "US",
            "eu-west-1": "UK",
            "eu-central-1": "DE",
            "ap-northeast-1": "JP",
            "ap-southeast-1": "SG"
        }
        self.country = region_map.get(region, "US")
        
        try:
            self.amazon = AmazonAPI(
                access_key=access_key,
                secret_key=secret_key,
                partner_tag=partner_tag,
                country=self.country
            )
            logging.info(f"✅ Amazon PA-API initialized for region: {self.country}")
        except Exception as e:
            logging.error(f"❌ Failed to initialize Amazon PA-API: {e}")
            raise
    
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
            
            # Define the resources we need, similar to the PHP plugin
            resources = [
                "ItemInfo.Title",
                "ItemInfo.Features",
                "ItemInfo.ByLineInfo", # For brand
                "Images.Primary.Large",
                "Offers.Listings.Price",
                "CustomerReviews.StarRating",
                "CustomerReviews.Count"
            ]

            # Search items using PA-API
            items_result = self.amazon.search_items(
                keywords=keyword,
                item_count=max_results,
                resources=resources
            )
            
            # Detailed logging for debugging
            # Note: items_result is a dict, and we need to call .items() method
            if not items_result:
                logging.error("❌ Amazon API returned an invalid or empty response.")
                logging.debug(f"Full API Response: {items_result}")
                return []
            
            # Get items - convert dict_items to list
            items_attr = getattr(items_result, 'items', None)
            items_list = list(items_result.items()) if callable(items_attr) else []
            
            if not items_list:
                logging.warning(f"⚠️ No items returned for keyword: {keyword}")
                return []
            
            products = []
            
            # items_list is a list of (key, value) tuples from dict.items()
            # We need to check the actual structure
            for item_data in items_list:
                try:
                    # Extract product data
                    product = {
                        'asin': item.asin if hasattr(item, 'asin') else '',
                        'title': 'N/A',
                        'url': item.detail_page_url if hasattr(item, 'detail_page_url') else '',
                        'image_url': '',
                        'price': '',
                        'rating': '',
                        'review_count': 0,
                        'features': []
                    }

                    if hasattr(item, 'item_info') and item.item_info is not None:
                        if hasattr(item.item_info, 'title') and item.item_info.title is not None:
                            product['title'] = item.item_info.title.display_value
                        
                        if hasattr(item.item_info, 'features') and item.item_info.features is not None:
                            product['features'] = item.item_info.features.display_values[:5]

                    # Image URL
                    if hasattr(item, 'images') and item.images is not None and hasattr(item.images, 'primary') and item.images.primary is not None:
                        if hasattr(item.images.primary, 'large') and item.images.primary.large is not None:
                            product['image_url'] = item.images.primary.large.url
                    
                    # Price
                    if hasattr(item, 'offers') and item.offers is not None and hasattr(item.offers, 'listings') and item.offers.listings:
                        listing = item.offers.listings[0]
                        if hasattr(listing, 'price') and listing.price is not None:
                            product['price'] = listing.price.display_amount
                    
                    # Rating and Reviews
                    if hasattr(item, 'customer_reviews') and item.customer_reviews is not None:
                        if hasattr(item.customer_reviews, 'star_rating') and item.customer_reviews.star_rating is not None:
                            product['rating'] = item.customer_reviews.star_rating
                        if hasattr(item.customer_reviews, 'count') and item.customer_reviews.count is not None:
                            product['review_count'] = item.customer_reviews.count
                    
                    products.append(product)
                    logging.info(f"✓ Found: {product['title'][:50]}...")
                
                except Exception as e:
                    logging.warning(f"⚠️ Error parsing a single product item: {e}")
                    continue
            
            if not products:
                logging.warning(f"⚠️ No products could be parsed from the response for '{keyword}'")
                return []

            logging.info(f"✅ Retrieved and parsed {len(products)} products for '{keyword}'")
            return products
        
        except Exception as e:
            logging.error(f"❌ Amazon API search failed for '{keyword}': {e}")
            import traceback
            logging.error(traceback.format_exc())
            return []
    
    def get_product_details(self, asin: str) -> dict:
        """Get detailed information for a specific product by ASIN"""
        try:
            item_result = self.amazon.get_items(item_ids=[asin])
            
            if not item_result:
                return {}
            
            # Get items - it's a method call
            items_list = item_result.items() if callable(getattr(item_result, 'items', None)) else []
            
            if not items_list:
                return {}
            
            item = items_list[0]
            
            product = {
                'asin': item.asin if hasattr(item, 'asin') else '',
                'title': 'N/A',
                'url': item.detail_page_url if hasattr(item, 'detail_page_url') else '',
                'image_url': '',
                'price': '',
                'rating': '',
                'features': []
            }

            if hasattr(item, 'item_info') and item.item_info is not None:
                if hasattr(item.item_info, 'title') and item.item_info.title is not None:
                    product['title'] = item.item_info.title.display_value
                if hasattr(item, 'item_info') and item.item_info.features is not None:
                    product['features'] = item.item_info.features.display_values

            # Extract detailed info
            if hasattr(item, 'offers') and item.offers is not None and hasattr(item.offers, 'listings') and item.offers.listings:
                listing = item.offers.listings[0]
                if hasattr(listing, 'price') and listing.price is not None:
                    product['price'] = listing.price.display_amount
            
            if hasattr(item, 'images') and item.images is not None and hasattr(item.images, 'primary') and item.images.primary is not None:
                if hasattr(item.images.primary, 'large') and item.images.primary.large is not None:
                    product['image_url'] = item.images.primary.large.url

            return product
        
        except Exception as e:
            logging.error(f"❌ Failed to get product details for ASIN {asin}: {e}")
            return {}
