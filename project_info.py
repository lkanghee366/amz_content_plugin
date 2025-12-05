"""
Project Structure and File Summary
Generated on: 2024-11-07
"""

PROJECT_STRUCTURE = """
python_poster/
│
├── 📝 Configuration Files
│   ├── .env.example              # Configuration template (COPY to .env)
│   ├── .gitignore                # Git ignore rules (security)
│   ├── cerebras_api_keys.txt     # Cerebras API keys (15 keys ready)
│   ├── keywords.txt              # 533 keywords ready to process
│   └── requirements.txt          # Python dependencies
│
├── 🔧 Core Application Files
│   ├── main.py                   # Main entry point (RUN THIS)
│   ├── cerebras_client.py        # Cerebras AI client (key rotation)
│   ├── amazon_api.py             # Amazon PA-API wrapper
│   ├── ai_generator.py           # AI content generation
│   ├── html_builder.py           # HTML structure builder
│   └── wordpress_api.py          # WordPress REST API client
│
├── 🧪 Testing & Setup Scripts
│   ├── setup.ps1                 # PowerShell setup script
│   ├── test_workflow.py          # Full workflow test (RUN FIRST)
│   └── quick_test.py             # Single keyword test
│
└── 📚 Documentation
    ├── README.md                 # Main documentation
    ├── WORKFLOW_CHECKLIST.md     # Detailed checklist
    └── SUMMARY.md                # Quick summary
"""

FILE_DESCRIPTIONS = {
    # Core Files
    "main.py": {
        "purpose": "Main application entry point",
        "lines": 273,
        "key_features": [
            "Load configuration from .env",
            "Initialize all components",
            "Process keywords from file",
            "Generate and post content",
            "Progress tracking and logging"
        ]
    },
    
    "cerebras_client.py": {
        "purpose": "Cerebras AI API client with automatic key rotation",
        "lines": 123,
        "key_features": [
            "Load API keys from file",
            "Automatic key rotation on rate limit",
            "Exponential backoff retry",
            "Stream response handling",
            "Model: gpt-oss-120b"
        ]
    },
    
    "amazon_api.py": {
        "purpose": "Amazon Product Advertising API wrapper",
        "lines": 150,
        "key_features": [
            "Product search by keyword",
            "Extract ASIN, title, price, images, features",
            "Region support (US, UK, DE, JP, SG)",
            "Error handling",
            "Returns standardized product data"
        ]
    },
    
    "ai_generator.py": {
        "purpose": "AI content generation using Cerebras",
        "lines": 250,
        "key_features": [
            "Generate introduction (60-100 words)",
            "Generate badges + top recommendation",
            "Generate buying guide (4-6 sections)",
            "Generate FAQs (5-10 Q&A)",
            "JSON parsing with fallbacks"
        ]
    },
    
    "html_builder.py": {
        "purpose": "Build HTML content for WordPress posts",
        "lines": 180,
        "key_features": [
            "Editor's Choice section",
            "Best-for-purpose list",
            "Product comparison cards",
            "Buying guide formatting",
            "FAQs with details/summary tags"
        ]
    },
    
    "wordpress_api.py": {
        "purpose": "WordPress REST API client",
        "lines": 160,
        "key_features": [
            "Application Password authentication",
            "Create/update/delete posts",
            "Set categories and author",
            "Test connection method",
            "Error handling"
        ]
    },
    
    # Testing Files
    "test_workflow.py": {
        "purpose": "Comprehensive workflow testing",
        "lines": 261,
        "tests": [
            "Environment configuration",
            "Cerebras API keys",
            "Keywords file",
            "Component initialization",
            "WordPress connection",
            "AI generation"
        ]
    },
    
    "quick_test.py": {
        "purpose": "Quick test with single keyword",
        "lines": 150,
        "features": [
            "Test all components",
            "Preview before posting",
            "Interactive confirmation",
            "Detailed progress output"
        ]
    },
    
    # Configuration
    ".env.example": {
        "purpose": "Environment configuration template",
        "sections": [
            "WordPress credentials",
            "Amazon PA-API keys",
            "Cerebras settings",
            "Post configuration"
        ]
    }
}

WORKFLOW_SUMMARY = """
WORKFLOW PROCESS:
=================

1. INITIALIZATION (main.py)
   ├─ Load .env configuration
   ├─ Initialize CerebrasClient (15 API keys)
   ├─ Initialize AmazonProductAPI
   ├─ Initialize AIContentGenerator
   └─ Initialize WordPressAPI

2. FOR EACH KEYWORD (from keywords.txt):
   
   A. Amazon Product Search (amazon_api.py)
      ├─ Search for 10 products
      ├─ Extract product data
      └─ Return standardized format
   
   B. AI Content Generation (ai_generator.py)
      ├─ Generate introduction (cerebras_client.py)
      ├─ Generate badges + top pick
      ├─ Generate buying guide
      └─ Generate FAQs
   
   C. HTML Building (html_builder.py)
      ├─ Intro paragraph
      ├─ Editor's Choice section
      ├─ Product cards
      ├─ Buying guide
      └─ FAQs
   
   D. WordPress Posting (wordpress_api.py)
      ├─ POST to /wp-json/wp/v2/posts
      ├─ Set title, content, status
      ├─ Set author and category
      └─ Return post ID and URL
   
   E. Delay (12 seconds)
      └─ Prevent rate limiting

3. SUMMARY REPORT
   ├─ Total processed
   ├─ Successful posts
   └─ Failed keywords
"""

DEPENDENCIES = {
    "python-amazon-paapi": "Amazon Product Advertising API",
    "cerebras-cloud-sdk": "Cerebras AI SDK",
    "requests": "HTTP library for WordPress API",
    "python-dotenv": "Environment variable management",
    "beautifulsoup4": "HTML parsing",
    "lxml": "XML/HTML processing"
}

PERFORMANCE_METRICS = {
    "keywords_total": 533,
    "time_per_post": "~50 seconds",
    "total_estimated_time": "~7.4 hours",
    "breakdown": {
        "amazon_search": "2-5s",
        "ai_generation": "15-30s (4 API calls)",
        "html_build": "<1s",
        "wordpress_post": "1-3s",
        "delay": "12s"
    }
}

if __name__ == "__main__":
    print(PROJECT_STRUCTURE)
    print("\n" + "="*60)
    print("TOTAL FILES: 17")
    print("="*60)
    print("\nCore Files: 6")
    print("Test Files: 3")
    print("Config Files: 5")
    print("Documentation: 3")
    print("\n" + WORKFLOW_SUMMARY)
