#!/usr/bin/env python3
"""Test get post content to debug"""

import os
import sys
import re
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))

from wordpress_api import WordPressAPI

load_dotenv()

wp = WordPressAPI(
    site_url=os.getenv('WP_SITE_URL'),
    username=os.getenv('WP_USERNAME'),
    app_password=os.getenv('WP_APP_PASSWORD')
)

# Get post by slug
slug = "best-6-person-patio-dining-set"

response = wp.session.get(
    f"{wp.api_base}/posts",
    params={'slug': slug},
    auth=wp.session.auth
)

if response.status_code == 200:
    posts = response.json()
    if posts:
        post = posts[0]
        print(f"\n{'='*80}")
        print(f"POST: {post['title']['rendered']}")
        print(f"ID: {post['id']}")
        print(f"{'='*80}\n")
        
        # Get HTML content
        html = post['content']['rendered']
        
        # Find intro div
        intro_pattern = r'<div class="acap-intro">(.*?)</div>'
        intro_match = re.search(intro_pattern, html, re.DOTALL)
        
        if intro_match:
            print("✅ Found intro div:")
            print(f"{intro_match.group(1)[:200]}...")
        else:
            print("❌ No intro div found")
            print("\nFirst 500 chars of HTML:")
            print(html[:500])
            print("\n...")
            
            # Try to find any div
            div_pattern = r'<div[^>]*class="([^"]*)"[^>]*>'
            divs = re.findall(div_pattern, html[:1000])
            if divs:
                print(f"\nFound divs with classes: {divs[:5]}")
