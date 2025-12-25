"""
AI Content Generator using Unified AI Client
Generates: Intro, Badges, Editor's Choice, Buying Guide, FAQs
"""
import json
import re
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from unified_ai_client import UnifiedAIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AIContentGenerator:
    """Generate article content using Unified AI Client (ChatZai + Cerebras fallback)"""
    
    def __init__(self, ai_client: UnifiedAIClient):
        """Initialize with Unified AI client"""
        self.client = ai_client
        self.max_retries = 3

    def classify_keyword(self, keyword: str) -> dict:
        """
        Classify keyword intent:
        1. Review (Commercial/Transactional)
        2. Info (Informational)
        3. Skip (Sensitive, Wrong Geo, Nonsense)
        
        Returns:
            {"type": "review"|"info"|"skip"}
        """
        logging.info(f"🔍 Classifying keyword: {keyword}")
        
        prompt = (
            f"Classify: '{keyword}'\n\n"
            "1 = REVIEW: Product names, 'best/top X', comparisons, buying intent\n"
            "2 = INFO: How-to, what/why/when, benefits, guides, tips, recipes\n"
            "3 = SKIP: NOT in us, uk, canada, eu (for example:india,vietnam,brazil,au,nz,sg,ph), or including drugs, sex, gaming, weapons, gambling, financial, nonsense\n\n"
            "Start your response with 'Here is your answer:' followed by only the number (1, 2, or 3). No extra explanations."
        )
        
        try:
            # Use Cerebras for class    ification (fast & cheap)
            # Use zai-glm-4.6 for classification with strong system prompt
            response = self.client.cerebras.generate(
                prompt=prompt,
                max_tokens=1000,
                temperature=0.5,
                model_override='zai-glm-4.6',
                system_prompt="You are a classifier. Output ONLY the number 1, 2, or 3. No explanation, no reasoning, just the number."
            )
            
            # Extract number from response
            response = response.strip()
            
            # Map number to type
            type_map = {
                "1": "review",
                "2": "info",
                "3": "skip"
            }
            
            # Find first digit
            for char in response:
                if char in type_map:
                    result_type = type_map[char]
                    logging.info(f"✅ Classified as: {result_type}")
                    return {"type": result_type}
            
            # Default to skip if no valid number found
            logging.warning(f"⚠️ Invalid response: {response[:100]}, defaulting to skip")
            return {"type": "skip"}
                
        except Exception as e:
            logging.error(f"❌ Classification failed: {e}")
            return {"type": "skip"}

    def _generate_with_retry(self, func, *args, **kwargs):
        """
        Execute a generation function with retry logic
        
        Args:
            func: Function to execute
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Result from function
            
        Raises:
            Exception: If all retries fail
        """
        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                logging.info(f"   Attempt {attempt}/{self.max_retries}")
                result = func(*args, **kwargs)
                if attempt > 1:
                    logging.info(f"   ✓ Succeeded on retry {attempt}")
                return result
            except Exception as e:
                last_error = e
                logging.warning(f"   ⚠️ Attempt {attempt} failed: {e}")
                if attempt < self.max_retries:
                    logging.info(f"   🔄 Retrying...")
        
        # All retries failed
        raise Exception(f"Failed after {self.max_retries} attempts. Last error: {last_error}")
    
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
        
        # Direct instruction to output ONLY the intro in plain text
        prompt = (
            f'Write a 80-word engaging introduction for a comparison article about "{keyword}". '
            'Be conversational and trustworthy. '
            'Start your response with "Here is your answer:" followed by the paragraph. '
            'No markdown, no bold formatting, no extra explanations or thinking.'
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
            
            # Remove any markdown bold formatting if present
            intro = re.sub(r'\*\*(.+?)\*\*', r'\1', intro)
            
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
            "Start your response with 'Here is your answer:' followed by the JSON only. No explanations, no thinking process.\n\n"
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
        
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logging.info(f"🔄 Badges generation attempt {attempt + 1}/{max_attempts}")
                
                response = self.client.generate(
                    prompt=prompt,
                    max_tokens=2048,
                    temperature=0.5,
                    stream=False
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
                last_error = f"JSON parse error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.info(f"🔄 Retrying immediately...")
                else:
                    logging.error(f"❌ All attempts failed. Last response: {response[:500]}")
                    
            except Exception as e:
                last_error = f"Generation error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.info(f"🔄 Retrying immediately...")
                else:
                    logging.error(f"❌ All attempts failed")
        
        raise Exception(f"Failed to generate badges after {max_attempts} attempts. Last error: {last_error}")
    
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
            "Start your response with 'Here is your answer:' followed by the JSON only. No markdown, no extra text.\n\n"
            '{"title": "Buying Guide: ' + keyword.title() + '", '
            '"sections": [{"heading": "Capacity & Size", "bullets": ["Consider your family size", "Check counter space"]}, '
            '{"heading": "Performance", "bullets": ["Look for higher wattage", "Check temperature range"]}]}\n\n'
            "Create 4-6 sections with 3-5 bullets each. No emojis, no prices.\n"
            f"Context: {keyword}"
        )
        
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logging.info(f"🔄 Buying guide generation attempt {attempt + 1}/{max_attempts}")
                
                response = self.client.generate(
                    prompt=prompt,
                    max_tokens=2048,
                    temperature=0.5,
                    stream=False
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
                last_error = f"JSON parse error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.info(f"🔄 Retrying immediately...")
                else:
                    logging.error(f"❌ All attempts failed. Last response: {response[:500]}")
                    
            except Exception as e:
                last_error = f"Generation error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.info(f"🔄 Retrying immediately...")
                else:
                    logging.error(f"❌ All attempts failed")
        
        raise Exception(f"Failed to generate buying guide after {max_attempts} attempts. Last error: {last_error}")
    
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
            "Start your response with 'Here is your answer:' followed by the JSON array only. No markdown, no extra text.\n\n"
            '[{"question": "What should I look for?", "answer": "Consider capacity, features..."}, '
            '{"question": "How do they compare?", "answer": "Main differences are..."}]\n\n'
            "Each answer should be 2-4 sentences. Cover buying tips, comparisons, features, value.\n"
            f"Context: {keyword}"
        )
        
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logging.info(f"🔄 FAQs generation attempt {attempt + 1}/{max_attempts}")
                
                response = self.client.generate(
                    prompt=prompt,
                    max_tokens=2048,
                    temperature=0.5,
                    stream=False
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
                last_error = f"JSON parse error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.info(f"🔄 Retrying immediately...")
                else:
                    logging.error(f"❌ All attempts failed. Last response: {response[:500]}")
                    
            except Exception as e:
                last_error = f"Generation error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.info(f"🔄 Retrying immediately...")
                else:
                    logging.error(f"❌ All attempts failed")
        
        raise Exception(f"Failed to generate FAQs after {max_attempts} attempts. Last error: {last_error}")
    
    def generate_product_reviews_batch(self, products: list, keyword: str) -> dict:
        """
        Generate product reviews for multiple products in a single API call (batch mode)
        
        Args:
            products: List of product dicts (max 10)
            keyword: Search keyword for context
            
        Returns:
            dict mapping ASIN to review:
            {
                "B08XYZ123": {
                    "description": "100-word description...",
                    "pros": ["Reason 1", "Reason 2", "Reason 3"],
                    "cons": ["Reason 1", "Reason 2"]
                },
                ...
            }
        """
        if not products:
            return {}
            
        logging.info(f"📝 Generating batch reviews for {len(products)} products...")
        
        # Build prompt with all products
        products_info = []
        for idx, product in enumerate(products, 1):
            title = product['title']
            if len(title) > 100:
                title = title[:97] + '…'
            
            features_text = '\n  '.join(f"- {f}" for f in (product['features'][:5] if product['features'] else []))
            
            product_text = (
                f"Product {idx} (ASIN: {product['asin']}):\n"
                f"  Title: {title}\n"
                f"  Brand: {product.get('brand', 'N/A')}\n"
                f"  Price: {product.get('price', 'N/A')}\n"
                f"  Features:\n  {features_text}\n"
            )
            products_info.append(product_text)
        
        all_products_text = '\n'.join(products_info)
        
        # Build example JSON structure
        example_json = '{\n'
        example_json += '  "B08XYZ123": {"description": "A 100-word description...", "pros": ["Great capacity", "Easy to use", "Durable build"], "cons": ["Pricey", "Heavy"]}'
        if len(products) > 1:
            example_json += ',\n  "B09ABC456": {"description": "Another 100-word description...", "pros": ["Compact design", "Fast performance"], "cons": ["Limited features"]}'
        example_json += '\n}'
        
        prompt = (
            f"Create product reviews for {len(products)} products with descriptions and pros/cons.\n"
            "Start your response with 'Here is your answer:' followed by the JSON only. No markdown, no extra text.\n\n"
            f"{example_json}\n\n"
            "Requirements for EACH product:\n"
            "- Description: Exactly 80-120 words, natural and engaging\n"
            "- Pros: 3-5 reasons to buy (short phrases, 3-6 words each)\n"
            "- Cons: 2-3 reasons not to buy (short phrases, 3-6 words each)\n"
            "- Be specific and helpful for buyers\n"
            "- Use the exact ASIN as the key\n\n"
            f"Context: {keyword}\n\n"
            f"Products:\n{all_products_text}"
        )
        
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logging.debug(f"🔄 Batch review attempt {attempt + 1}/{max_attempts}")
                
                response = self.client.generate(
                    prompt=prompt,
                    max_tokens=2048,  # Increased for multiple products
                    temperature=0.6,
                    stream=False
                )
                
                # Extract and parse JSON
                json_text = self._extract_json(response)
                reviews = json.loads(json_text)
                
                # Validate structure
                if not isinstance(reviews, dict):
                    raise ValueError("Reviews must be a dict")
                
                # Validate each review
                for asin, review in reviews.items():
                    if not isinstance(review, dict):
                        raise ValueError(f"Review for {asin} must be a dict")
                    
                    if 'description' not in review or 'pros' not in review or 'cons' not in review:
                        raise ValueError(f"Missing required fields for {asin}")
                    
                    if not isinstance(review['pros'], list) or not isinstance(review['cons'], list):
                        raise ValueError(f"Pros and cons must be lists for {asin}")
                
                # Log success
                total_words = sum(len(r['description'].split()) for r in reviews.values())
                logging.info(f"✅ Generated {len(reviews)} batch reviews ({total_words} total words)")
                
                return reviews
                
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.debug(f"🔄 Retrying...")
                    
            except Exception as e:
                last_error = f"Generation error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.debug(f"🔄 Retrying...")
        
        # Fallback if all attempts fail - create individual fallbacks
        logging.error(f"❌ Failed to generate batch reviews, using fallback for each product")
        fallback_reviews = {}
        for product in products:
            fallback_reviews[product['asin']] = {
                "description": f"This {product.get('brand', '')} product offers {' and '.join(product['features'][:3]) if product['features'] else 'great features'}. A solid choice for {keyword}.",
                "pros": ["Quality build", "Good features", "Reliable performance"],
                "cons": ["Price may vary", "Limited availability"]
            }
        return fallback_reviews

    def generate_product_review(self, product: dict, keyword: str) -> dict:
        """
        Generate product review with description + pros/cons
        
        Returns:
            {
                "description": "100-word description...",
                "pros": ["Reason 1", "Reason 2", "Reason 3"],
                "cons": ["Reason 1", "Reason 2"]
            }
        """
        logging.info(f"📝 Generating review for: {product['title'][:50]}...")
        
        # Build compact product info
        title = product['title']
        if len(title) > 100:
            title = title[:97] + '…'
        
        features_text = '\n'.join(f"- {f}" for f in (product['features'][:8] if product['features'] else []))
        
        prompt = (
            "Create a product review with description and pros/cons.\n"
            "Start your response with 'Here is your answer:' followed by the JSON only. No markdown, no extra text.\n\n"
            '{"description": "A 100-word description highlighting key features and use cases...", '
            '"pros": ["Great capacity", "Easy to use", "Durable build"], '
            '"cons": ["Pricey", "Heavy"]}\n\n'
            "Requirements:\n"
            "- Description: Exactly 80-120 words, natural and engaging\n"
            "- Pros: 3-5 reasons to buy (short phrases, 3-6 words each)\n"
            "- Cons: 2-3 reasons not to buy (short phrases, 3-6 words each)\n"
            "- Be specific and helpful for buyers\n\n"
            f"Context: {keyword}\n"
            f"Product: {title}\n"
            f"Brand: {product.get('brand', 'N/A')}\n"
            f"Price: {product.get('price', 'N/A')}\n"
            f"Features:\n{features_text}"
        )
        
        max_attempts = 3
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                logging.debug(f"🔄 Product review attempt {attempt + 1}/{max_attempts}")
                
                response = self.client.generate(
                    prompt=prompt,
                    max_tokens=512,
                    temperature=0.6,
                    stream=False
                )
                
                # Extract and parse JSON
                json_text = self._extract_json(response)
                review = json.loads(json_text)
                
                # Validate structure
                if not isinstance(review, dict):
                    raise ValueError("Review must be a dict")
                
                if 'description' not in review or 'pros' not in review or 'cons' not in review:
                    raise ValueError("Missing required fields")
                
                if not isinstance(review['pros'], list) or not isinstance(review['cons'], list):
                    raise ValueError("Pros and cons must be lists")
                
                # Validate word count
                word_count = len(review['description'].split())
                if word_count < 60 or word_count > 150:
                    logging.warning(f"⚠️ Description word count: {word_count} (expected 80-120)")
                
                logging.info(f"✅ Generated review ({word_count} words, {len(review['pros'])} pros, {len(review['cons'])} cons)")
                return review
                
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.debug(f"🔄 Retrying...")
                    
            except Exception as e:
                last_error = f"Generation error: {e}"
                logging.warning(f"⚠️ Attempt {attempt + 1}/{max_attempts} - {last_error}")
                if attempt < max_attempts - 1:
                    logging.debug(f"🔄 Retrying...")
        
        # Fallback if all attempts fail
        logging.error(f"❌ Failed to generate review, using fallback")
        return {
            "description": f"This {product.get('brand', '')} product offers {' and '.join(product['features'][:3]) if product['features'] else 'great features'}. A solid choice for {keyword}.",
            "pros": ["Quality build", "Good features", "Reliable performance"],
            "cons": ["Price may vary", "Limited availability"]
        }

    def generate_all_content_parallel(self, keyword: str, products: list) -> dict:
        """
        Generate all content sections with controlled concurrency (max 3 concurrent requests)
        Product reviews are batched 2 products at a time for optimal API usage
        
        Strategy:
        - Submit all tasks to ThreadPoolExecutor (max_workers=3)
        - First 3 tasks run immediately
        - Remaining tasks queued automatically
        - After each completion: wait 1s, next task auto-starts
        
        Tasks breakdown:
        - 4 content tasks: intro, badges, guide, faqs
        - 5 review batches: 2 products each (10 products total)
        Total: 9 tasks with max 3 running concurrently
        
        Args:
            keyword: Search keyword
            products: List of product data (10 products)
            
        Returns:
            dict: All generated content sections
            
        Raises:
            Exception: If any section fails after retries
        """
        logging.info("🚀 Starting parallel content generation (max 3 concurrent, 2 products/batch, 1s delay)...")
        
        results = {}
        
        # Split products into batches of 2
        batch_size = 2
        review_batches = []
        for i in range(0, len(products), batch_size):
            batch = products[i:i+batch_size]
            review_batches.append(batch)
        
        logging.info(f"📦 Created {len(review_batches)} review batches (2 products each)")
        
        # Prepare all tasks as (name, function, args)
        tasks = [
            ('intro', self.generate_intro, (keyword,)),
            ('badges', self.generate_badges, (keyword, products)),
            ('guide', self.generate_buying_guide, (keyword, products)),
            ('faqs', self.generate_faqs, (keyword, products))
        ]
        
        # Add review batch tasks
        for idx, batch in enumerate(review_batches, 1):
            tasks.append((f'review_batch_{idx}', self.generate_product_reviews_batch, (batch, keyword)))
        
        logging.info(f"📋 Total tasks: {len(tasks)} (4 content + {len(review_batches)} review batches)")
        
        from concurrent.futures import as_completed
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit all tasks (executor will queue them automatically)
            futures = {}
            for name, func, args in tasks:
                future = executor.submit(self._generate_with_retry, func, *args)
                futures[future] = name
                logging.info(f"📤 Submitted: {name}")
            
            logging.info(f"✅ All {len(tasks)} tasks submitted! Max 3 running concurrently...")
            
            # Collect results as they complete (in any order)
            reviews_map = {}
            completed_count = 0
            
            for future in as_completed(futures):
                name = futures[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    
                    # Store result based on task name
                    if name == 'intro':
                        results['intro'] = result
                    elif name == 'badges':
                        results['badges'] = result
                    elif name == 'guide':
                        results['guide'] = result
                    elif name == 'faqs':
                        results['faqs'] = result
                    elif name.startswith('review_batch_'):
                        # Merge review results
                        reviews_map.update(result)
                    
                    logging.info(f"✅ {name} complete ({completed_count}/{len(tasks)})")
                    
                    # Wait 1s after each completion (except last one)
                    if completed_count < len(tasks):
                        logging.info("⏳ Waiting 1s before next task...")
                        time.sleep(1)
                    
                except Exception as e:
                    logging.error(f"❌ {name} failed: {e}")
                    raise
            
            results['reviews'] = reviews_map
        
        logging.info(f"\n✅ All parallel content generation complete! Total reviews: {len(reviews_map)}")
        return results

    def generate_info_article(self, keyword: str) -> dict:
        """
        Generate informational/educational article (no affiliate links)
        
        Structure:
        - Intro (educational tone)
        - Body sections (4-6 H2 with educational content)
        - FAQs
        - Conclusion (educational summary)
        
        Args:
            keyword: The topic keyword (e.g., "how to cook beef ribs")
            
        Returns:
            {
                "intro": "Educational intro paragraph...",
                "sections": [
                    {"heading": "Understanding the Basics", "content": "Paragraph content..."},
                    {"heading": "Step-by-Step Process", "content": "Paragraph content..."}
                ],
                "faqs": [
                    {"question": "...", "answer": "..."}
                ],
                "conclusion": "Closing paragraph..."
            }
        """
        logging.info(f"📚 Generating INFO article for: {keyword}")
        
        # Generate intro
        logging.info("📝 Generating intro...")
        intro_prompt = (
            f'Write a 80-word engaging introduction for an educational article about "{keyword}". '
            'Be conversational and informative. '
            'Start your response with "Here is your answer:" followed by the paragraph. '
            'No markdown, no bold formatting, no extra explanations.'
        )
        
        intro = self._generate_with_retry(
            self.client.generate,
            prompt=intro_prompt,
            max_tokens=512,
            temperature=0.2,
            stream=True,
            model_override='qwen-3-235b-a22b-instruct-2507'
        )
        intro = self._clean_intro(intro)
        intro = re.sub(r'\*\*(.+?)\*\*', r'\1', intro)  # Remove bold
        logging.info(f"✅ Intro generated ({len(intro.split())} words)")
        
        # Generate body sections
        logging.info("📝 Generating body sections...")
        sections_prompt = (
            f"Create 4-6 educational sections about '{keyword}'.\n"
            "Start your response with 'Here is your answer:' followed by the JSON only. No markdown, no extra text.\n\n"
            '[{"heading": "Understanding the Basics", "subpoints": [{"subheading": "Core principles", "content": "Educational paragraph..."}, {"subheading": "Key terms", "content": "Educational paragraph..."}]}, '
            '{"heading": "Key Techniques", "subpoints": [{"subheading": "Practical steps", "content": "Educational paragraph..."}, {"subheading": "Tips", "content": "Educational paragraph..."}]}]\n\n'
            "Requirements:\n"
            "- Each section: heading (H2) + 2-4 subpoints (H3)\n"
            "- Each subpoint content: 70-110 words, easy to read, short sentences\n"
            "- Include 1-2 bolded key points using **like this** (markdown) in each subpoint\n"
            "- Conversational, practical, no affiliate or product mentions\n\n"
            f"Topic: {keyword}"
        )
        
        sections = self._generate_with_retry(
            self._generate_json_content,
            sections_prompt,
            max_tokens=2048,
            temperature=0.6
        )
        logging.info(f"✅ Generated {len(sections)} body sections")
        
        # Generate FAQs
        logging.info("❓ Generating FAQs...")
        faqs_prompt = (
            f"Create 5-8 helpful FAQs about '{keyword}'.\n"
            "Start your response with 'Here is your answer:' followed by the JSON array only. No markdown, no extra text.\n\n"
            '[{"question": "What is...?", "answer": "Educational answer in 2-3 sentences..."}, '
            '{"question": "How do I...?", "answer": "Practical guidance..."}]\n\n'
            "Requirements:\n"
            "- Common questions learners ask\n"
            "- Clear, helpful answers (2-4 sentences each)\n"
            "- No product recommendations\n\n"
            f"Topic: {keyword}"
        )
        
        faqs = self._generate_with_retry(
            self._generate_json_content,
            faqs_prompt,
            max_tokens=2048,
            temperature=0.5
        )
        logging.info(f"✅ Generated {len(faqs)} FAQs")
        
        # Generate conclusion
        logging.info("📝 Generating conclusion...")
        conclusion_prompt = (
            f'Write a 60-80 word conclusion for the article about "{keyword}". '
            'Summarize key takeaways and encourage readers. '
            'Start your response with "Here is your answer:" followed by the paragraph. '
            'No markdown, no extra explanations.'
        )
        
        conclusion = self._generate_with_retry(
            self.client.generate,
            prompt=conclusion_prompt,
            max_tokens=512,
            temperature=0.2,
            stream=True,
            model_override='qwen-3-235b-a22b-instruct-2507'
        )
        conclusion = self._clean_intro(conclusion)
        conclusion = re.sub(r'\*\*(.+?)\*\*', r'\1', conclusion)  # Remove bold
        logging.info(f"✅ Conclusion generated ({len(conclusion.split())} words)")
        
        result = {
            "intro": intro,
            "sections": sections,
            "faqs": faqs,
            "conclusion": conclusion
        }
        
        logging.info("✅ INFO article generation complete!")
        return result

    def _generate_json_content(self, prompt: str, max_tokens: int, temperature: float) -> list:
        """Helper to generate and parse JSON content from ChatZai"""
        response = self.client.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=False
        )
        
        # Extract and parse JSON
        json_text = self._extract_json(response)
        data = json.loads(json_text)
        
        if not isinstance(data, list):
            raise ValueError("Response must be a JSON array")
        
        return data
