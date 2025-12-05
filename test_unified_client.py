#!/usr/bin/env python3
"""
Test script for Unified AI Client
Tests ChatZai and Cerebras integration with fallback logic
"""
import os
from dotenv import load_dotenv
from chat_zai_client import ChatZaiClient
from cerebras_client import CerebrasClient
from unified_ai_client import UnifiedAIClient

def test_chat_zai_only():
    """Test ChatZai client only"""
    print("\n" + "="*60)
    print("TEST 1: ChatZai Client Only")
    print("="*60)
    
    client = ChatZaiClient(api_url=os.getenv('CHAT_ZAI_API_URL', 'http://localhost:3001'))
    
    # Health check
    print("\n1. Health Check...")
    healthy = client.health_check()
    print(f"   Status: {'✓ Healthy' if healthy else '✗ Unhealthy'}")
    
    if healthy:
        # Test generation
        print("\n2. Testing Generation...")
        try:
            response = client.generate(
                prompt="Write a 2-sentence intro about air fryers.",
                max_tokens=100
            )
            print(f"   ✓ Success! Generated {len(response)} characters")
            print(f"\n   Response preview:")
            print(f"   {response[:200]}...")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
    else:
        print("\n⚠ Skipping generation test - API not healthy")
    
    client.close()


def test_unified_client():
    """Test Unified AI Client with both providers"""
    print("\n" + "="*60)
    print("TEST 2: Unified AI Client (ChatZai + Cerebras)")
    print("="*60)
    
    load_dotenv()
    
    # Initialize clients
    chat_zai = ChatZaiClient(api_url=os.getenv('CHAT_ZAI_API_URL', 'http://localhost:3001'))
    cerebras = CerebrasClient(
        api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
        model=os.getenv('CEREBRAS_MODEL', 'llama3.1-8b')
    )
    
    unified = UnifiedAIClient(chat_zai, cerebras)
    
    # Test generation (will use ChatZai or fallback to Cerebras)
    print("\n1. Testing Generation with Auto-Fallback...")
    try:
        response = unified.generate(
            prompt="Write a 2-sentence intro about blenders.",
            max_tokens=100
        )
        print(f"   ✓ Success! Generated {len(response)} characters")
        print(f"\n   Response preview:")
        print(f"   {response[:200]}...")
    except Exception as e:
        print(f"   ✗ Failed: {e}")
    
    # Print statistics
    print("\n2. Usage Statistics:")
    unified.print_stats()
    
    unified.close()


def test_multiple_requests():
    """Test multiple requests to see fallback behavior"""
    print("\n" + "="*60)
    print("TEST 3: Multiple Requests (Fallback Testing)")
    print("="*60)
    
    load_dotenv()
    
    # Initialize clients
    chat_zai = ChatZaiClient(api_url=os.getenv('CHAT_ZAI_API_URL', 'http://localhost:3001'))
    cerebras = CerebrasClient(
        api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
        model=os.getenv('CEREBRAS_MODEL', 'llama3.1-8b')
    )
    
    unified = UnifiedAIClient(chat_zai, cerebras)
    
    prompts = [
        "Write about air fryers",
        "Write about blenders",
        "Write about coffee makers"
    ]
    
    print(f"\nTesting {len(prompts)} requests...\n")
    
    for i, prompt in enumerate(prompts, 1):
        print(f"Request {i}/{len(prompts)}: {prompt}...")
        try:
            response = unified.generate(prompt, max_tokens=50)
            print(f"   ✓ Success ({len(response)} chars)")
        except Exception as e:
            print(f"   ✗ Failed: {e}")
    
    # Final statistics
    print("\n" + "="*60)
    print("Final Statistics:")
    unified.print_stats()
    
    unified.close()


def main():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          Unified AI Client Test Suite                    ║
║  Tests ChatZai + Cerebras Integration                    ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check .env file
    if not os.path.exists('.env'):
        print("⚠ Warning: .env file not found")
        print("Using default configuration...\n")
    else:
        load_dotenv()
    
    try:
        # Test 1: ChatZai only
        test_chat_zai_only()
        
        # Test 2: Unified client
        test_unified_client()
        
        # Test 3: Multiple requests
        test_multiple_requests()
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
