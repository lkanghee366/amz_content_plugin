#!/usr/bin/env python3
"""Quick test intro with llama-3.3-70b"""
import os
from dotenv import load_dotenv
from cerebras_client import CerebrasClient
from ai_generator import AIContentGenerator

load_dotenv()

print("=" * 70)
print("TESTING INTRO WITH LLAMA-3.3-70B")
print("=" * 70)

cerebras = CerebrasClient(
    api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
    model=os.getenv('CEREBRAS_MODEL', 'gpt-oss-120b')  # Default for other tasks
)

ai_gen = AIContentGenerator(cerebras)

keyword = "best coffee maker"

for i in range(1, 4):
    print(f"\n[{i}/3] Generating intro with llama-3.3-70b...")
    try:
        intro = ai_gen.generate_intro(keyword)
        word_count = len(intro.split())
        print(f"✅ Success ({word_count} words)")
        print(f"Intro: {intro}")
        print("-" * 70)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
