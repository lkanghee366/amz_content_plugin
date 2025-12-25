"""
Test INFO Article Generation
Test keyword: "how to cook beef ribs"
"""
import sys
import os
import json
from dotenv import load_dotenv
from unified_ai_client import UnifiedAIClient
from chat_zai_client import ChatZaiClient
from cerebras_client import CerebrasClient
from ai_generator import AIContentGenerator

# Load environment
load_dotenv()

def test_info_article():
    """Test generating complete INFO article"""
    keyword = "how to cook beef ribs"
    
    print(f"\n{'='*60}")
    print(f"🧪 Testing INFO Article Generation")
    print(f"Keyword: {keyword}")
    print(f"{'='*60}\n")
    
    # Initialize clients
    print("🔧 Initializing AI clients...")
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
    
    try:
        # Generate INFO article
        print("\n📝 Generating INFO article...")
        article = generator.generate_info_article(keyword)
        
        # Display results
        print(f"\n{'='*60}")
        print("✅ GENERATION COMPLETE")
        print(f"{'='*60}\n")
        
        print("📄 INTRO:")
        print(f"   {article['intro']}")
        print(f"   ({len(article['intro'].split())} words)\n")
        
        print(f"📚 BODY SECTIONS ({len(article['sections'])}):")
        for i, section in enumerate(article['sections'], 1):
            word_count = len(section['content'].split())
            print(f"   {i}. {section['heading']}")
            print(f"      {section['content'][:100]}...")
            print(f"      ({word_count} words)\n")
        
        print(f"❓ FAQs ({len(article['faqs'])}):")
        for i, faq in enumerate(article['faqs'], 1):
            print(f"   {i}. Q: {faq['question']}")
            print(f"      A: {faq['answer'][:80]}...")
            print()
        
        print("🏁 CONCLUSION:")
        print(f"   {article['conclusion']}")
        print(f"   ({len(article['conclusion'].split())} words)\n")
        
        # Save to file
        output_file = "test_info_article_output.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(article, f, indent=2, ensure_ascii=False)
        print(f"💾 Full output saved to: {output_file}\n")
        
        return article
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    test_info_article()
