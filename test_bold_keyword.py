#!/usr/bin/env python3
"""Test bold keyword in intro"""

import sys
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

load_dotenv()

from cerebras_client import CerebrasClient
from ai_generator import AIContentGenerator

def test_bold_keyword():
    """Test that keyword gets bolded in intro"""
    
    # Initialize client
    cerebras = CerebrasClient(
        api_keys_file=os.getenv('CEREBRAS_API_KEYS_FILE'),
        model='qwen-3-235b-a22b-instruct-2507'
    )
    
    generator = AIContentGenerator(cerebras)
    
    # Test keyword
    keyword = "4 seater garden dining set sale"
    
    print(f"\n{'='*80}")
    print(f"TESTING BOLD KEYWORD IN INTRO")
    print(f"{'='*80}")
    print(f"Keyword: {keyword}")
    print(f"\n{'-'*80}\n")
    
    # Generate intro
    intro = generator.generate_intro(keyword)
    
    print(f"Generated Intro:")
    print(f"{intro}")
    print(f"\n{'-'*80}\n")
    
    # Check if keyword is bolded
    bolded_keyword = f"**{keyword}**"
    if bolded_keyword in intro:
        print(f"✅ SUCCESS: Keyword is bolded")
        print(f"   Found: {bolded_keyword}")
    else:
        # Check case-insensitive
        import re
        pattern = re.compile(f'\\*\\*{re.escape(keyword)}\\*\\*', re.IGNORECASE)
        if pattern.search(intro):
            print(f"✅ SUCCESS: Keyword is bolded (case variation)")
        else:
            print(f"❌ WARNING: Keyword not found as bolded")
            print(f"   Expected: {bolded_keyword}")
            # Check if keyword appears at all
            if keyword.lower() in intro.lower():
                print(f"   Note: Keyword appears in text but not bolded")
            else:
                print(f"   Note: Keyword doesn't appear in text at all")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    test_bold_keyword()
