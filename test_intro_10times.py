#!/usr/bin/env python3
"""Test intro generation 10 times and save to file"""
import os
from dotenv import load_dotenv
from cerebras_client import CerebrasClient
from ai_generator import AIContentGenerator

load_dotenv()

print("=" * 70)
print("TESTING INTRO GENERATION - 10 TIMES")
print("=" * 70)

cerebras = CerebrasClient(
    api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
    model=os.getenv('CEREBRAS_MODEL', 'gpt-oss-120b')
)

ai_gen = AIContentGenerator(cerebras)

keyword = "best coffee maker"
results = []

for i in range(1, 11):
    print(f"\n[{i}/10] Generating intro for '{keyword}'...")
    try:
        intro = ai_gen.generate_intro(keyword)
        word_count = len(intro.split())
        results.append({
            'run': i,
            'intro': intro,
            'word_count': word_count,
            'success': True
        })
        print(f"  ✅ Success ({word_count} words)")
    except Exception as e:
        results.append({
            'run': i,
            'intro': '',
            'error': str(e),
            'success': False
        })
        print(f"  ❌ Error: {e}")

# Save to file
output_file = "intro_test_results.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 70 + "\n")
    f.write("INTRO GENERATION TEST - 10 RUNS\n")
    f.write(f"Keyword: {keyword}\n")
    f.write("=" * 70 + "\n\n")
    
    for result in results:
        f.write(f"{'='*70}\n")
        f.write(f"RUN #{result['run']}\n")
        f.write(f"{'='*70}\n")
        
        if result['success']:
            f.write(f"Status: SUCCESS\n")
            f.write(f"Word Count: {result['word_count']}\n")
            f.write(f"Length: {len(result['intro'])} characters\n")
            f.write(f"\nIntro Text:\n")
            f.write("-" * 70 + "\n")
            f.write(f"{result['intro']}\n")
            f.write("-" * 70 + "\n\n")
        else:
            f.write(f"Status: FAILED\n")
            f.write(f"Error: {result['error']}\n\n")

# Summary
success_count = sum(1 for r in results if r['success'])
print("\n" + "=" * 70)
print(f"SUMMARY: {success_count}/10 successful")
print(f"Results saved to: {output_file}")
print("=" * 70)
