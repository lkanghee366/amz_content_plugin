"""
Cerebras AI Handler with API Key Rotation
Based on cerebras_client_standalone.py
"""
import os
import time
import logging
from cerebras.cloud.sdk import Cerebras

# Enable DEBUG level logging for this module
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class CerebrasClient:
    """Cerebras API client with automatic key rotation"""
    
    def __init__(self, api_keys_file: str, model: str = "gpt-oss-120b", cache_file: str = "cerebras_key_cache.txt"):
        """Initialize Cerebras client with API keys from file"""
        self.model = model
        self.cache_file = cache_file
        
        # Load API keys
        if not os.path.exists(api_keys_file):
            raise FileNotFoundError(f"API keys file not found: {api_keys_file}")
        
        self.api_keys = []
        with open(api_keys_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.split("#", 1)[0].strip()
                if line:
                    self.api_keys.append(line)
        
        if not self.api_keys:
            raise ValueError(f"No API keys found in {api_keys_file}")
        
        logging.info(f"Loaded {len(self.api_keys)} Cerebras API key(s)")
        
        # Initialize client state
        self.key_index = 0
        self._real_client = None
        self.failed_keys = set()  # Cache failed keys to avoid retrying
        
        # Load cached key index
        cached_index = self._load_key_cache()
        if cached_index is not None:
            logging.info(f"📂 Found cached key index: #{cached_index}")
            self._init_client(cached_index)
        else:
            self._init_client(0)
    
    def _load_key_cache(self) -> int:
        """Load cached key index from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content.isdigit():
                        index = int(content)
                        if 0 <= index < len(self.api_keys):
                            return index
                        else:
                            logging.warning(f"⚠️ Cached index {index} out of range, ignoring")
            return None
        except Exception as e:
            logging.warning(f"⚠️ Failed to load key cache: {e}")
            return None
    
    def _save_key_cache(self):
        """Save current key index to cache file"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                f.write(str(self.key_index))
            logging.debug(f"💾 Saved key cache: #{self.key_index}")
        except Exception as e:
            logging.warning(f"⚠️ Failed to save key cache: {e}")
    
    def _init_client(self, key_index: int) -> bool:
        """Initialize Cerebras client with specific key index"""
        try:
            key = self.api_keys[key_index]
            # Disable SDK auto-retry to handle retries manually with key rotation
            self._real_client = Cerebras(api_key=key, max_retries=0)
            self.key_index = key_index
            self._save_key_cache()  # Save immediately after successful init
            logging.info(f"✅ Initialized Cerebras client with key #{key_index}")
            return True
        except Exception as e:
            logging.warning(f"⚠️ Failed to initialize with key #{key_index}: {e}")
            return False
    
    def _rotate_key(self) -> bool:
        """Rotate to next API key, skipping failed ones"""
        if len(self.api_keys) <= 1:
            logging.warning("Only 1 API key available, cannot rotate")
            return False
        
        # Find next available key that hasn't failed
        attempts = 0
        while attempts < len(self.api_keys):
            next_index = (self.key_index + 1 + attempts) % len(self.api_keys)
            
            # Skip failed keys
            if next_index in self.failed_keys:
                logging.info(f"⏭️ Skipping key #{next_index} (previously failed)")
                attempts += 1
                continue
            
            if self._init_client(next_index):
                logging.info(f"🔄 Rotated to API key #{next_index}")
                self._save_key_cache()  # Save after successful rotation
                return True
            else:
                # Mark as failed
                self.failed_keys.add(next_index)
                logging.warning(f"⚠️ Marked key #{next_index} as failed")
                attempts += 1
        
        logging.error("❌ No available API keys after rotation (all tried or failed)")
        return False
    
    def generate(self, prompt: str, max_tokens: int = 1024, temperature: float = 0.7, stream: bool = False, use_reasoning: bool = True, model_override: str = None) -> str:
        """Generate text using Cerebras AI with retry logic
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Enable streaming response
            use_reasoning: Add reasoning_effort parameter (for gpt-oss-120b)
            model_override: Override default model (e.g., 'llama-3.3-70b' for intro)
        """
        attempts = 0
        max_attempts = len(self.api_keys) * 2
        
        # Use override model if specified, otherwise use default
        model_to_use = model_override if model_override else self.model
        
        while attempts < max_attempts:
            try:
                if self._real_client is None:
                    raise RuntimeError("Cerebras client not initialized")
                
                # Build request parameters
                request_params = {
                    "model": model_to_use,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_completion_tokens": max_tokens,
                    "temperature": temperature,
                    "stream": stream
                }
                
                # Only add reasoning_effort if use_reasoning is True AND using gpt-oss-120b
                if use_reasoning and model_to_use == "gpt-oss-120b":
                    request_params["reasoning_effort"] = "medium"
                
                response = self._real_client.chat.completions.create(**request_params)
                
                # Handle streaming response
                if stream:
                    content = ""
                    chunk_count = 0
                    for chunk in response:
                        chunk_count += 1
                        if chunk.choices and len(chunk.choices) > 0:
                            delta = chunk.choices[0].delta
                            if hasattr(delta, 'content') and delta.content:
                                content += delta.content
                    
                    logging.debug(f"📊 Streaming: received {chunk_count} chunks, total {len(content)} chars")
                    
                    if not content:
                        logging.warning("⚠️ Empty content from streaming response")
                    
                    return content
                else:
                    # Non-streaming: get full response
                    logging.debug(f"📊 Response object type: {type(response)}")
                    logging.debug(f"📊 Response choices: {len(response.choices) if hasattr(response, 'choices') else 'N/A'}")
                    
                    if not response.choices or len(response.choices) == 0:
                        logging.error(f"❌ No choices in response! Full response: {response}")
                        return ""
                    
                    message = response.choices[0].message
                    content = message.content if hasattr(message, 'content') and message.content else None
                    
                    # gpt-oss-120b sometimes returns content in 'reasoning' field instead of 'content'
                    if not content and hasattr(message, 'reasoning') and message.reasoning:
                        logging.info("📝 Using 'reasoning' field as model returned content there")
                        content = message.reasoning
                    
                    logging.debug(f"📊 Content length: {len(content) if content else 0} chars")
                    
                    if not content:
                        logging.warning(f"⚠️ Empty content from response. Message object: {message}")
                        logging.warning(f"⚠️ Full response object: {response}")
                    else:
                        logging.debug(f"📝 First 200 chars: {content[:200]}...")
                    
                    # Save cache after successful generation
                    self._save_key_cache()
                    
                    return content if content else ""
                
            except Exception as e:
                err_str = str(e).lower()
                
                # Check for rate limit or auth errors
                if any(code in err_str for code in ["429", "401", "403", "too_many_requests", "unauthorized", "forbidden"]):
                    current_key = self.key_index
                    logging.warning(f"⚠️ API error with key #{current_key}: {e}")
                    
                    # Mark current key as failed
                    self.failed_keys.add(current_key)
                    logging.info(f"🔒 Marked key #{current_key} as failed")
                    
                    logging.info(f"🔄 Attempting key rotation (attempt {attempts + 1}/{max_attempts})")
                    
                    if not self._rotate_key():
                        logging.error("❌ All API keys exhausted")
                        raise Exception(f"All Cerebras API keys failed: {e}")
                    
                    # Exponential backoff
                    wait_time = min(2 ** (attempts // len(self.api_keys)), 30)
                    logging.info(f"⏱️ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                    attempts += 1
                    continue
                else:
                    # Non-recoverable error
                    logging.error(f"❌ Non-recoverable error: {e}")
                    raise
        
        raise Exception(f"Failed after {max_attempts} attempts")
