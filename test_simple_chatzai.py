#!/usr/bin/env python3
"""
Simple test for ChatZai API
"""
import requests
import json

API_URL = "http://localhost:3001"

print("\n" + "="*60)
print("Simple ChatZai API Test")
print("="*60)

# Test 1: Health Check
print("\n1. Health Check...")
try:
    response = requests.get(f"{API_URL}/health", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ✗ Failed: {e}")

# Test 2: Simple generation
print("\n2. Testing Generation...")
payload = {
    "prompt": "Say hello in one sentence",
    "maxTokens": 50
}

try:
    response = requests.post(f"{API_URL}/ask", json=payload, timeout=30)
    print(f"   Status: {response.status_code}")
    data = response.json()
    print(f"   Response keys: {list(data.keys())}")
    
    if 'answer' in data:
        print(f"   Answer: {data['answer'][:200]}")
    elif 'response' in data:
        print(f"   Response: {data['response'][:200]}")
    else:
        print(f"   Full data: {data}")
        
except Exception as e:
    print(f"   ✗ Failed: {e}")

print("\n" + "="*60 + "\n")
