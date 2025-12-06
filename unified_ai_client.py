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
            # Rotate context on startup for fresh start
            logger.info("🔄 Rotating context on startup for fresh session...")
            self.chat_zai.rotate_context()
        else:
            logger.warning("✗ ChatZai API is not responding, will use Cerebras fallback")
    
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
            Exception: If both providers fail
        """
        self.stats['total_requests'] += 1
        
        # Try ChatZai first if healthy
        if self.chat_zai_healthy:
            try:
                logger.info("🌐 Using ChatZai (primary provider)")
                response = self.chat_zai.generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                # Check if JSON response is complete
                response_stripped = response.strip()
                if response_stripped.startswith('{') or response_stripped.startswith('['):
                    # It's JSON, validate completeness
                    if response_stripped.startswith('{') and not response_stripped.endswith('}'):
                        logger.warning("⚠️ ChatZai returned incomplete JSON (missing closing brace)")
                        raise Exception("Incomplete JSON response from ChatZai")
                    elif response_stripped.startswith('[') and not response_stripped.endswith(']'):
                        logger.warning("⚠️ ChatZai returned incomplete JSON (missing closing bracket)")
                        raise Exception("Incomplete JSON response from ChatZai")
                
                self.stats['chat_zai_success'] += 1
                logger.info("✓ ChatZai generation successful")
                
                # Rotate context after successful response
                logger.info("🔄 Rotating context after successful request...")
                rotate_success = self.chat_zai.rotate_context()
                
                if rotate_success:
                    logger.info("✓ Rotation complete, context is fresh")
                else:
                    logger.warning("⚠️ Rotation failed, continuing anyway")
                
                # Rate limiting: wait 3 seconds before next request
                logger.info("⏳ Waiting 3 seconds before next request...")
                time.sleep(3)
                
                return response
                
            except Exception as e:
                logger.error(f"✗ ChatZai failed: {e}")
                self.stats['chat_zai_failed'] += 1
                # Mark as unhealthy for next check
                self.chat_zai_healthy = False
                logger.info("→ Falling back to Cerebras...")
        else:
            logger.info("⚠ ChatZai unhealthy, using Cerebras directly")
        
        # Fallback to Cerebras
        try:
            logger.info("🧠 Using Cerebras (fallback provider)")
            # Cerebras doesn't support system_prompt parameter, merge it with prompt
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = self.cerebras.generate(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
                use_reasoning=use_reasoning,
                model_override=model_override
            )
            self.stats['cerebras_success'] += 1
            logger.info("✓ Cerebras generation successful")
            
            # Rate limiting: wait 3 seconds before next request (no rotation for Cerebras)
            logger.info("⏳ Waiting 3 seconds before next request...")
            time.sleep(3)
            
            # Try to restore ChatZai health for next request
            self.chat_zai_healthy = self.chat_zai.health_check()
            
            return response
            
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
