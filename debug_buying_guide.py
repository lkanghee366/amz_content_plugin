#!/usr/bin/env python3
"""
Debug script for Buying Guide generation
Test if response is complete
"""
import os
import json
from dotenv import load_dotenv
from chat_zai_client import ChatZaiClient

load_dotenv()

print("\n" + "="*60)
print("Debug: Buying Guide Generation")
print("="*60)

# Initialize ChatZai client
client = ChatZaiClient(
    api_url=os.getenv('CHAT_ZAI_API_URL', 'http://localhost:3001'),
    timeout=120
)

# Test keyword
keyword = "best 6 quart stainless steel stock pot"

# Exact prompt from ai_generator.py (line 272-281)
prompt = (
    "Create a buying guide for product comparison.\n"
    "IMPORTANT: Return ONLY this exact JSON format (no markdown, no extra text):\n\n"
    '{"title": "Buying Guide: ' + keyword.title() + '", '
    '"sections": [{"heading": "Capacity & Size", "bullets": ["Consider your family size", "Check counter space"]}, '
    '{"heading": "Performance", "bullets": ["Look for higher wattage", "Check temperature range"]}]}\n\n'
    "Create 4-6 sections with 3-5 bullets each. No emojis, no prices.\n"
    f"Context: {keyword}"
)

print("\n📝 Prompt:")
print(f"   Length: {len(prompt)} characters")
print(f"   Preview: {prompt[:200]}...")

print("\n🌐 Sending request to ChatZai...")
print(f"   Max tokens: 2048")
print(f"   Timeout: 120s")

try:
    response = client.generate(
        prompt=prompt,
        max_tokens=2048,
        temperature=0.7
    )
    
    print(f"\n✅ Response received:")
    print(f"   Length: {len(response)} characters")
    print(f"\n📦 Full response:")
    print(response)
    
    # Check if complete JSON
    response_stripped = response.strip()
    print(f"\n🔍 JSON validation:")
    print(f"   Starts with '{{': {response_stripped.startswith('{')}")
    print(f"   Ends with '}}': {response_stripped.endswith('}')}")
    
    # Try to parse
    try:
        data = json.loads(response_stripped)
        print(f"   ✓ Valid JSON!")
        print(f"   Title: {data.get('title', 'N/A')}")
        print(f"   Sections: {len(data.get('sections', []))}")
        
        for i, section in enumerate(data.get('sections', []), 1):
            print(f"   - Section {i}: {section.get('heading', 'N/A')} ({len(section.get('bullets', []))} bullets)")
            
    except json.JSONDecodeError as e:
        print(f"   ✗ Invalid JSON: {e}")
        print(f"   Error at character: {e.pos}")
        print(f"   Context: ...{response_stripped[max(0, e.pos-50):e.pos+50]}...")
    
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "="*60 + "\n")

client.close()
