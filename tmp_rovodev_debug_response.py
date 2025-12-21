#!/usr/bin/env python3
"""
Debug script to test ChatZai API response format
"""
import requests
import json

API_URL = "http://localhost:3001"

def test_simple_json_request():
    """Test if API returns only the answer or includes the prompt"""
    print("="*70)
    print("TEST 1: Simple JSON Request")
    print("="*70)
    
    prompt = '''Return ONLY this JSON, no explanations:
{"name": "John", "age": 30}'''
    
    print(f"\n📤 Sending prompt ({len(prompt)} chars):")
    print(f"'{prompt}'")
    
    response = requests.post(
        f"{API_URL}/ask",
        json={"prompt": prompt},
        timeout=30
    )
    
    data = response.json()
    answer = data.get('answer', '')
    
    print(f"\n📥 Response ({len(answer)} chars):")
    print(f"'{answer}'")
    
    # Check if prompt is included in answer
    if prompt in answer:
        print("\n❌ PROBLEM: API is returning the PROMPT inside the answer!")
        print("   This causes JSON parsing to fail.")
        
        # Find where actual answer starts
        prompt_end = answer.find(prompt) + len(prompt)
        actual_answer = answer[prompt_end:].strip()
        print(f"\n📝 Actual answer after prompt ({len(actual_answer)} chars):")
        print(f"'{actual_answer[:200]}'...")
    else:
        print("\n✅ GOOD: API returns only the answer, not the prompt")
        
    return answer

def test_json_generation():
    """Test JSON generation like badges"""
    print("\n" + "="*70)
    print("TEST 2: JSON Generation (like badges)")
    print("="*70)
    
    prompt = '''IMPORTANT: Output ONLY the JSON, no explanations, no thinking process.

Create badges for 2 products.

JSON FORMAT (no markdown, no extra text):
{"top_recommendation": {"asin": "B0XXX"}, "badges": [{"asin": "B0XXX", "badge": "Best Overall"}, {"asin": "B0YYY", "badge": "Best Value"}]}

Products:
- ASIN: B0TEST1, Title: "Test Product 1"
- ASIN: B0TEST2, Title: "Test Product 2"'''
    
    print(f"\n📤 Sending prompt ({len(prompt)} chars)")
    
    response = requests.post(
        f"{API_URL}/ask",
        json={"prompt": prompt},
        timeout=30
    )
    
    data = response.json()
    answer = data.get('answer', '')
    
    print(f"\n📥 Response ({len(answer)} chars):")
    print(f"First 300 chars: '{answer[:300]}'...")
    print(f"Last 300 chars: '...{answer[-300:]}'")
    
    # Try to find JSON in response
    print("\n🔍 Looking for JSON in response...")
    
    # Check if starts with prompt
    if answer.startswith("IMPORTANT: Output ONLY"):
        print("❌ Response starts with the prompt!")
        
        # Try to extract JSON after prompt
        try:
            json_start = answer.find('{')
            json_end = answer.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                extracted = answer[json_start:json_end]
                print(f"\n📦 Extracted JSON ({len(extracted)} chars):")
                print(extracted[:200] + "..." if len(extracted) > 200 else extracted)
                
                # Try to parse
                try:
                    parsed = json.loads(extracted)
                    print("\n✅ JSON is valid!")
                    print(f"Keys: {list(parsed.keys())}")
                except json.JSONDecodeError as e:
                    print(f"\n❌ JSON parse error: {e}")
                    print(f"Error at position {e.pos}: '{extracted[max(0,e.pos-20):e.pos+20]}'")
        except Exception as e:
            print(f"❌ Error extracting JSON: {e}")
    else:
        print("✅ Response does NOT start with prompt")
        
        # Try to parse directly
        try:
            parsed = json.loads(answer)
            print("✅ Response is valid JSON!")
            print(f"Keys: {list(parsed.keys())}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")

def test_with_system_prompt():
    """Test if system prompt affects response"""
    print("\n" + "="*70)
    print("TEST 3: With System Prompt Style")
    print("="*70)
    
    prompt = '''You are a helpful assistant. Return only valid JSON.

Create this JSON: {"status": "ok", "message": "test"}'''
    
    print(f"\n📤 Sending prompt with system-style instruction")
    
    response = requests.post(
        f"{API_URL}/ask",
        json={"prompt": prompt},
        timeout=30
    )
    
    data = response.json()
    answer = data.get('answer', '')
    
    print(f"\n📥 Response:")
    print(answer)
    
    if "You are a helpful assistant" in answer:
        print("\n❌ System prompt is included in response!")
    else:
        print("\n✅ System prompt is NOT included")

def main():
    print("\n🔬 ChatZai API Response Format Debug\n")
    
    try:
        test_simple_json_request()
        test_json_generation()
        test_with_system_prompt()
        
        print("\n" + "="*70)
        print("CONCLUSION:")
        print("="*70)
        print("""
If API returns the prompt inside the answer:
  → This is an API behavior issue
  → We need to strip the prompt from response
  → Update _extract_json() to handle this

If API returns clean answer:
  → Problem is in our prompt structure
  → Need to adjust how we format prompts
""")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
