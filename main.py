#!/usr/bin/env python3
"""
Amazon Product Comparison to WordPress Auto Poster
Main entry point
"""
import os
import sys
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

from cerebras_client import CerebrasClient
from chat_zai_client import ChatZaiClient
from unified_ai_client import UnifiedAIClient
from amazon_api import AmazonProductAPI
from ai_generator import AIContentGenerator
from html_builder import HTMLBuilder
from wordpress_api import WordPressAPI
from site_config import SiteConfigManager, SiteConfig

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('amazon_poster.log')
    ]
)

class AmazonWPPoster:
    """Main application class"""
    
    def __init__(self, site_config: SiteConfig, env_file: str = '.env'):
        """Initialize with site configuration"""
        logging.info("🚀 Initializing Amazon WP Poster...")
        
        # Load environment variables
        load_dotenv(env_file)
        
        # Store site config
        self.site_config = site_config
        
        # Validate required env vars (only Amazon credentials now)
        self._validate_config()
        
        # Initialize components
        # Initialize ChatZai client (primary)
        chat_zai_url = os.getenv('CHAT_ZAI_API_URL', 'http://localhost:3001')
        self.chat_zai = ChatZaiClient(
            api_url=chat_zai_url,
            timeout=120,  # Increased timeout for long JSON responses
            max_retries=3
        )
        
        # Initialize Cerebras client (fallback)
        self.cerebras = CerebrasClient(
            api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
            model=os.getenv('CEREBRAS_MODEL', 'gpt-oss-120b')
        )
        
        # Create unified AI client
        self.ai_client = UnifiedAIClient(
            chat_zai_client=self.chat_zai,
            cerebras_client=self.cerebras
        )
        
        self.amazon = AmazonProductAPI(
            access_key=os.getenv('AMAZON_ACCESS_KEY'),
            secret_key=os.getenv('AMAZON_SECRET_KEY'),
            partner_tag=os.getenv('AMAZON_PARTNER_TAG'),
            region=os.getenv('AMAZON_REGION', 'us-east-1')
        )
        
        self.ai_generator = AIContentGenerator(self.ai_client)
        
        # Initialize WordPress with site config
        self.wordpress = WordPressAPI(
            site_url=site_config.site_url,
            username=site_config.username,
            app_password=site_config.app_password
        )
        
        # Post settings from site config
        self.post_author_id = site_config.author_id
        self.post_category_id = site_config.category_id
        self.post_status = site_config.status
        self.post_delay = int(os.getenv('POST_DELAY_SECONDS', '12'))
        
        logging.info(f"✅ Initialized for site: {site_config.name}")
        logging.info("✅ All components initialized successfully!")
    
    def _validate_config(self):
        """Validate required configuration"""
        required_vars = [
            'AMAZON_ACCESS_KEY', 'AMAZON_SECRET_KEY', 'AMAZON_PARTNER_TAG'
        ]
        
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            logging.error(f"❌ Missing required environment variables: {', '.join(missing)}")
            logging.error("Please copy .env.example to .env and fill in your credentials")
            sys.exit(1)
    
    def process_keyword(self, keyword: str) -> dict:
        """
        Process a single keyword and create WordPress post
        
        Args:
            keyword: Search keyword (e.g., "best laptop 2024")
        
        Returns:
            dict: Result with success status and post info
        """
        logging.info(f"\n{'='*60}")
        logging.info(f"🎯 Processing keyword: {keyword}")
        logging.info(f"{'='*60}")
        
        try:
            # Step 1: Search Amazon products
            logging.info("\n📦 Step 1: Searching Amazon products...")
            products = self.amazon.search_products(keyword, max_results=10)
            
            if not products:
                logging.warning(f"⚠️ No products found for: {keyword}")
                return {'success': False, 'error': 'No products found'}
            
            logging.info(f"✅ Found {len(products)} products")
            
            # Step 2: Generate AI content (PARALLEL - 3 waves, max 3 concurrent)
            logging.info("\n🤖 Step 2: Generating AI content in parallel...")
            
            # Generate ALL content in parallel (Intro, Badges, Guide, FAQs, Reviews)
            content = self.ai_generator.generate_all_content_parallel(keyword, products)
            
            intro = content['intro']
            badges_data = content['badges']
            buying_guide = content['guide']
            faqs = content['faqs']
            reviews_map = content['reviews']
            
            logging.info(f"✅ Generated reviews for {len(reviews_map)}/{len(products)} products")
            logging.info("✅ All AI content generated successfully!")
            
            # Step 3: Build HTML content
            logging.info("\n🏗️ Step 3: Building HTML content...")
            html_content = HTMLBuilder.build_full_post(
                keyword=keyword,
                intro=intro,
                products=products,
                badges_data=badges_data,
                reviews_map=reviews_map,
                buying_guide=buying_guide,
                faqs=faqs
            )
            
            # Step 4: Post to WordPress
            logging.info("\n📤 Step 4: Posting to WordPress...")
            
            title = f"Comparison: {keyword.title()}"
            
            category_ids = [self.post_category_id] if self.post_category_id > 0 else None
            
            result = self.wordpress.create_post(
                title=title,
                content=html_content,
                status=self.post_status,
                author_id=self.post_author_id,
                category_ids=category_ids,
                slug=keyword
            )
            
            logging.info(f"\n{'='*60}")
            logging.info(f"✅ SUCCESS! Post created for: {keyword}")
            logging.info(f"   Post ID: {result['id']}")
            logging.info(f"   Status: {result['status']}")
            logging.info(f"   URL: {result['url']}")
            logging.info(f"{'='*60}\n")
            
            return {
                'success': True,
                'keyword': keyword,
                'post_id': result['id'],
                'url': result['url'],
                'status': result['status']
            }
        
        except Exception as e:
            logging.error(f"\n❌ ERROR processing '{keyword}': {e}")
            return {
                'success': False,
                'keyword': keyword,
                'error': str(e)
            }
    
    def process_keywords_file(self, filepath: str):
        """
        Process all keywords from a text file
        
        Args:
            filepath: Path to keywords file (one keyword per line)
        """
        if not os.path.exists(filepath):
            logging.error(f"❌ Keywords file not found: {filepath}")
            return
        
        # Read keywords
        with open(filepath, 'r', encoding='utf-8') as f:
            keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not keywords:
            logging.warning(f"⚠️ No keywords found in {filepath}")
            return
        
        logging.info(f"\n📋 Found {len(keywords)} keyword(s) to process")
        logging.info(f"⏱️ Estimated time: ~{len(keywords) * 25 / 60:.1f} minutes (no delays between posts)")
        
        # Test WordPress connection
        if not self.wordpress.test_connection():
            logging.error("❌ WordPress connection failed. Please check credentials.")
            return
        
        # Process each keyword
        results = []
        remaining_keywords = keywords.copy()
        consecutive_failures = 0
        
        for idx, keyword in enumerate(keywords, 1):
            logging.info(f"\n📊 Progress: {idx}/{len(keywords)}")
            
            result = self.process_keyword(keyword)
            results.append(result)
            
            # Remove keyword from file if successfully posted
            if result['success']:
                consecutive_failures = 0  # Reset failure counter on success
                try:
                    remaining_keywords.remove(keyword)
                    with open(filepath, 'w', encoding='utf-8') as f:
                        for kw in remaining_keywords:
                            f.write(f"{kw}\n")
                    logging.info(f"✂️ Removed '{keyword}' from {filepath}")
                except Exception as e:
                    logging.warning(f"⚠️ Failed to remove keyword from file: {e}")
            else:
                # Increment failure counter
                consecutive_failures += 1
                logging.warning(f"⚠️ Consecutive failures: {consecutive_failures}/2")
                
                # Stop if 2 consecutive failures
                if consecutive_failures >= 2:
                    logging.error("\n" + "="*60)
                    logging.error("🛑 STOPPING: 2 consecutive failures detected!")
                    logging.error("Reason: Preventing waste of Amazon API calls")
                    logging.error("Action: Please check logs and fix issues before resuming")
                    logging.error("="*60 + "\n")
                    break
        
        # Summary
        logging.info(f"\n{'='*60}")
        logging.info("📊 PROCESSING COMPLETE - SUMMARY")
        logging.info(f"{'='*60}")
        
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        logging.info(f"✅ Successful: {len(successful)}/{len(results)}")
        logging.info(f"❌ Failed: {len(failed)}/{len(results)}")
        
        if successful:
            logging.info("\n✅ Successful posts:")
            for r in successful:
                logging.info(f"   - {r['keyword']}: {r['url']}")
        
        if failed:
            logging.info("\n❌ Failed keywords:")
            for r in failed:
                logging.info(f"   - {r['keyword']}: {r.get('error', 'Unknown error')}")
        
        logging.info(f"\n{'='*60}\n")
        
        # Print AI provider statistics
        if hasattr(self, 'ai_client'):
            self.ai_client.print_stats()
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'ai_client'):
            self.ai_client.close()
        logging.info("✅ Cleanup complete")

def main():
    """Main entry point"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║  Amazon Product Comparison → WordPress Auto Poster       ║
║  Powered by PA-API + Cerebras AI                         ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check for .env file
    if not os.path.exists('.env'):
        logging.error("❌ .env file not found!")
        logging.info("📝 Please copy .env.example to .env and configure your settings")
        sys.exit(1)
    
    # Load site configurations
    try:
        site_manager = SiteConfigManager('sites_config.json')
    except Exception as e:
        logging.error(f"❌ Failed to load site config: {e}")
        sys.exit(1)
    
    # Select site interactively
    site_config = site_manager.select_site_interactive()
    
    # Initialize application with selected site
    try:
        app = AmazonWPPoster(site_config)
    except Exception as e:
        logging.error(f"❌ Initialization failed: {e}")
        sys.exit(1)
    
    # Use keyword file from site config
    keywords_file = site_config.keyword_file
    
    if not os.path.exists(keywords_file):
        logging.error(f"❌ Keyword file not found: {keywords_file}")
        logging.info(f"📝 Please create {keywords_file} with one keyword per line")
        sys.exit(1)
    
    logging.info(f"📄 Using keyword file: {keywords_file}")
    
    try:
        app.process_keywords_file(keywords_file)
    finally:
        # Cleanup resources
        app.cleanup()

if __name__ == '__main__':
    main()
