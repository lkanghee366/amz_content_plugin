import os
import logging
import time
from dotenv import load_dotenv
from chat_zai_client import ChatZaiClient
from cerebras_client import CerebrasClient
from unified_ai_client import UnifiedAIClient
from ai_generator import AIContentGenerator

# Tắt hoàn toàn tất cả logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger('cerebras').setLevel(logging.CRITICAL)
logging.getLogger('httpx').setLevel(logging.CRITICAL)
logging.getLogger('httpcore').setLevel(logging.CRITICAL)

def main():
    load_dotenv()
    
    # Initialize clients
    chat_zai = ChatZaiClient(
        api_url=os.getenv('CHAT_ZAI_API_URL', 'http://localhost:3001'),
        timeout=60
    )
    
    cerebras = CerebrasClient(
        api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
        model='zai-glm-4.6'
    )
    
    ai_client = UnifiedAIClient(chat_zai_client=chat_zai, cerebras_client=cerebras)
    generator = AIContentGenerator(ai_client)
    
    # Load keywords from file
    keywords_file = os.path.join('python_poster', 'test_keywords_comprehensive.txt')
    if not os.path.exists(keywords_file):
        keywords_file = 'test_keywords_comprehensive.txt'  # Try current directory
    
    if not os.path.exists(keywords_file):
        print(f"❌ ERROR: File not found: {keywords_file}")
        print(f"   Current working directory: {os.getcwd()}")
        return
    
    print(f"✅ Loading keywords from: {keywords_file}")
    
    with open(keywords_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📄 Read {len(lines)} lines from file\n")
    
    # Parse keywords and expected types
    test_cases = []
    current_category = None
    expected_type = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith('#'):
            # Category header
            line_upper = line.upper()
            if 'REVIEW' in line_upper and 'INTENT' in line_upper:
                expected_type = 'review'
                current_category = 'REVIEW'
                print(f"DEBUG: Found REVIEW section")
            elif 'INFO' in line_upper and 'INTENT' in line_upper:
                expected_type = 'info'
                current_category = 'INFO'
                print(f"DEBUG: Found INFO section")
            elif 'SKIP' in line_upper and 'GEOGRAPHY' in line_upper:
                expected_type = 'skip'
                current_category = 'SKIP (Geo)'
                print(f"DEBUG: Found SKIP Geo section")
            elif 'SKIP' in line_upper and 'SENSITIVE' in line_upper:
                expected_type = 'skip'
                current_category = 'SKIP (Sensitive)'
                print(f"DEBUG: Found SKIP Sensitive section")
            elif 'EDGE' in line_upper:
                expected_type = 'unknown'
                current_category = 'EDGE CASES'
                print(f"DEBUG: Found EDGE section")
        else:
            # Keyword - only add if we have a category
            if current_category:
                test_cases.append({
                    'keyword': line,
                    'expected': expected_type,
                    'category': current_category
                })
                print(f"DEBUG: Added '{line}' to category '{current_category}'")
    
    print(f"\n🚀 Comprehensive Classifier Test - {len(test_cases)} test cases\n")
    print(f"{'KEYWORD':<45} | {'EXPECTED':<8} | {'RESULT':<8} | STATUS")
    print("-" * 85)
    
    stats = {
        'total': len(test_cases),
        'correct': 0,
        'incorrect': 0,
        'error': 0
    }
    
    category_stats = {}
    
    for test_case in test_cases:
        keyword = test_case['keyword']
        expected = test_case['expected']
        category = test_case['category']
        
        result = generator.classify_keyword(keyword)
        result_type = result['type']
        
        # Initialize category stats
        if category not in category_stats:
            category_stats[category] = {'correct': 0, 'total': 0}
        category_stats[category]['total'] += 1
        
        # Check if correct
        if expected == 'unknown':
            # Edge case - no expected answer
            status = "🔍 CHECK"
            is_correct = None
        elif result_type == expected:
            status = "✅ PASS"
            stats['correct'] += 1
            category_stats[category]['correct'] += 1
            is_correct = True
        else:
            status = "❌ FAIL"
            stats['incorrect'] += 1
            is_correct = False
        
        # Color code
        result_display = result_type.upper()
        if result_type == 'review':
            result_display = f"\033[92m{result_display}\033[0m"
        elif result_type == 'info':
            result_display = f"\033[94m{result_display}\033[0m"
        else:
            result_display = f"\033[91m{result_display}\033[0m"
        
        expected_display = expected.upper() if expected and expected != 'unknown' else "N/A"
        
        print(f"{keyword:<45} | {expected_display:<8} | {result_display:<17} | {status}")
        
        # Small delay
        time.sleep(0.3)
    
    print("-" * 85)
    print(f"\n📊 OVERALL RESULTS:")
    print(f"   Total: {stats['total']}")
    if stats['total'] > 0:
        print(f"   Correct: {stats['correct']} ({stats['correct']*100//stats['total']}%)")
        print(f"   Incorrect: {stats['incorrect']} ({stats['incorrect']*100//stats['total']}%)")
    else:
        print(f"   ⚠️ No test cases loaded! Check if file exists and is formatted correctly.")
        return
    
    print(f"\n📈 BY CATEGORY:")
    for cat, cat_stats in category_stats.items():
        accuracy = cat_stats['correct'] * 100 // cat_stats['total'] if cat_stats['total'] > 0 else 0
        print(f"   {cat:<20}: {cat_stats['correct']}/{cat_stats['total']} ({accuracy}%)")
    print()

if __name__ == "__main__":
    main()
