#!/usr/bin/env python3
"""
Debug Cerebras API - Test raw response
"""
import os
from dotenv import load_dotenv
from cerebras.cloud.sdk import Cerebras

load_dotenv()

print("="*60)
print("CEREBRAS API RAW TEST")
print("="*60)

# Load keys
keys_file = "cerebras_api_keys.txt"
with open(keys_file, 'r') as f:
    keys = [line.strip() for line in f if line.strip() and not line.startswith('#')]

print(f"\n✓ Loaded {len(keys)} API keys")

# Test with first key
api_key = keys[0]
print(f"✓ Testing with key: {api_key[:15]}...")

try:
    client = Cerebras(api_key=api_key)
    print("✓ Client initialized\n")
    
    # Simple test prompt
    test_prompt = "Write exactly 3 words only."
    
    print(f"📤 Sending prompt: '{test_prompt}'")
    print(f"📤 Model: gpt-oss-120b")
    print(f"📤 Max tokens: 50")
    print(f"📤 Stream: False\n")
    
    response = client.chat.completions.create(
        model="llama-3.3-70b",  # Try different model
        messages=[{"role": "user", "content": test_prompt}],
        max_tokens=50,
        temperature=0.7,
        stream=False
    )
    
    print("📦 Response received!")
    print(f"   Type: {type(response)}")
    print(f"   Has choices: {hasattr(response, 'choices')}")
    
    if hasattr(response, 'choices'):
        print(f"   Number of choices: {len(response.choices)}")
        
        if response.choices and len(response.choices) > 0:
            choice = response.choices[0]
            print(f"\n   Choice[0]:")
            print(f"      Type: {type(choice)}")
            print(f"      Has message: {hasattr(choice, 'message')}")
            
            if hasattr(choice, 'message'):
                message = choice.message
                print(f"      Message type: {type(message)}")
                print(f"      Has content: {hasattr(message, 'content')}")
                
                if hasattr(message, 'content'):
                    content = message.content
                    print(f"\n   ✅ CONTENT:")
                    print(f"      Length: {len(content) if content else 0} chars")
                    print(f"      Value: '{content}'")
                else:
                    print(f"   ❌ No 'content' attribute in message")
                    print(f"      Message attributes: {dir(message)}")
            else:
                print(f"   ❌ No 'message' attribute in choice")
                print(f"      Choice attributes: {dir(choice)}")
        else:
            print("   ❌ No choices returned!")
    else:
        print("   ❌ No 'choices' attribute!")
        print(f"      Response attributes: {dir(response)}")
    
    print("\n" + "="*60)
    print("Testing with gpt-oss-120b model:")
    print("="*60)
    
    response2 = client.chat.completions.create(
        model="gpt-oss-120b",
        messages=[{"role": "user", "content": test_prompt}],
        max_tokens=50,
        temperature=0.7,
        stream=False
    )
    
    print("📦 Response 2 received!")
    if hasattr(response2, 'choices') and response2.choices:
        content2 = response2.choices[0].message.content if hasattr(response2.choices[0].message, 'content') else None
        print(f"   Content: '{content2}'")
        print(f"   Length: {len(content2) if content2 else 0} chars")
    else:
        print("   ❌ No content in response 2")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()

print("\n" + "="*60)
