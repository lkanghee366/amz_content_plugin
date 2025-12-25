import os
import logging
from dotenv import load_dotenv
from cerebras_client import CerebrasClient
from chat_zai_client import ChatZaiClient
from unified_ai_client import UnifiedAIClient
from ai_generator import AIContentGenerator

# Setup logging với DEBUG level
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

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
    
    # Test với 1 keyword
    test_keyword = "wine cooler ge"
    
    print(f"\n{'='*60}")
    print(f"Testing classifier với keyword: {test_keyword}")
    print(f"{'='*60}\n")
    
    # Build prompt manually to show it
    prompt = (
        f"Analyze the search keyword: '{test_keyword}'\n"
        "Classify it into exactly one of these 3 categories:\n"
        "1. REVIEW: User wants to buy a physical product, compare models, or find 'best' options. (e.g., 'best laptop', 'iphone 15 review', 'cheap running shoes', 'wine cooler fridge', 'samsung vs lg').\n"
        "2. INFO: User wants knowledge, guides, recipes, definitions, or troubleshooting. (e.g., 'how to tie a tie', 'wine cooler recipe', 'why is sky blue', 'cleaning tips', 'what is a wine cooler').\n"
        "3. SKIP: Keywords related to:\n"
        "   - Adult/Sex/Porn\n"
        "   - Drugs/Weapons/Illegal acts\n"
        "   - Gambling\n"
        "   - Specific locations OUTSIDE US, UK, EU, Canada (e.g., 'price in india', 'vietnam shop')\n"
        "   - Nonsense or too short to be meaningful\n\n"
        "Output JSON ONLY in this format:\n"
        "{\"type\": \"review\" or \"info\" or \"skip\", \"reason\": \"short explanation\"}"
    )
    
    print("PROMPT:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)
    print("\nCalling Cerebras API...\n")
    
    # Get raw response from Cerebras
    raw_response = cerebras.generate(
        prompt=prompt,
        max_tokens=100,
        temperature=0.1,
        use_reasoning=False
    )
    
    print("RAW RESPONSE:")
    print("-" * 60)
    print(raw_response)
    print("-" * 60)
    
    # Now use the classifier
    result = generator.classify_keyword(test_keyword)
    
    print(f"\n{'='*60}")
    print(f"RESULT:")
    print(f"{'='*60}")
    print(f"Type: {result['type']}")
    print(f"Reason: {result.get('reason', 'N/A')}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
