"""
Test posting INFO article to WordPress
Site: MountainTidesWine (site 3)
Keyword: "how to cook beef ribs"
"""
import sys
import json
from dotenv import load_dotenv
from wordpress_api import WordPressAPI
from html_builder import HTMLBuilder
from site_config import SiteConfigManager

# Load environment
load_dotenv()

def test_post_info():
    """Test posting INFO article to WordPress"""
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing INFO Article Post to WordPress")
    print(f"{'='*60}\n")
    
    # Load generated content
    print("📂 Loading generated content...")
    with open('test_info_article_output.json', 'r', encoding='utf-8') as f:
        article_data = json.load(f)
    
    keyword = "how to cook beef ribs"
    print(f"Keyword: {keyword}")
    
    # Load site config
    print("\n🔧 Loading site configuration...")
    config_manager = SiteConfigManager('sites_config.json')
    site_config = config_manager.get_site(3)  # MountainTidesWine
    
    if not site_config:
        print("❌ Site 3 not found!")
        sys.exit(1)
    
    print(f"Site: {site_config.name}")
    print(f"URL: {site_config.site_url}")
    print(f"Info Category ID: {site_config.info_category_id}")
    
    # Build HTML
    print("\n🏗️ Building HTML content...")
    html_content = HTMLBuilder.build_info_article(keyword, article_data)
    
    print(f"HTML length: {len(html_content)} chars")
    print(f"\nPreview (first 500 chars):")
    print("-" * 60)
    print(html_content[:500])
    print("-" * 60)
    
    # Generate title (capitalize keyword)
    title = keyword.title()
    print(f"\nTitle: {title}")
    
    # Connect to WordPress
    print(f"\n🔌 Connecting to WordPress...")
    wp_api = WordPressAPI(
        site_url=site_config.site_url,
        username=site_config.username,
        app_password=site_config.app_password
    )
    
    # Create post
    post_status = 'draft'
    print(f"Status: {post_status} (forced draft for testing)")
    print(f"Category: {[site_config.info_category_id] if site_config.info_category_id else []}")
    
    try:
        print("\n⚠️ Testing post creation WITH category but draft status...")
        result = wp_api.create_post(
            title=title,
            content=html_content,
            status=post_status,
            author_id=site_config.author_id,
            category_ids=[site_config.info_category_id] if site_config.info_category_id else None
        )
        
        print(f"\n{'='*60}")
        print("✅ POST SUCCESSFUL")
        print(f"{'='*60}\n")
        print(f"Post ID: {result['id']}")
        print(f"Title: {result['title']['rendered']}")
        print(f"Status: {result['status']}")
        print(f"URL: {result['link']}")
        print()
        
        # Save result
        with open('test_info_post_result.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("💾 Full result saved to: test_info_post_result.json\n")
        
    except Exception as e:
        print(f"\n❌ Error posting to WordPress: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_post_info()
