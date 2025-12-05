#!/usr/bin/env python3
"""Test Cerebras key caching mechanism"""
import os
from cerebras_client import CerebrasClient

print("=" * 70)
print("TESTING CEREBRAS KEY CACHING")
print("=" * 70)

# Clean cache first
cache_file = "cerebras_key_cache.txt"
if os.path.exists(cache_file):
    os.remove(cache_file)
    print(f"🗑️ Removed old cache file")

# Test 1: First initialization (no cache)
print("\n[TEST 1] First initialization (no cache)")
client1 = CerebrasClient(
    api_keys_file='cerebras_api_keys.txt',
    model='gpt-oss-120b'
)
print(f"   Current key index: #{client1.key_index}")
print(f"   Cache file exists: {os.path.exists(cache_file)}")

if os.path.exists(cache_file):
    with open(cache_file, 'r') as f:
        cached = f.read().strip()
    print(f"   Cache content: {cached}")

# Test 2: Second initialization (should load from cache)
print("\n[TEST 2] Second initialization (should load cached key)")
client2 = CerebrasClient(
    api_keys_file='cerebras_api_keys.txt',
    model='gpt-oss-120b'
)
print(f"   Current key index: #{client2.key_index}")

# Test 3: Generate content (should update cache)
print("\n[TEST 3] Generate content (cache should update after success)")
try:
    response = client2.generate(
        prompt="Say 'Hello' in one word.",
        max_tokens=10,
        temperature=0.5,
        stream=False
    )
    print(f"   Response: {response[:50]}...")
    
    with open(cache_file, 'r') as f:
        cached_after = f.read().strip()
    print(f"   Cache after generation: {cached_after}")
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "=" * 70)
print("✅ Cache test complete!")
print("=" * 70)
