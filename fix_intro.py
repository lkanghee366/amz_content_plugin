#!/usr/bin/env python3
"""
Fix intro for existing WordPress posts
Reads keywords from fixkey.txt, finds posts, regenerates intro, updates posts
"""

import os
import sys
import logging
import re
import time
from typing import Optional
from dotenv import load_dotenv

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from wordpress_api import WordPressAPI
from cerebras_client import CerebrasClient
from ai_generator import AIContentGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_intro.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class IntroFixer:
    """Fix intro for existing WordPress posts"""
    
    def __init__(self, wp_client: WordPressAPI, ai_generator: AIContentGenerator):
        self.wp = wp_client
        self.ai = ai_generator
    
    def get_post_by_slug(self, slug: str) -> Optional[dict]:
        """
        Get WordPress post by slug
        
        Args:
            slug: Post slug (usually same as keyword)
            
        Returns:
            Post data dict or None if not found
        """
        try:
            logging.info(f"🔍 Searching for post with slug: {slug}")
            
            # WordPress REST API: GET /wp/v2/posts?slug={slug}
            response = self.wp.session.get(
                f"{self.wp.api_base}/posts",
                params={'slug': slug},
                auth=self.wp.session.auth
            )
            
            if response.status_code == 200:
                posts = response.json()
                if posts and len(posts) > 0:
                    post = posts[0]
                    logging.info(f"✅ Found post ID: {post['id']} - {post['title']['rendered']}")
                    return post
                else:
                    logging.warning(f"⚠️ No post found with slug: {slug}")
                    return None
            else:
                logging.error(f"❌ Failed to search posts: {response.status_code}")
                return None
                
        except Exception as e:
            logging.error(f"❌ Error getting post by slug: {e}")
            return None
    
    def extract_intro_from_html(self, html: str) -> Optional[str]:
        """
        Extract intro text from HTML content
        
        Args:
            html: Full HTML content
            
        Returns:
            Intro text or None if not found
        """
        # First try: Look for <div class="acap-intro">...</div>
        pattern = r'<div class="acap-intro">(.*?)</div>'
        match = re.search(pattern, html, re.DOTALL)
        
        if match:
            intro = match.group(1).strip()
            return intro
        
        # Fallback: Look for first <p> tag (old broken intro)
        p_pattern = r'<p>(.*?)</p>'
        p_match = re.search(p_pattern, html, re.DOTALL)
        
        if p_match:
            intro = p_match.group(1).strip()
            logging.info(f"📄 Found intro in <p> tag (old format)")
            return intro
        
        logging.warning("⚠️ Could not find intro in HTML")
        return None
    
    def replace_intro_in_html(self, html: str, new_intro: str) -> str:
        """
        Replace intro in HTML content
        
        Args:
            html: Original HTML content
            new_intro: New intro text (plain text, will be wrapped in p tag)
            
        Returns:
            Updated HTML content
        """
        # Wrap new intro in <p> tag (matching current format)
        new_intro_html = f'<p>{new_intro}</p>\n'
        
        # Try to replace <div class="acap-intro">...</div> if exists
        div_pattern = r'<div class="acap-intro">.*?</div>'
        if re.search(div_pattern, html, re.DOTALL):
            updated_html = re.sub(div_pattern, new_intro_html.strip(), html, count=1, flags=re.DOTALL)
            logging.info("✅ Replaced intro in <div class='acap-intro'> with <p>")
            return updated_html
        
        # Replace first <p> tag (current format)
        p_pattern = r'<p>.*?</p>'
        if re.search(p_pattern, html, re.DOTALL):
            updated_html = re.sub(p_pattern, new_intro_html.strip(), html, count=1, flags=re.DOTALL)
            logging.info("✅ Replaced first <p> tag with new intro")
            return updated_html
        
        # Last resort: just prepend new intro
        logging.warning("⚠️ Could not find old intro, prepending new intro")
        return new_intro_html + html
    
    def update_post_content(self, post_id: int, new_content: str) -> bool:
        """
        Update WordPress post content
        
        Args:
            post_id: WordPress post ID
            new_content: New HTML content
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logging.info(f"📝 Updating post ID: {post_id}")
            
            # WordPress REST API: POST /wp/v2/posts/{id}
            response = self.wp.session.post(
                f"{self.wp.api_base}/posts/{post_id}",
                json={'content': new_content},
                auth=self.wp.session.auth
            )
            
            if response.status_code == 200:
                logging.info(f"✅ Post updated successfully")
                return True
            else:
                logging.error(f"❌ Failed to update post: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logging.error(f"❌ Error updating post: {e}")
            return False
    
    def fix_post_intro(self, keyword: str) -> dict:
        """
        Fix intro for a single post
        
        Args:
            keyword: Keyword (same as post slug)
            
        Returns:
            Result dict with status and details
        """
        result = {
            'keyword': keyword,
            'success': False,
            'post_id': None,
            'old_intro': None,
            'new_intro': None,
            'error': None
        }
        
        try:
            # Step 1: Find post by slug
            slug = keyword.lower().replace(' ', '-')
            post = self.get_post_by_slug(slug)
            
            if not post:
                result['error'] = 'Post not found'
                return result
            
            result['post_id'] = post['id']
            
            # Step 2: Extract current HTML content
            html_content = post['content']['rendered']
            
            # Step 3: Extract old intro
            old_intro = self.extract_intro_from_html(html_content)
            if old_intro:
                result['old_intro'] = old_intro[:100] + '...' if len(old_intro) > 100 else old_intro
                logging.info(f"📄 Old intro: {result['old_intro']}")
            
            # Step 4: Generate new intro (with retry)
            logging.info(f"🤖 Generating new intro for: {keyword}")
            
            max_retries = 2
            retry_delay = 3  # seconds
            new_intro = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    new_intro = self.ai.generate_intro(keyword)
                    break  # Success, exit retry loop
                except Exception as gen_error:
                    if attempt < max_retries:
                        logging.warning(f"⚠️ Attempt {attempt} failed: {gen_error}. Retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        logging.error(f"❌ All {max_retries} attempts failed for intro generation")
                        raise  # Re-raise last exception
            
            if not new_intro:
                result['error'] = 'Failed to generate intro after retries'
                return result
            
            result['new_intro'] = new_intro
            
            # Step 5: Replace intro in HTML
            updated_html = self.replace_intro_in_html(html_content, new_intro)
            
            # Step 6: Update post
            success = self.update_post_content(post['id'], updated_html)
            result['success'] = success
            
            if success:
                logging.info(f"✅ Successfully fixed intro for: {keyword}")
            
            return result
            
        except Exception as e:
            logging.error(f"❌ Error fixing intro for {keyword}: {e}")
            result['error'] = str(e)
            return result


def load_keywords_from_file(filepath: str) -> list:
    """Load keywords from fixkey.txt"""
    keywords = []
    
    if not os.path.exists(filepath):
        logging.error(f"❌ File not found: {filepath}")
        return keywords
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                keywords.append(line)
    
    logging.info(f"📋 Loaded {len(keywords)} keywords from {filepath}")
    return keywords


def main():
    """Main function"""
    load_dotenv()
    
    print("\n" + "="*80)
    print("🔧 INTRO FIXER - Fix intro for existing WordPress posts")
    print("="*80 + "\n")
    
    # Validate environment variables
    required_env = {
        'WP_SITE_URL': os.getenv('WP_SITE_URL'),
        'WP_USERNAME': os.getenv('WP_USERNAME'),
        'WP_APP_PASSWORD': os.getenv('WP_APP_PASSWORD')
    }
    
    missing = [k for k, v in required_env.items() if not v]
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please check your .env file")
        return
    
    # Cerebras API keys file (default to local file)
    cerebras_keys_file = os.getenv('CEREBRAS_API_KEYS_FILE', 'cerebras_api_keys.txt')
    if not os.path.exists(cerebras_keys_file):
        print(f"❌ Cerebras API keys file not found: {cerebras_keys_file}")
        return
    
    # Initialize clients
    wp_client = WordPressAPI(
        site_url=required_env['WP_SITE_URL'],
        username=required_env['WP_USERNAME'],
        app_password=required_env['WP_APP_PASSWORD']
    )
    
    cerebras_client = CerebrasClient(
        api_keys_file=cerebras_keys_file,
        model='qwen-3-235b-a22b-instruct-2507'
    )
    
    ai_generator = AIContentGenerator(cerebras_client)
    
    fixer = IntroFixer(wp_client, ai_generator)
    
    # Load keywords to fix
    fixkey_file = 'fixkey.txt'
    keywords = load_keywords_from_file(fixkey_file)
    
    if not keywords:
        print("⚠️ No keywords found in fixkey.txt")
        print("Please add keywords (one per line) and try again.")
        return
    
    print(f"Found {len(keywords)} posts to fix:\n")
    for i, kw in enumerate(keywords, 1):
        print(f"  {i}. {kw}")
    
    print(f"\n{'-'*80}\n")
    
    # Process each keyword
    results = []
    for i, keyword in enumerate(keywords, 1):
        print(f"\n[{i}/{len(keywords)}] Processing: {keyword}")
        print("-" * 60)
        
        result = fixer.fix_post_intro(keyword)
        results.append(result)
        
        if result['success']:
            print(f"✅ SUCCESS")
            print(f"   Post ID: {result['post_id']}")
            print(f"   New intro: {result['new_intro'][:80]}...")
        else:
            print(f"❌ FAILED: {result['error']}")
        
        print()
    
    # Summary
    print("\n" + "="*80)
    print("📊 SUMMARY")
    print("="*80 + "\n")
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if failed:
        print("\nFailed keywords:")
        for r in failed:
            print(f"  - {r['keyword']}: {r['error']}")
    
    print("\n" + "="*80 + "\n")


if __name__ == '__main__':
    main()
