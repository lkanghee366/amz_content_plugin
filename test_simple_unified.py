#!/usr/bin/env python3
"""
Simple test for Unified AI Client
"""
import os
from dotenv import load_dotenv
from chat_zai_client import ChatZaiClient
from cerebras_client import CerebrasClient
from unified_ai_client import UnifiedAIClient

load_dotenv()

print("\n" + "="*60)
print("Unified AI Client Test")
print("="*60)

# Initialize clients
print("\nInitializing clients...")
chat_zai = ChatZaiClient(
    api_url=os.getenv('CHAT_ZAI_API_URL', 'http://localhost:3001'),
    timeout=30
)

cerebras = CerebrasClient(
    api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
    model=os.getenv('CEREBRAS_MODEL', 'llama3.1-8b')
)

unified = UnifiedAIClient(chat_zai, cerebras)

# Test 1: Short generation
print("\n1. Testing short generation...")
try:
    response = unified.generate(
        prompt="Write one sentence about air fryers.",
        max_tokens=50
    )
    print(f"   ✓ Success!")
    print(f"   Response: {response}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 2: Medium generation
print("\n2. Testing medium generation...")
try:
    response = unified.generate(
        prompt="Write 2 sentences about blenders.",
        max_tokens=100
    )
    print(f"   ✓ Success!")
    print(f"   Response: {response}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Show statistics
print("\n3. Usage Statistics:")
unified.print_stats()

unified.close()

print("\n" + "="*60)
print("✅ Test Complete!")
print("="*60 + "\n")
