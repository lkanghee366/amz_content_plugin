#!/usr/bin/env python3
"""
See full response from ChatZai for badge generation
"""
import requests
import json

API_URL = "http://localhost:3001"

# Sample products (like real workflow)
products = [
    {
        'asin': 'B0TEST1',
        'title': 'Test Slow Cooker 1 - 6 Quart Programmable',
        'price': '$49.99',
        'brand': 'TestBrand',
        'features': ['6 quart capacity', 'Programmable timer', 'Keep warm function']
    },
    {
        'asin': 'B0TEST2',
        'title': 'Test Slow Cooker 2 - 8 Quart Digital',
        'price': '$69.99',
        'brand': 'TestBrand2',
        'features': ['8 quart capacity', 'Digital display', 'Auto shutoff']
    }
]

keyword = "the best slow cooker roast"

# Build compact list
compact = []
all_asins = []
for product in products:
    title = product['title']
    if len(title) > 80:
        title = title[:77] + '…'
    
    compact.append({
        'asin': product['asin'],
        'title': title,
        'price': product['price'],
        'brand': product.get('brand', ''),
        'features': product['features'] if product['features'] else []
    })
    all_asins.append(product['asin'])

# Build prompt (EXACTLY like ai_generator.py)
prompt = (
    "IMPORTANT: Output ONLY the JSON, no explanations, no thinking process.\n\n"
    "Create product badges for ALL products in the comparison article.\n\n"
    "CRITICAL REQUIREMENTS:\n"
    "1. You MUST create a badge for EVERY SINGLE product listed below\n"
    "2. Each badge must be a purposeful 2-3 word phrase that clearly reflects the product's unique strength, use case, or standout feature\n"
    "3. Avoid generic labels (e.g., 'Best overall', 'Great value') unless they truly match the product; make badges feel human and specific\n"
    "4. Pick exactly ONE product as top recommendation (editor's choice)\n"
    "5. Draw inspiration from the brand, title, and feature list for each product when crafting the badge\n"
    "6. Examples of acceptable style: \"Rain-Ready Seating\", \"Compact Bistro Choice\", \"Premium Teak Craft\", \"Budget-Friendly Lounger\"\n\n"
    f"MANDATORY: Return badges for ALL {len(compact)} products.\n\n"
    "JSON FORMAT (no markdown, no extra text):\n"
    '{"top_recommendation": {"asin": "ACTUAL_ASIN"}, "badges": ['
    '{"asin": "ASIN1", "badge": "Best overall"}, {"asin": "ASIN2", "badge": "Best value"}, ...]}\n\n'
    f"ALL ASINs that MUST be included:\n{', '.join(all_asins)}\n\n"
    f"Context: {keyword}\n"
    f"Products: {json.dumps(compact, ensure_ascii=False)}"
)

print("="*80)
print("SENDING BADGE GENERATION REQUEST")
print("="*80)
print(f"\n📤 Prompt length: {len(prompt)} chars")
print(f"\n📤 First 500 chars of prompt:")
print(prompt[:500])
print("\n...")
print(f"\n📤 Last 300 chars of prompt:")
print(prompt[-300:])

print("\n" + "="*80)
print("SENDING TO API...")
print("="*80)

response = requests.post(
    f"{API_URL}/ask",
    json={"prompt": prompt},
    timeout=60
)

data = response.json()
answer = data.get('answer', '')

print(f"\n✅ Response received: {len(answer)} chars")
print(f"⚡ Duration: {data.get('duration', 'N/A')}ms")
print(f"🔧 Worker: {data.get('workerPort', 'N/A')}")

print("\n" + "="*80)
print("FULL RESPONSE (COMPLETE):")
print("="*80)
print(answer)
print("="*80)

# Try to find JSON
print("\n" + "="*80)
print("ANALYZING RESPONSE:")
print("="*80)

# Check if starts with prompt
if answer.startswith("IMPORTANT: Output ONLY"):
    print("❌ Response STARTS with the prompt text!")
    
    # Find first {
    json_start = answer.find('{')
    if json_start == -1:
        print("❌ No JSON object found in response!")
    else:
        print(f"✅ JSON object found at position {json_start}")
        print(f"   Text before JSON: '{answer[:json_start]}'")
        
        # Check if it's part of the prompt
        if json_start > 500:  # Prompt is long
            print(f"   → This is likely the echoed prompt (too far: {json_start} chars)")
        else:
            print(f"   → JSON might be close to start")
else:
    print("✅ Response does NOT start with prompt")
    if answer.startswith('{'):
        print("✅ Response starts directly with JSON")
    elif answer.startswith('['):
        print("✅ Response starts directly with JSON array")
    else:
        print(f"⚠️ Response starts with: '{answer[:100]}'")

# Save to file for inspection
with open('tmp_rovodev_badge_response.txt', 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("PROMPT:\n")
    f.write("="*80 + "\n")
    f.write(prompt)
    f.write("\n\n")
    f.write("="*80 + "\n")
    f.write("RESPONSE:\n")
    f.write("="*80 + "\n")
    f.write(answer)

print(f"\n💾 Full response saved to: tmp_rovodev_badge_response.txt")
