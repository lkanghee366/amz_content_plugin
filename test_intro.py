#!/usr/bin/env python3
"""Test intro generation"""
import os
from dotenv import load_dotenv
from cerebras_client import CerebrasClient
from ai_generator import AIContentGenerator

load_dotenv()

print("=" * 70)
print("TESTING INTRO GENERATION (WITHOUT REASONING MODE)")
print("=" * 70)

cerebras = CerebrasClient(
    api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
    model=os.getenv('CEREBRAS_MODEL', 'gpt-oss-120b')
)

ai_gen = AIContentGenerator(cerebras)

keyword = "best coffee maker"
print(f"\nKeyword: {keyword}\n")

intro = ai_gen.generate_intro(keyword)

print("\n" + "=" * 70)
print("GENERATED INTRO:")
print("=" * 70)
print(intro)
print("=" * 70)
print(f"\nWord count: {len(intro.split())} words")
print("=" * 70)
