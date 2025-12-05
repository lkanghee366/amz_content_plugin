#!/usr/bin/env python3
"""
Test script to validate the entire workflow
"""
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_env_config():
    """Test environment configuration"""
    print("🔍 Testing environment configuration...")
    
    required_vars = {
        'WP_SITE_URL': 'WordPress site URL',
        'WP_USERNAME': 'WordPress username',
        'WP_APP_PASSWORD': 'WordPress app password',
        'AMAZON_ACCESS_KEY': 'Amazon access key',
        'AMAZON_SECRET_KEY': 'Amazon secret key',
        'AMAZON_PARTNER_TAG': 'Amazon partner tag'
    }
    
    missing = []
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if not value:
            print(f"  ❌ Missing: {var} ({desc})")
            missing.append(var)
        else:
            print(f"  ✅ {var}: {value[:20]}..." if len(value) > 20 else f"  ✅ {var}: {value}")
    
    # Check numeric values
    try:
        author_id = int(os.getenv('POST_AUTHOR_ID', '0'))
        category_id = int(os.getenv('POST_CATEGORY_ID', '0'))
        delay = int(os.getenv('POST_DELAY_SECONDS', '12'))
        print(f"  ✅ POST_AUTHOR_ID: {author_id}")
        print(f"  ✅ POST_CATEGORY_ID: {category_id}")
        print(f"  ✅ POST_DELAY_SECONDS: {delay}")
    except ValueError as e:
        print(f"  ❌ Error parsing numeric config: {e}")
        missing.append('numeric_config')
    
    if missing:
        print(f"\n❌ Configuration incomplete. Missing: {', '.join(missing)}")
        return False
    
    print("✅ Environment configuration OK\n")
    return True

def test_cerebras_keys():
    """Test Cerebras API keys file"""
    print("🔍 Testing Cerebras API keys...")
    
    keys_file = os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt')
    
    if not os.path.exists(keys_file):
        print(f"  ❌ File not found: {keys_file}")
        return False
    
    with open(keys_file, 'r', encoding='utf-8') as f:
        keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not keys:
        print(f"  ❌ No API keys found in {keys_file}")
        return False
    
    print(f"  ✅ Found {len(keys)} API key(s)")
    for i, key in enumerate(keys[:3], 1):
        print(f"     Key #{i}: {key[:10]}...{key[-10:]}")
    
    if len(keys) > 3:
        print(f"     ... and {len(keys) - 3} more")
    
    print("✅ Cerebras API keys OK\n")
    return True

def test_keywords():
    """Test keywords file"""
    print("🔍 Testing keywords file...")
    
    if not os.path.exists('keywords.txt'):
        print("  ❌ keywords.txt not found")
        return False
    
    with open('keywords.txt', 'r', encoding='utf-8') as f:
        keywords = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    if not keywords:
        print("  ❌ No keywords found")
        return False
    
    print(f"  ✅ Found {len(keywords)} keyword(s)")
    for kw in keywords[:5]:
        print(f"     - {kw}")
    
    if len(keywords) > 5:
        print(f"     ... and {len(keywords) - 5} more")
    
    print("✅ Keywords OK\n")
    return True

def test_cerebras_client():
    """Test Cerebras client initialization"""
    print("🔍 Testing Cerebras client...")
    
    try:
        from cerebras_client import CerebrasClient
        
        keys_file = os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt')
        model = os.getenv('CEREBRAS_MODEL', 'gpt-oss-120b')
        
        client = CerebrasClient(api_keys_file=keys_file, model=model)
        print(f"  ✅ Client initialized with model: {model}")
        print(f"  ✅ Using {len(client.api_keys)} API key(s)")
        print("✅ Cerebras client OK\n")
        return True, client
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("❌ Cerebras client FAILED\n")
        return False, None

def test_amazon_api():
    """Test Amazon API initialization"""
    print("🔍 Testing Amazon API...")
    
    try:
        from amazon_api import AmazonProductAPI
        
        api = AmazonProductAPI(
            access_key=os.getenv('AMAZON_ACCESS_KEY'),
            secret_key=os.getenv('AMAZON_SECRET_KEY'),
            partner_tag=os.getenv('AMAZON_PARTNER_TAG'),
            region=os.getenv('AMAZON_REGION', 'us-east-1')
        )
        print(f"  ✅ Amazon API initialized for region: {api.country}")
        print("✅ Amazon API OK\n")
        return True, api
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("❌ Amazon API FAILED\n")
        return False, None

def test_wordpress_api():
    """Test WordPress API connection"""
    print("🔍 Testing WordPress API...")
    
    try:
        from wordpress_api import WordPressAPI
        
        wp = WordPressAPI(
            site_url=os.getenv('WP_SITE_URL'),
            username=os.getenv('WP_USERNAME'),
            app_password=os.getenv('WP_APP_PASSWORD')
        )
        
        if wp.test_connection():
            print("✅ WordPress API OK\n")
            return True, wp
        else:
            print("❌ WordPress API connection FAILED\n")
            return False, None
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("❌ WordPress API FAILED\n")
        return False, None

def test_ai_generation(cerebras_client):
    """Test AI content generation with a simple prompt"""
    print("🔍 Testing AI generation...")
    
    try:
        from ai_generator import AIContentGenerator
        
        generator = AIContentGenerator(cerebras_client)
        
        # Test with simple prompt
        print("  Testing intro generation...")
        intro = generator.generate_intro("test product")
        
        if intro and len(intro) > 20:
            print(f"  ✅ Generated intro ({len(intro)} chars): {intro[:100]}...")
            print("✅ AI generation OK\n")
            return True
        else:
            print(f"  ❌ Generated intro too short or empty")
            return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        print("❌ AI generation FAILED\n")
        return False

def main():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║  Amazon WP Poster - Workflow Test                        ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # Test 1: Environment
    results['env'] = test_env_config()
    if not results['env']:
        print("⚠️  Fix .env file before continuing\n")
        return False
    
    # Test 2: Cerebras keys
    results['cerebras_keys'] = test_cerebras_keys()
    
    # Test 3: Keywords
    results['keywords'] = test_keywords()
    
    # Test 4: Cerebras client
    cerebras_ok, cerebras_client = test_cerebras_client()
    results['cerebras_client'] = cerebras_ok
    
    # Test 5: Amazon API
    amazon_ok, amazon_api = test_amazon_api()
    results['amazon_api'] = amazon_ok
    
    # Test 6: WordPress API
    wp_ok, wp_api = test_wordpress_api()
    results['wordpress_api'] = wp_ok
    
    # Test 7: AI Generation (only if Cerebras client OK)
    if cerebras_ok and cerebras_client:
        results['ai_generation'] = test_ai_generation(cerebras_client)
    else:
        results['ai_generation'] = False
        print("⚠️  Skipping AI generation test (Cerebras client not initialized)\n")
    
    # Summary
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  Test Summary                                             ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}  {test_name.replace('_', ' ').title()}")
    
    print("")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("🎉 All tests passed! Ready to run main.py")
        return True
    else:
        failed = [name for name, passed in results.items() if not passed]
        print(f"⚠️  Some tests failed: {', '.join(failed)}")
        print("   Please fix the issues before running main.py")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
