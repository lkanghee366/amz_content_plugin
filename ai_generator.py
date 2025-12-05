"""
AI Content Generator using Unified AI Client
Generates: Intro, Badges, Editor's Choice, Buying Guide, FAQs
"""
import json
import re
import logging
from unified_ai_client import UnifiedAIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AIContentGenerator:
    """Generate article content using Unified AI Client (ChatZai + Cerebras fallback)"""
    
    def __init__(self, ai_client: UnifiedAIClient):
        """Initialize with Unified AI client"""
        self.client = ai_client
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from AI response (handles markdown code blocks)"""
        text = text.strip()
        
        # Remove markdown code blocks
        text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
        text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        # Find both object {...} and array [...]
        obj_start = text.find('{')
        obj_end = text.rfind('}')
        arr_start = text.find('[')
        arr_end = text.rfind(']')
        
        # Choose which to extract based on what comes first
        if arr_start != -1 and (obj_start == -1 or arr_start < obj_start):
            # Array comes first or object not found - extract array
            if arr_start != -1 and arr_end != -1 and arr_end > arr_start:
                return text[arr_start:arr_end + 1]
        else:
            # Object comes first - extract object
            if obj_start != -1 and obj_end != -1 and obj_end > obj_start:
                return text[obj_start:obj_end + 1]
        
        return text

    def _clean_intro(self, text: str) -> str:
        """Return a single clean paragraph from the model output"""
        if not text:
            return ""

        def is_instruction(segment: str) -> bool:
            lower = segment.lower()
            instruction_tokens = (
                "we need", "let's", "lets", "count", "ensure word count",
                "i will", "draft", "plan", "outline", "analysis", "approach",
                "step", "goal", "objective", "strategy"
            )
            return any(token in lower for token in instruction_tokens)

        text = text.strip()

        # Collect candidate paragraphs (quoted blocks first, then individual lines)
        candidates = []
        for match in re.finditer(r'["“](.+?)["”]', text, re.DOTALL):
            candidates.append(match.group(1).strip())
        candidates.extend(line.strip() for line in text.splitlines() if line.strip())

        seen = set()
        for cand in candidates:
            normalized = re.sub(r'\s+', ' ', cand.strip('"“”'))
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            word_count = len(re.findall(r'\w+', normalized))
            if 40 <= word_count <= 140 and not is_instruction(normalized):
                return normalized

        # Fallback: remove instruction-like sentences and join the rest
        sentences = re.split(r'(?<=[.!?])\s+', text)
        filtered = [s for s in sentences if s and not is_instruction(s)]
        fallback = ' '.join(filtered).strip('"“” ')
        if fallback:
            return re.sub(r'\s+', ' ', fallback)

        return re.sub(r'\s+', ' ', text.strip('""" '))
    
    def _bold_keyword_in_text(self, text: str, keyword: str) -> str:
        """
        Bold the keyword in text using **keyword** markdown.
        Handles case-insensitive matching and preserves original case.
        
        Example:
            keyword = "4 seater garden dining set sale"
            "...the best 4 seater garden dining set sale..." 
            -> "...the best **4 seater garden dining set sale**..."
        """
        import re
        
        # Escape special regex characters in keyword
        escaped_keyword = re.escape(keyword)
        
        # Case-insensitive search, capture original text
        pattern = re.compile(f'({escaped_keyword})', re.IGNORECASE)
        
        # Replace with **original_match**
        result = pattern.sub(r'**\1**', text)
        
        return result
    
    def generate_intro(self, keyword: str) -> str:
        """Generate introduction paragraph (55-110 words)"""
        logging.info(f"📝 Generating introduction for: {keyword}")
        
        # Direct instruction to output ONLY the intro
        prompt = (
            f'Write a 80-word engaging introduction for a comparison article about "{keyword}". '
            'Be conversational and trustworthy.'
            'Output ONLY the final paragraph—no explanations, no thinking, no notes.'
        )
        
        try:
            # Use llama-3.3-70b for intro (cleaner output, less reasoning)
            raw_intro = self.client.generate(
                prompt=prompt,
                max_tokens=512,
                temperature=0.2,
                stream=True,
                model_override='qwen-3-235b-a22b-instruct-2507'
            )
            
            # Clean aggressively
            intro = self._clean_intro(raw_intro)
            
            # If still too short or contains meta-text, extract last sentence cluster
            if len(intro.split()) < 40:
                sentences = re.split(r'(?<=[.!?])\s+', raw_intro)
                # Get last 2-3 sentences that don't look like meta-text
                clean_sentences = []
                for sent in reversed(sentences):
                    if len(sent) > 20 and not any(word in sent.lower() for word in ['word', 'paragraph', 'intro', 'write', 'must', 'output']):
                        clean_sentences.insert(0, sent)
                        if len(' '.join(clean_sentences).split()) >= 40:
                            break
                if clean_sentences:
                    intro = ' '.join(clean_sentences)
            
            intro = intro.strip()
            
            # Bold the keyword in intro
            intro = self._bold_keyword_in_text(intro, keyword)
            
            word_count = len(intro.split())
            logging.info(f"✅ Introduction generated ({word_count} words)")
            return intro
        except Exception as e:
            logging.error(f"❌ Failed to generate intro: {e}")
            raise
    
    def generate_badges(self, keyword: str, products: list) -> dict:
        """
        Generate badges for all products + select top recommendation
        
        Returns:
            {
                "top_recommendation": {"asin": "B0XXX"},
                "badges": [
                    {"asin": "B0XXX", "badge": "Best overall"},
                    {"asin": "B0YYY", "badge": "Best value"}
                ]
            }
        """
        logging.info(f"🏷️ Generating badges for {len(products)} products")
        
        # Compact product info
        compact = []
        all_asins = []
        for product in products:
            title = product['title']
            if len(title) > 80:
                title = title[:77] + '…'
            
            compact.append({
                'asin': product['asin'],
                'title': title,
                'price': product['price'],
                'brand': product.get('brand', ''),
                'features': product['features'] if product['features'] else []
            })
            all_asins.append(product['asin'])
        
        prompt = (
            "IMPORTANT: Output ONLY the JSON, no explanations, no thinking process.\n\n"
            "Create product badges for ALL products in the comparison article.\n\n"
            "CRITICAL REQUIREMENTS:\n"
            "1. You MUST create a badge for EVERY SINGLE product listed below\n"
            "2. Each badge must be a purposeful 2-3 word phrase that clearly reflects the product's unique strength, use case, or standout feature\n"
            "3. Avoid generic labels (e.g., 'Best overall', 'Great value') unless they truly match the product; make badges feel human and specific\n"
            "4. Pick exactly ONE product as top recommendation (editor's choice)\n"
            "5. Draw inspiration from the brand, title, and feature list for each product when crafting the badge\n"
            "6. Examples of acceptable style: \"Rain-Ready Seating\", \"Compact Bistro Choice\", \"Premium Teak Craft\", \"Budget-Friendly Lounger\"\n\n"
            f"MANDATORY: Return badges for ALL {len(compact)} products.\n\n"
            "JSON FORMAT (no markdown, no extra text):\n"
            '{"top_recommendation": {"asin": "ACTUAL_ASIN"}, "badges": ['
            '{"asin": "ASIN1", "badge": "Best overall"}, {"asin": "ASIN2", "badge": "Best value"}, ...]}\n\n'
            f"ALL ASINs that MUST be included:\n{', '.join(all_asins)}\n\n"
            f"Context: {keyword}\n"
            f"Products: {json.dumps(compact, ensure_ascii=False)}"
        )
        
        try:
            response = self.client.generate(
                prompt=prompt,
                max_tokens=2048,  # Increased to ensure JSON completion (badges for 10 products)
                temperature=0.5,
                stream=False  # Disable streaming for JSON reliability
            )
            
            logging.info(f"📦 Raw badges response: {len(response)} chars, preview: '{response[:100]}'")
            
            # Extract and parse JSON
            json_text = self._extract_json(response)
            logging.info(f"📦 Extracted JSON: {len(json_text)} chars, preview: '{json_text[:100]}'")
            
            data = json.loads(json_text)
            
            # Validate structure
            if 'top_recommendation' not in data or 'badges' not in data:
                raise ValueError("Missing top_recommendation or badges in response")
            
            if not isinstance(data['badges'], list):
                raise ValueError("badges must be a list")
            
            logging.info(f"✅ Generated {len(data['badges'])} badges, top: {data['top_recommendation']['asin']}")
            return data
            
        except json.JSONDecodeError as e:
            logging.error(f"❌ JSON parse error: {e}")
            logging.error(f"Raw response: {response[:500]}")
            raise
        except Exception as e:
            logging.error(f"❌ Failed to generate badges: {e}")
            raise
    
    def generate_buying_guide(self, keyword: str, products: list) -> dict:
        """
        Generate buying guide with sections
        
        Returns:
            {
                "title": "Buying Guide: ...",
                "sections": [
                    {"heading": "Capacity & Size", "bullets": ["...", "..."]},
                    {"heading": "Performance", "bullets": ["...", "..."]}
                ]
            }
        """
        logging.info(f"📚 Generating buying guide for: {keyword}")
        
        # Compact product info
        compact = []
        for product in products:
            title = product['title']
            if len(title) > 80:
                title = title[:77] + '…'
            
            compact.append({
                'asin': product['asin'],
                'title': title,
                'price': product['price'],
                'features': product['features'][:5] if product['features'] else []
            })
        
        prompt = (
            "Create a buying guide for product comparison.\n"
            "IMPORTANT: Return ONLY this exact JSON format (no markdown, no extra text):\n\n"
            '{"title": "Buying Guide: ' + keyword.title() + '", '
            '"sections": [{"heading": "Capacity & Size", "bullets": ["Consider your family size", "Check counter space"]}, '
            '{"heading": "Performance", "bullets": ["Look for higher wattage", "Check temperature range"]}]}\n\n'
            "Create 4-6 sections with 3-5 bullets each. No emojis, no prices.\n"
            f"Context: {keyword}\n"
            f"Products: {json.dumps(compact, ensure_ascii=False)}"
        )
        
        try:
            response = self.client.generate(
                prompt=prompt,
                max_tokens=2048,  # Increased for complete JSON response
                temperature=0.5,
                stream=False  # Disable streaming
            )
            
            # Extract and parse JSON
            json_text = self._extract_json(response)
            data = json.loads(json_text)
            
            # Handle different response formats
            if 'title' in data and 'sections' in data:
                final_data = data
            elif isinstance(data, list) and len(data) > 0 and 'heading' in data[0]:
                # AI returned sections array directly
                final_data = {
                    'title': f"Buying Guide: {keyword.title()}",
                    'sections': data
                }
            else:
                raise ValueError("Invalid buying guide schema")
            
            logging.info(f"✅ Generated buying guide with {len(final_data['sections'])} sections")
            return final_data
            
        except json.JSONDecodeError as e:
            logging.error(f"❌ JSON parse error: {e}")
            logging.error(f"Raw response: {response[:500]}")
            raise
        except Exception as e:
            logging.error(f"❌ Failed to generate buying guide: {e}")
            raise
    
    def generate_faqs(self, keyword: str, products: list) -> list:
        """
        Generate FAQs
        
        Returns:
            [
                {"question": "What should I look for?", "answer": "Consider..."},
                {"question": "How do they compare?", "answer": "Main differences..."}
            ]
        """
        logging.info(f"❓ Generating FAQs for: {keyword}")
        
        # Compact product info
        compact = []
        for product in products:
            title = product['title']
            if len(title) > 80:
                title = title[:77] + '…'
            
            compact.append({
                'asin': product['asin'],
                'title': title,
                'price': product['price'],
                'features': product['features'][:5] if product['features'] else []
            })
        
        prompt = (
            "Create 5-10 detailed FAQs for shoppers comparing products.\n"
            "IMPORTANT: Return ONLY a JSON array (no markdown, no extra text):\n\n"
            '[{"question": "What should I look for?", "answer": "Consider capacity, features..."}, '
            '{"question": "How do they compare?", "answer": "Main differences are..."}]\n\n'
            "Each answer should be 2-4 sentences. Cover buying tips, comparisons, features, value.\n"
            f"Context: {keyword}\n"
            f"Products: {json.dumps(compact, ensure_ascii=False)}"
        )
        
        try:
            response = self.client.generate(
                prompt=prompt,
                max_tokens=2048,  # Increased for complete JSON response (5-10 FAQs)
                temperature=0.5,
                stream=False  # Disable streaming
            )
            
            # Extract and parse JSON
            json_text = self._extract_json(response)
            faqs = json.loads(json_text)
            
            # Validate structure
            if not isinstance(faqs, list):
                raise ValueError("FAQs must be a list")
            
            if len(faqs) == 0:
                raise ValueError("FAQs list is empty")
            
            if 'question' not in faqs[0] or 'answer' not in faqs[0]:
                raise ValueError("Invalid FAQ schema")
            
            logging.info(f"✅ Generated {len(faqs)} FAQs")
            return faqs
            
        except json.JSONDecodeError as e:
            logging.error(f"❌ JSON parse error: {e}")
            logging.error(f"Raw response: {response[:500]}")
            raise
        except Exception as e:
            logging.error(f"❌ Failed to generate FAQs: {e}")
            raise
