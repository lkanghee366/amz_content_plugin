#!/usr/bin/env python3
"""
Quick test script - Test with ONE keyword only
"""
import os
import sys
from dotenv import load_dotenv

from cerebras_client import CerebrasClient
from amazon_api import AmazonProductAPI
from ai_generator import AIContentGenerator
from html_builder import HTMLBuilder
from wordpress_api import WordPressAPI

def quick_test():
    """Quick test with a single keyword"""
    
    # Load environment
    load_dotenv()
    
    # Test keyword
    TEST_KEYWORD = "best coffee maker"
    
    print(f"""
╔═══════════════════════════════════════════════════════════╗
║  Quick Test - Single Keyword                              ║
║  Keyword: {TEST_KEYWORD:<48}║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    try:
        # Initialize components
        print("🔧 Initializing components...")
        
        cerebras = CerebrasClient(
            api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
            model=os.getenv('CEREBRAS_MODEL', 'gpt-oss-120b')
        )
        print("  ✅ Cerebras client")
        
        amazon = AmazonProductAPI(
            access_key=os.getenv('AMAZON_ACCESS_KEY'),
            secret_key=os.getenv('AMAZON_SECRET_KEY'),
            partner_tag=os.getenv('AMAZON_PARTNER_TAG'),
            region=os.getenv('AMAZON_REGION', 'us-east-1')
        )
        print("  ✅ Amazon API")
        
        ai_gen = AIContentGenerator(cerebras)
        print("  ✅ AI Generator")
        
        wordpress = WordPressAPI(
            site_url=os.getenv('WP_SITE_URL'),
            username=os.getenv('WP_USERNAME'),
            app_password=os.getenv('WP_APP_PASSWORD')
        )
        print("  ✅ WordPress API")
        
        # Test WordPress connection
        print("\n🔌 Testing WordPress connection...")
        if not wordpress.test_connection():
            print("❌ WordPress connection failed!")
            return False
        
        # Step 1: Search products
        print(f"\n📦 Step 1: Searching Amazon products for '{TEST_KEYWORD}'...")
        products = amazon.search_products(TEST_KEYWORD, max_results=10)
        
        if not products:
            print(f"❌ No products found for '{TEST_KEYWORD}'")
            return False
        
        print(f"✅ Found {len(products)} products")
        for i, p in enumerate(products[:3], 1):
            print(f"   {i}. {p['title'][:60]}...")
        
        # Step 2: Generate AI content
        print("\n🤖 Step 2: Generating AI content...")
        
        print("  📝 Generating introduction...")
        intro = ai_gen.generate_intro(TEST_KEYWORD)
        print(f"  ✅ Intro: {intro[:80]}...")
        
        print("  🏷️ Generating badges...")
        badges_data = ai_gen.generate_badges(TEST_KEYWORD, products)
        print(f"  ✅ Badges: {len(badges_data['badges'])} badges, Top: {badges_data['top_recommendation']['asin']}")
        
        print("  📚 Generating buying guide...")
        buying_guide = ai_gen.generate_buying_guide(TEST_KEYWORD, products)
        print(f"  ✅ Buying guide: {len(buying_guide['sections'])} sections")
        
        print("  ❓ Generating FAQs...")
        faqs = ai_gen.generate_faqs(TEST_KEYWORD, products)
        print(f"  ✅ FAQs: {len(faqs)} questions")
        
        # Step 3: Build HTML
        print("\n🏗️ Step 3: Building HTML content...")
        html_content = HTMLBuilder.build_full_post(
            keyword=TEST_KEYWORD,
            intro=intro,
            products=products,
            badges_data=badges_data,
            buying_guide=buying_guide,
            faqs=faqs
        )
        print(f"✅ HTML built: {len(html_content)} characters")
        
        # Step 4: Ask before posting
        print("\n" + "="*60)
        print("📋 Preview:")
        print("="*60)
        print(f"Title: Comparison: {TEST_KEYWORD.title()}")
        print(f"Status: {os.getenv('POST_STATUS', 'draft')}")
        print(f"Category ID: {os.getenv('POST_CATEGORY_ID', '0')}")
        print(f"Author ID: {os.getenv('POST_AUTHOR_ID', '2')}")
        print(f"Content length: {len(html_content)} chars")
        print("="*60)
        
        response = input("\n✋ Post to WordPress? (yes/no): ").strip().lower()
        
        if response != 'yes':
            print("⏸️ Skipped posting. Test complete!")
            return True
        
        # Step 4: Post to WordPress
        print("\n📤 Step 4: Posting to WordPress...")
        
        category_id = int(os.getenv('POST_CATEGORY_ID', '0'))
        category_ids = [category_id] if category_id > 0 else None
        
        result = wordpress.create_post(
            title=f"Comparison: {TEST_KEYWORD.title()}",
            content=html_content,
            status=os.getenv('POST_STATUS', 'draft'),
            author_id=int(os.getenv('POST_AUTHOR_ID', '2')),
            category_ids=category_ids,
            slug=TEST_KEYWORD
        )
        
        print("\n" + "="*60)
        print("✅ SUCCESS!")
        print("="*60)
        print(f"Post ID: {result['id']}")
        print(f"Status: {result['status']}")
        print(f"URL: {result['url']}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = quick_test()
    sys.exit(0 if success else 1)
