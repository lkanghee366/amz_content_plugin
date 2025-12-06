"""
ChatZai API Client - Wrapper for chat.z.ai Node.js API
"""
import requests
import logging
import time
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ChatZaiClient:
    """Client for chat.z.ai API running on Node.js server"""
    
    def __init__(self, api_url: str = "http://localhost:3001", timeout: int = 120, max_retries: int = 3):
        """
        Initialize ChatZai client
        
        Args:
            api_url: Base URL of the chat.z.ai API server
            timeout: Request timeout in seconds (default 120 for long responses)
            max_retries: Maximum number of retry attempts
        """
        self.api_url = api_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        
    def health_check(self) -> bool:
        """
        Check if the API server is running and healthy
        
        Returns:
            bool: True if server is healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.api_url}/health",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"ChatZai health check failed: {e}")
            return False
    
    def rotate_context(self) -> bool:
        """
        Force rotate context to start fresh conversation
        
        Returns:
            bool: True if rotation successful, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.api_url}/rotate",
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✓ Context rotated")
                return True
            else:
                logger.warning(f"⚠️ Context rotation failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Context rotation error: {e}")
            return False
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None, 
                 max_tokens: int = 4000, temperature: float = 0.7) -> str:
        """
        Generate text using chat.z.ai API
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0.0-1.0)
            
        Returns:
            str: Generated text
            
        Raises:
            Exception: If generation fails after all retries
        """
        payload = {
            "prompt": prompt,
            "systemPrompt": system_prompt,
            "maxTokens": max_tokens,
            "temperature": temperature
        }
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                logger.info(f"ChatZai generation attempt {attempt + 1}/{self.max_retries}")
                
                response = self.session.post(
                    f"{self.api_url}/ask",
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # Handle both 'response' and 'answer' fields
                    if 'response' in data:
                        result = data['response']
                        logger.info(f"ChatZai generated {len(result)} characters")
                        # Check if response looks incomplete (for JSON)
                        if result.strip().startswith('{') and not result.strip().endswith('}'):
                            logger.warning(f"⚠️ Response may be incomplete (missing closing brace)")
                        return result
                    elif 'answer' in data:
                        result = data['answer']
                        logger.info(f"ChatZai generated {len(result)} characters")
                        # Check if response looks incomplete (for JSON)
                        if result.strip().startswith('{') and not result.strip().endswith('}'):
                            logger.warning(f"⚠️ Response may be incomplete (missing closing brace)")
                        return result
                    else:
                        raise Exception(f"Invalid response format: {data}")
                else:
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout as e:
                last_error = f"Request timeout after {self.timeout}s: {e}"
                logger.warning(f"{last_error} (attempt {attempt + 1}/{self.max_retries})")
                
            except requests.exceptions.ConnectionError as e:
                last_error = f"Connection error: {e}"
                logger.warning(f"{last_error} (attempt {attempt + 1}/{self.max_retries})")
                
            except Exception as e:
                last_error = f"Generation error: {e}"
                logger.warning(f"{last_error} (attempt {attempt + 1}/{self.max_retries})")
            
            # Wait before retry (fixed 10 second delay)
            if attempt < self.max_retries - 1:
                wait_time = 10  # 10s between retries
                logger.info(f"Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
        
        # All retries failed
        raise Exception(f"ChatZai generation failed after {self.max_retries} attempts. Last error: {last_error}")
    
    def close(self):
        """Close the session"""
        self.session.close()
