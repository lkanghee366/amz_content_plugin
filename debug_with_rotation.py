#!/usr/bin/env python3
"""
Debug: Test Buying Guide with rotation between requests
Simulate real workflow
"""
import os
import json
from dotenv import load_dotenv
from chat_zai_client import ChatZaiClient

load_dotenv()

print("\n" + "="*60)
print("Debug: Buying Guide with Rotation (Real Workflow)")
print("="*60)

# Initialize ChatZai client
client = ChatZaiClient(
    api_url=os.getenv('CHAT_ZAI_API_URL', 'http://localhost:3001'),
    timeout=120
)

keywords = [
    "best air fryer",
    "best blender", 
    "best 6 quart stainless steel stock pot"
]

for i, keyword in enumerate(keywords, 1):
    print(f"\n{'='*60}")
    print(f"Request {i}/3: {keyword}")
    print(f"{'='*60}")
    
    # Buying guide prompt
    prompt = (
        "Create a buying guide for product comparison.\n"
        "IMPORTANT: Return ONLY this exact JSON format (no markdown, no extra text):\n\n"
        '{"title": "Buying Guide: ' + keyword.title() + '", '
        '"sections": [{"heading": "Capacity & Size", "bullets": ["Consider your family size", "Check counter space"]}, '
        '{"heading": "Performance", "bullets": ["Look for higher wattage", "Check temperature range"]}]}\n\n'
        "Create 4-6 sections with 3-5 bullets each. No emojis, no prices.\n"
        f"Context: {keyword}"
    )
    
    try:
        response = client.generate(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.7
        )
        
        print(f"✅ Response: {len(response)} chars")
        
        # Validate JSON
        response_stripped = response.strip()
        if response_stripped.startswith('{') and response_stripped.endswith('}'):
            try:
                data = json.loads(response_stripped)
                print(f"✓ Valid JSON: {len(data.get('sections', []))} sections")
            except json.JSONDecodeError as e:
                print(f"✗ Invalid JSON at char {e.pos}")
                print(f"Response preview: {response[:500]}...")
        else:
            print(f"✗ Incomplete JSON (missing braces)")
            print(f"Starts with '{{': {response_stripped.startswith('{')}")
            print(f"Ends with '}}': {response_stripped.endswith('}')}")
        
        # Rotate context after success (like real workflow)
        if i < len(keywords):  # Don't rotate after last request
            print(f"🔄 Rotating context...")
            if client.rotate_context():
                print(f"✓ Context rotated")
                import time
                print(f"⏳ Waiting 3 seconds...")
                time.sleep(3)
            else:
                print(f"✗ Rotation failed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "="*60)
print("Test complete!")
print("="*60 + "\n")

client.close()
