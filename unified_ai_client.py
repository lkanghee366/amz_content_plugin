"""
Unified AI Client - Manages multiple AI providers with smart fallback
"""
import logging
import time
from typing import Optional
from chat_zai_client import ChatZaiClient
from cerebras_client import CerebrasClient

logger = logging.getLogger(__name__)


class UnifiedAIClient:
    """Unified client that manages ChatZai (primary) and Cerebras (fallback)"""
    
    def __init__(self, chat_zai_client: ChatZaiClient, cerebras_client: CerebrasClient):
        """
        Initialize unified client with both providers
        
        Args:
            chat_zai_client: ChatZai API client (primary)
            cerebras_client: Cerebras API client (fallback)
        """
        self.chat_zai = chat_zai_client
        self.cerebras = cerebras_client
        
        # Stats tracking
        self.stats = {
            'chat_zai_success': 0,
            'chat_zai_failed': 0,
            'cerebras_success': 0,
            'cerebras_failed': 0,
            'total_requests': 0
        }
        
        # Check initial health
        self.chat_zai_healthy = self.chat_zai.health_check()
        if self.chat_zai_healthy:
            logger.info("✓ ChatZai API is healthy and ready")
        else:
            logger.warning("✗ ChatZai API is not responding, will use Cerebras fallback")
    
    def _parse_response(self, text: str) -> str:
        """Parse response and remove 'Here is your answer' prefix"""
        import re
        # Case-insensitive search for "Here is your answer"
        match = re.search(r'here\s+is\s+your\s+answer[:\s]*', text, re.IGNORECASE)
        if match:
            return text[match.end():].strip()
        return text.strip()
    
    def generate(self, prompt: str, system_prompt: Optional[str] = None,
                 max_tokens: int = 4000, temperature: float = 0.7, 
                 stream: bool = False, use_reasoning: bool = True, 
                 model_override: Optional[str] = None) -> str:
        """
        Generate text using primary provider with automatic fallback
        
        Args:
            prompt: User prompt text
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation (0.0-1.0)
            stream: Enable streaming (only for Cerebras)
            use_reasoning: Add reasoning effort (only for Cerebras)
            model_override: Override model (only for Cerebras)
            
        Returns:
            str: Generated text
            
        Raises:
            Exception: If ChatZai fails after retries
        """
        self.stats['total_requests'] += 1
        
        # Use ChatZai only (with built-in 3 retries)
        try:
            logger.info("🌐 Using ChatZai")
            response = self.chat_zai.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            # Check if response is too short (likely incomplete)
            if len(response.strip()) < 50:
                logger.warning(f"⚠️ ChatZai returned very short response ({len(response)} chars), may be incomplete")
                raise Exception("ChatZai response too short, likely incomplete")
            
            self.stats['chat_zai_success'] += 1
            logger.info("✓ ChatZai generation successful")
            
            # Auto-parse <start>...</end> tags
            response = self._parse_response(response)
            
            return response
            
        except Exception as e:
            logger.error(f"✗ ChatZai failed after retries: {e}")
            self.stats['chat_zai_failed'] += 1
            raise Exception(f"ChatZai generation failed: {e}")
        except Exception as e:
            logger.error(f"✗ Cerebras failed: {e}")
            self.stats['cerebras_failed'] += 1
            raise Exception(f"Both AI providers failed. ChatZai: {self.stats['chat_zai_failed']}, Cerebras: {self.stats['cerebras_failed']}")
    
    def get_stats(self) -> dict:
        """
        Get usage statistics
        
        Returns:
            dict: Statistics about provider usage
        """
        return {
            **self.stats,
            'chat_zai_healthy': self.chat_zai_healthy,
            'success_rate': (
                (self.stats['chat_zai_success'] + self.stats['cerebras_success']) / 
                max(self.stats['total_requests'], 1)
            ) * 100
        }
    
    def print_stats(self):
        """Print usage statistics"""
        stats = self.get_stats()
        logger.info("=" * 60)
        logger.info("AI Provider Statistics:")
        logger.info(f"  Total Requests: {stats['total_requests']}")
        logger.info(f"  ChatZai Success: {stats['chat_zai_success']}")
        logger.info(f"  ChatZai Failed: {stats['chat_zai_failed']}")
        logger.info(f"  Cerebras Success: {stats['cerebras_success']}")
        logger.info(f"  Cerebras Failed: {stats['cerebras_failed']}")
        logger.info(f"  Overall Success Rate: {stats['success_rate']:.1f}%")
        logger.info(f"  ChatZai Health: {'✓ Healthy' if stats['chat_zai_healthy'] else '✗ Unhealthy'}")
        logger.info("=" * 60)
    
    def close(self):
        """Close all client connections"""
        self.chat_zai.close()
        # Cerebras client doesn't need closing
