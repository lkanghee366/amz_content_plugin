"""
HTML Builder - Creates WordPress post content
Mirrors the PHP plugin's HTML structure
"""
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class HTMLBuilder:
    """Build HTML content for WordPress post"""
    
    @staticmethod
    def _title_before_comma(title: str) -> str:
        """Extract title before first comma"""
        if ',' in title:
            return title.split(',')[0].strip()
        return title
    
    @staticmethod
    def build_intro(intro_text: str) -> str:
        """Build introduction paragraph"""
        return f'<p>{intro_text}</p>\n'
    
    @staticmethod
    def build_editors_choice(products: list, badges_map: dict, top_asin: str) -> str:
        """Build Editor's Choice + Best-for section"""
        html = '<div class="acap-picks">\n'
        
        # Find top product
        top_product = next((p for p in products if p['asin'] == top_asin), None)
        
        if top_product:
            top_title = HTMLBuilder._title_before_comma(top_product['title'])
            top_badge = badges_map.get(top_asin, '')
            top_img = top_product.get('image_url', '')
            
            html += '  <div class="acap-bestfor-box acap-bestfor-box--ec">\n'
            html += '    <div class="acap-bestfor-title">\n'
            html += '      <span class="acap-label acap-label--red" style="background-image: linear-gradient(to right, #6a11cb 0%, #2575fc 100%); color: #ffffff; padding: 4px 12px; border-radius: 20px; display: inline-block; font-weight: bold;">Editor\'s Choice</span>\n'
            html += '    </div>\n'
            html += '    <div class="acap-ec">\n'
            
            if top_img:
                html += f'      <a class="acap-ec-thumb" href="{top_product["url"]}" target="_blank" rel="nofollow sponsored noopener">\n'
                html += f'        <img src="{top_img}" alt="{top_title}" width="240" height="240" loading="lazy" />\n'
                html += '      </a>\n'
            
            html += f'      <a class="acap-ec-title" href="{top_product["url"]}" target="_blank" rel="nofollow sponsored noopener">{top_title}</a>\n'
            
            if top_badge:
                html += f'      <span class="acap-badge-inline">{top_badge}</span>\n'
            
            html += '    </div>\n'
            html += '  </div>\n'
        
        # Best for specific purpose
        html += '  <div class="acap-bestfor-box">\n'
        html += '    <div class="acap-bestfor-title" style="background-image: linear-gradient(to right, #ff8008 0%, #ffc837 100%); color: #ffffff; padding: 4px 12px; border-radius: 20px; display: inline-block; font-weight: bold;">Best for a specific purpose</div>\n'
        html += '    <ul class="acap-list">\n'
        
        for product in products:
            asin = product['asin']
            badge = badges_map.get(asin, '')
            if not badge:
                continue
            
            short_title = HTMLBuilder._title_before_comma(product['title'])
            html += f'      <li><strong>Best for {badge.lower()}:</strong> '
            html += f'<a href="{product["url"]}" target="_blank" rel="nofollow sponsored noopener" class="acap-bestfor-link">{short_title}</a></li>\n'
        
        html += '    </ul>\n'
        html += '  </div>\n'
        html += '</div>\n'
        
        return html
    
    @staticmethod
    def build_product_cards(keyword: str, products: list, badges_map: dict) -> str:
        """Build product comparison cards section"""
        html = '<div class="acap-compare-wrap">\n'
        html += f'  <h2>Product Comparison: {keyword.title()}</h2>\n'
        html += '  <div class="acap-vstack">\n'
        
        for product in products:
            asin = product['asin']
            badge = badges_map.get(asin, '')
            
            html += '    <div class="acap-box">\n'
            
            if badge:
                html += f'      <div class="acap-badge">{badge}</div>\n'
            
            html += f'      <h3 class="acap-title">{product["title"]}</h3>\n'
            
            if product.get('image_url'):
                html += f'      <img class="acap-img" src="{product["image_url"]}" alt="{product["title"]}" />\n'
            
            brand = product.get('brand')
            if brand:
                html += f'      <div class="acap-brand">{brand}</div>\n'
            else:
                html += '      <div class="acap-brand">—</div>\n'
            
            # Features
            if product.get('features'):
                html += '      <ul class="acap-features">\n'
                for feature in product['features']:
                    html += f'        <li>{feature}</li>\n'
                html += '      </ul>\n'
            
            html += f'      <a class="acap-btn" href="{product["url"]}" rel="nofollow sponsored noopener" target="_blank">Check price</a>\n'
            html += '    </div>\n'
        
        html += '  </div>\n'
        html += '  <p class="acap-note"><em>Product prices and availability are accurate as of the date/time indicated and are subject to change. Any price and availability information displayed on Amazon.com at the time of purchase will apply to the purchase of this product.</em></p>\n'
        html += '</div>\n'
        
        return html
    
    @staticmethod
    def build_buying_guide(guide_data: dict) -> str:
        """Build buying guide section"""
        html = '<h2>Buying Guide</h2>\n'
        html += '<div class="acap-buying-guide">\n'
        html += f'  <h3>{guide_data["title"]}</h3>\n'
        
        if guide_data.get('sections'):
            for section in guide_data['sections']:
                if section.get('heading'):
                    html += f'  <h4>{section["heading"]}</h4>\n'
                
                if section.get('bullets'):
                    html += '  <ul>\n'
                    for bullet in section['bullets']:
                        html += f'    <li>{bullet}</li>\n'
                    html += '  </ul>\n'
        
        html += '</div>\n'
        return html
    
    @staticmethod
    def build_faqs(faqs_data: list) -> str:
        """Build FAQs section"""
        html = '<h2>FAQs</h2>\n'
        html += '<div class="acap-faqs">\n'
        
        for qa in faqs_data:
            html += '  <details>\n'
            html += f'    <summary>{qa["question"]}</summary>\n'
            html += f'    <p>{qa["answer"]}</p>\n'
            html += '  </details>\n'
        
        html += '</div>\n'
        return html
    
    @staticmethod
    def build_full_post(keyword: str, intro: str, products: list, badges_data: dict, 
                       buying_guide: dict, faqs: list) -> str:
        """
        Build complete post content
        
        Structure:
        1. Introduction
        2. Editor's Choice + Best-for
        3. Product Cards
        4. Buying Guide
        5. FAQs
        """
        logging.info(f"🏗️ Building HTML content for: {keyword}")
        
        # Create badges map
        badges_map = {item['asin']: item['badge'] for item in badges_data['badges']}
        top_asin = badges_data['top_recommendation']['asin']
        
        content = ""
        content += HTMLBuilder.build_intro(intro)
        content += HTMLBuilder.build_editors_choice(products, badges_map, top_asin)
        content += HTMLBuilder.build_product_cards(keyword, products, badges_map)
        content += HTMLBuilder.build_buying_guide(buying_guide)
        content += HTMLBuilder.build_faqs(faqs)
        
        logging.info(f"✅ HTML content built ({len(content)} chars)")
        return content
