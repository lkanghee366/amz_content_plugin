import sys
import os
import logging

# Add current directory to path
sys.path.append(os.getcwd())

from html_builder import HTMLBuilder

def test_html_structure():
    print("Testing HTML Structure...")
    
    keyword = "best coffee maker 2024"
    intro = "Choosing the right coffee maker can transform your mornings."
    products = [
        {"asin": "B01", "title": "Premium Espresso Machine", "url": "https://amazon.com/ps1", "image_url": "img1.jpg"},
        {"asin": "B02", "title": "Budget Drip Coffee Maker", "url": "https://amazon.com/ps2", "image_url": "img2.jpg"}
    ]
    badges_data = {
        "top_recommendation": {"asin": "B01"},
        "badges": [
            {"asin": "B01", "badge": "Best Overall"},
            {"asin": "B02", "badge": "Best Value"}
        ]
    }
    buying_guide = {"title": "Buying Guide", "sections": []}
    faqs = []
    reviews_map = {
        "B01": {
            "description": "High-end machine with great features.",
            "pros": ["Professional grade", "Built-in grinder", "Stainless steel"],
            "cons": ["Expensive"]
        },
        "B02": {
            "description": "Simple and effective.",
            "pros": ["Cheap", "Small"],
            "cons": ["Slow"]
        }
    }
    takeaways = [
        "The Premium Espresso Machine is top-rated for its professional-grade results.",
        "Consider your counter space and daily coffee volume before buying.",
        "Budget options like the Drip Maker offer great value for simple needs."
    ]

    html = HTMLBuilder.build_full_post(
        keyword=keyword,
        intro=intro,
        products=products,
        badges_data=badges_data,
        buying_guide=buying_guide,
        faqs=faqs,
        reviews_map=reviews_map,
        takeaways=takeaways
    )

    # Verification
    print("\n--- HTML CONTENT PREVIEW ---")
    print(html[:1500])
    print("----------------------------\n")

    # Check for Key Takeaways
    assert "Key Takeaways" in html, "FAIL: Key Takeaways section missing"
    assert takeaways[0] in html, "FAIL: Takeaway content missing"
    print("✅ Key Takeaways section verified")

    # Check for Why we choose
    assert "Why we choose:" in html, "FAIL: 'Why we choose' section missing"
    assert "Professional grade" in html, f"FAIL: Pro content missing from Why we choose: {reviews_map['B01']['pros'][0]}"
    print("✅ 'Why we choose' section verified")

    # Check order (Takeaways should be after Intro)
    intro_idx = html.find(intro)
    takeaways_idx = html.find("Key Takeaways")
    ec_idx = html.find("Editor's Choice")
    
    assert intro_idx < takeaways_idx, "FAIL: Key Takeaways should be after Intro"
    assert takeaways_idx < ec_idx, "FAIL: Editor's Choice should be after Key Takeaways"
    print("✅ Section order verified (Intro -> Takeaways -> Editor's Choice)")

    print("\n🎉 ALL TESTS PASSED!")

if __name__ == "__main__":
    try:
        test_html_structure()
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
