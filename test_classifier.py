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
    
    # Initialize Cerebras client
    cerebras = CerebrasClient(
        api_keys_file=os.getenv('CEREBRAS_KEYS_FILE', 'cerebras_api_keys.txt'),
        model='zai-glm-4.6'
    )
    
    ai_client = UnifiedAIClient(chat_zai_client=chat_zai, cerebras_client=cerebras)
    generator = AIContentGenerator(ai_client)
    
    # Test keywords
    keywords = [
        "frigidaire wine cooler 8 bottle",
        "wine cooler glass",
        "wine cooler gift",
        "wine cooler glass bottle",
        "wine cooler ge",
        "wine cooler gas station",
        "wine cooler gif",
        "wine cooler gluten free",
        "wine cooler gasket replacement",
        "wine cooler gift set",
        "wine cooler gea",
        "georg jensen wine cooler",
        "ge monogram wine cooler",
        "ge wine cooler",
        "good pair days wine cooler",
        "ge profile wine cooler",
        "gaggenau wine cooler",
        "gold wine cooler",
        "glass wine cooler",
        "glen dimplex wine cooler",
        "green apple wine cooler",
        "wine cooler home depot",
        "wine cooler holder",
        "wine cooler humidity control",
        "wine cooler humidor",
        "wine cooler height",
        "wine cooler humidity",
        "wine cooler haier",
        "wine cooler history",
        "wine cooler hot to touch",
        "wine cooler high end",
        "hisense wine cooler",
        "hoover wine cooler",
        "home depot wine cooler",
        "huski wine cooler nz",
        "howdens wine cooler",
        "how much alcohol is in a wine cooler",
        "huski wine cooler uk",
        "how to make a wine cooler",
        "wine cooler in cabinet",
        "wine cooler in a can",
        "wine cooler in 2 liter bottle",
        "wine cooler in spanish",
        "wine cooler in kitchen",
        "wine cooler ingredients",
        "wine cooler ideas",
        "wine cooler in kitchen island",
        "wine cooler ice maker combo",
        "wine cooler in island",
        "integrated wine cooler",
        "ivation wine cooler",
        "insignia wine cooler",
        "ionchill wine cooler",
        "ikea wine cooler",
        "insulated wine cooler",
        "igloo wine cooler",
        "ionchill 6 bottle wine cooler",
        "integrated wine cooler 600mm",
        "insignia 29 bottle wine cooler",
        "wine cooler jamaican me happy",
        "wine cooler jack daniels",
        "wine cooler john lewis",
        "wine cooler jacket"
    ]
    
    print(f"\n🚀 Testing Classifier with {len(keywords)} keywords...\n")
    print(f"{'KEYWORD':<40} | {'TYPE':<10} | STATUS")
    print("-" * 70)
    
    results = {'review': 0, 'info': 0, 'skip': 0}
    success_count = 0
    error_count = 0
    
    for idx, kw in enumerate(keywords, 1):
        result = generator.classify_keyword(kw)
        k_type = result['type'].upper()
        results[result['type']] += 1
        
        # Check if it's a real classification or error fallback
        if k_type == 'SKIP' and 'error' in str(result).lower():
            status = "❌ ERROR"
            error_count += 1
        else:
            status = "✅ OK"
            success_count += 1
        
        # Color code output
        if k_type == 'REVIEW':
            type_str = f"\033[92m{k_type}\033[0m"  # Green
        elif k_type == 'INFO':
            type_str = f"\033[94m{k_type}\033[0m"  # Blue
        else:
            type_str = f"\033[91m{k_type}\033[0m"  # Red
            
        print(f"{kw:<40} | {type_str:<19} | {status}")
        
        # Small delay to be nice to API
        time.sleep(0.5)
        
    print("-" * 70)
    print(f"\n📊 SUMMARY:")
    print(f"   Total: {len(keywords)} keywords")
    print(f"   Success: {success_count} | Errors: {error_count}")
    print(f"   Review: {results['review']} | Info: {results['info']} | Skip: {results['skip']}")
    print()

if __name__ == "__main__":
    main()
