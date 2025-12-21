"""
AI Content Generator using Unified AI Client
Generates: Intro, Badges, Editor's Choice, Buying Guide, FAQs
"""
import json
import re
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from unified_ai_client import UnifiedAIClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class AIContentGenerator:
    """Generate article content using Unified AI Client (ChatZai + Cerebras fallback)"""
    
    def __init__(self, ai_client: UnifiedAIClient):
        """Initialize with Unified AI client"""
        self.client = ai_client
        self.max_retries = 3
    
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
    
    def generate_all_content_parallel(self, keyword: str, products: list) -> dict:
        """
        Generate all content sections in parallel (max 2 concurrent)
        2 Waves: Intro+Badges, Guide+FAQs
        
        Args:
            keyword: Search keyword
            products: List of product data
            
        Returns:
            dict: All generated content sections
            
        Raises:
            Exception: If any section fails after retries
        """
        logging.info("🚀 Starting parallel content generation (2 waves)...")
        
        results = {}
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Wave 1: Intro + Badges (all 10 products at once)
            logging.info("\n⚡ Wave 1: Generating Intro + Badges (10 products) in parallel...")
            
            future_intro = executor.submit(self._generate_with_retry, self.generate_intro, keyword)
            future_badges = executor.submit(self._generate_with_retry, self.generate_badges, keyword, products)
            
            # Wait for Wave 1 to complete
            try:
                logging.info("📝 Waiting for Intro...")
                results['intro'] = future_intro.result()
                logging.info("✅ Intro complete")
            except Exception as e:
                logging.error(f"❌ Intro failed after all retries: {e}")
                raise
            
            try:
                logging.info("🏆 Waiting for Badges...")
                results['badges'] = future_badges.result()
                logging.info("✅ Badges complete")
            except Exception as e:
                logging.error(f"❌ Badges failed after all retries: {e}")
                raise
            
            # Wave 2: Guide + FAQs (parallel)
            logging.info("\n⚡ Wave 2: Generating Guide + FAQs in parallel...")
            
            future_guide = executor.submit(self._generate_with_retry, self.generate_buying_guide, keyword, products)
            future_faqs = executor.submit(self._generate_with_retry, self.generate_faqs, keyword, products)
            
            # Wait for Wave 2 to complete
            try:
                logging.info("📚 Waiting for Buying Guide...")
                results['guide'] = future_guide.result()
                logging.info("✅ Guide complete")
            except Exception as e:
                logging.error(f"❌ Guide failed after all retries: {e}")
                raise
            
            try:
                logging.info("❓ Waiting for FAQs...")
                results['faqs'] = future_faqs.result()
                logging.info("✅ FAQs complete")
            except Exception as e:
                logging.error(f"❌ FAQs failed after all retries: {e}")
                raise
        
        # Wave 3: Product Reviews (3 batches parallel - max 2 at a time)
        logging.info("\n⚡ Wave 3: Generating Product Reviews in 3 batches...")
        
        # Split products into 3 batches
        batch1 = products[0:3]   # 3 products
        batch2 = products[3:6]   # 3 products  
        batch3 = products[6:10]  # 4 products
        
        # Wave 3a: Batch 1 + Batch 2 (parallel)
        logging.info("\n  Wave 3a: Review Batch 1 (3 prods) + Batch 2 (3 prods) in parallel...")
        
        future_review1 = executor.submit(self._generate_with_retry, self.generate_product_reviews_batch, batch1, keyword)
        future_review2 = executor.submit(self._generate_with_retry, self.generate_product_reviews_batch, batch2, keyword)
        
        reviews_map = {}
        
        try:
            logging.info("📝 Waiting for Review Batch 1...")
            batch1_reviews = future_review1.result()
            reviews_map.update(batch1_reviews)
            logging.info(f"✅ Review Batch 1 complete ({len(batch1_reviews)} reviews)")
        except Exception as e:
            logging.error(f"❌ Review Batch 1 failed after all retries: {e}")
            raise
        
        try:
            logging.info("📝 Waiting for Review Batch 2...")
            batch2_reviews = future_review2.result()
            reviews_map.update(batch2_reviews)
            logging.info(f"✅ Review Batch 2 complete ({len(batch2_reviews)} reviews)")
        except Exception as e:
            logging.error(f"❌ Review Batch 2 failed after all retries: {e}")
            raise
        
        # Wave 3b: Batch 3 (single)
        logging.info("\n  Wave 3b: Review Batch 3 (4 prods)...")
        
        try:
            batch3_reviews = self._generate_with_retry(self.generate_product_reviews_batch, batch3, keyword)
            reviews_map.update(batch3_reviews)
            logging.info(f"✅ Review Batch 3 complete ({len(batch3_reviews)} reviews)")
        except Exception as e:
            logging.error(f"❌ Review Batch 3 failed after all retries: {e}")
            raise
        
        results['reviews'] = reviews_map
        
        logging.info(f"\n✅ All parallel content generation complete! Total reviews: {len(reviews_map)}")
        return results
    
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
    
    def generate_badges_batch(self, keyword: str, products: list, batch_name: str = "Batch") -> dict:
        """
        Generate badges for a batch of products (3-4 products)
        
        Args:
            keyword: Search keyword
            products: List of 3-4 products
            batch_name: Name for logging (e.g., "Batch 1")
            
        Returns:
            {
                "badges": [
                    {"asin": "B0XXX", "badge": "Best overall"},
                    {"asin": "B0YYY", "badge": "Best value"}
                ]
            }
        """
        logging.info(f"🏷️ Generating badges for {batch_name}: {len(products)} products")
        
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
            f"Create product badges for ALL {len(compact)} products in this batch.\n\n"
            "CRITICAL REQUIREMENTS:\n"
            "1. You MUST create a badge for EVERY SINGLE product listed below\n"
            "2. Each badge must be a purposeful 2-3 word phrase that clearly reflects the product's unique strength, use case, or standout feature\n"
            "3. Avoid generic labels unless they truly match the product; make badges feel human and specific\n"
            "4. Draw inspiration from the brand, title, and feature list for each product when crafting the badge\n"
            "5. Examples of acceptable style: \"Rain-Ready Seating\", \"Compact Bistro Choice\", \"Premium Teak Craft\"\n\n"
            f"MANDATORY: Return badges for ALL {len(compact)} products.\n\n"
            "JSON FORMAT (no markdown, no extra text):\n"
            '{"badges": [{"asin": "ASIN1", "badge": "Best overall"}, {"asin": "ASIN2", "badge": "Best value"}]}\n\n'
            f"ALL ASINs that MUST be included:\n{', '.join(all_asins)}\n\n"
            f"Context: {keyword}\n"
            f"Products: {json.dumps(compact, ensure_ascii=False)}"
        )
        
        response = self.client.generate(
            prompt=prompt,
            max_tokens=1024,
            temperature=0.5,
            stream=False
        )
        
        logging.debug(f"📦 Raw badges response: {len(response)} chars")
        
        # Extract and parse JSON
        json_text = self._extract_json(response)
        data = json.loads(json_text)
        
        # Validate structure
        if 'badges' not in data:
            raise ValueError("Missing badges in response")
        
        if not isinstance(data['badges'], list):
            raise ValueError("badges must be a list")
        
        logging.info(f"✅ Generated {len(data['badges'])} badges for {batch_name}")
        return data
    
    def generate_badges(self, keyword: str, products: list) -> dict:
        """
        Generate badges for all products at once + select top recommendation
        
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
                'features': product['features'][:5] if product['features'] else []
            })
            all_asins.append(product['asin'])
        
        prompt = (
            "IMPORTANT: Output ONLY the JSON, no explanations.\n\n"
            f"Create badges for ALL {len(compact)} products + select 1 top recommendation.\n\n"
            "REQUIREMENTS:\n"
            "1. MUST create a badge for EVERY product\n"
            "2. Each badge: 2-3 words reflecting unique strength\n"
            "3. Pick ONE product as top_recommendation\n\n"
            "JSON FORMAT:\n"
            '{"top_recommendation": {"asin": "B0XXX"}, "badges": ['
            '{"asin": "B0XXX", "badge": "Best overall"}, ...]}\n\n'
            f"ALL ASINs REQUIRED: {', '.join(all_asins)}\n\n"
            f"Context: {keyword}\n"
            f"Products: {json.dumps(compact, ensure_ascii=False)}"
        )
        
        response = self.client.generate(
            prompt=prompt,
            max_tokens=2048,
            temperature=0.5,
            stream=False
        )
        
        # Extract and parse JSON
        json_text = self._extract_json(response)
        data = json.loads(json_text)
        
        # Validate structure
        if 'top_recommendation' not in data or 'badges' not in data:
            raise ValueError("Missing top_recommendation or badges in response")
        
        if not isinstance(data['badges'], list):
            raise ValueError("badges must be a list")
        
        logging.info(f"✅ Generated {len(data['badges'])} badges, top: {data['top_recommendation']['asin']}")
        return data
    
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
            f"Context: {keyword}"
        )
        
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
            f"Context: {keyword}"
        )
        
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
            "IMPORTANT: Return ONLY valid JSON (no markdown, no extra text):\n\n"
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
            "IMPORTANT: Return ONLY this exact JSON format (no markdown, no extra text):\n\n"
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
