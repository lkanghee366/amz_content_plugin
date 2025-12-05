"""
WordPress REST API Client
Posts content to WordPress via REST API
"""
import requests
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WordPressAPI:
    """WordPress REST API client for posting articles"""
    
    def __init__(self, site_url: str, username: str, app_password: str):
        """
        Initialize WordPress API client
        
        Args:
            site_url: WordPress site URL (e.g., https://yoursite.com)
            username: WordPress username
            app_password: WordPress Application Password
        """
        self.site_url = site_url.rstrip('/')
        self.username = username
        self.app_password = app_password
        self.api_base = f"{self.site_url}/wp-json/wp/v2"
        
        # Create session with auth
        self.session = requests.Session()
        self.session.auth = (username, app_password)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'Amazon-WP-Poster/1.0'
        })
        
        logging.info(f"✅ WordPress API initialized: {self.site_url}")
    
    def test_connection(self) -> bool:
        """Test API connection and authentication"""
        try:
            response = self.session.get(f"{self.api_base}/users/me")
            if response.status_code == 200:
                user = response.json()
                logging.info(f"✅ Connected as: {user.get('name', 'Unknown')}")
                return True
            else:
                logging.error(f"❌ Auth failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            logging.error(f"❌ Connection test failed: {e}")
            return False
    
    def create_post(self, title: str, content: str, status: str = 'draft',
                   author_id: Optional[int] = None, category_ids: Optional[list] = None,
                   tags: Optional[list] = None, slug: Optional[str] = None) -> dict:
        """
        Create a new WordPress post
        
        Args:
            title: Post title
            content: Post content (HTML)
            status: Post status ('draft', 'publish', 'pending', 'private')
            author_id: Author ID (optional)
            category_ids: List of category IDs (optional)
            tags: List of tag IDs (optional)
            slug: Custom slug for the post (optional)
        
        Returns:
            dict: Response data with post ID and URL
        
        Raises:
            Exception: If post creation fails
        """
        logging.info(f"📤 Creating post: {title}")
        
        # Build post data
        post_data = {
            'title': title,
            'content': content,
            'status': status,
        }

        if slug:
            post_data['slug'] = slug
        
        if author_id:
            post_data['author'] = author_id
        
        if category_ids:
            post_data['categories'] = category_ids
        
        if tags:
            post_data['tags'] = tags
        
        try:
            response = self.session.post(
                f"{self.api_base}/posts",
                json=post_data,
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                post = response.json()
                logging.info(f"✅ Post created successfully!")
                logging.info(f"   ID: {post['id']}")
                logging.info(f"   Status: {post['status']}")
                logging.info(f"   URL: {post['link']}")
                
                return {
                    'success': True,
                    'id': post['id'],
                    'url': post['link'],
                    'status': post['status'],
                    'title': post['title']['rendered']
                }
            else:
                error_msg = f"Failed to create post: {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg += f" - {error_data.get('message', response.text)}"
                except:
                    error_msg += f" - {response.text}"
                
                logging.error(f"❌ {error_msg}")
                raise Exception(error_msg)
        
        except requests.exceptions.Timeout:
            logging.error("❌ Request timeout")
            raise Exception("WordPress API request timeout")
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Request error: {e}")
            raise
        except Exception as e:
            logging.error(f"❌ Unexpected error: {e}")
            raise
    
    def update_post(self, post_id: int, title: Optional[str] = None, 
                   content: Optional[str] = None, status: Optional[str] = None) -> dict:
        """Update an existing post"""
        logging.info(f"📝 Updating post ID: {post_id}")
        
        update_data = {}
        if title:
            update_data['title'] = title
        if content:
            update_data['content'] = content
        if status:
            update_data['status'] = status
        
        try:
            response = self.session.post(
                f"{self.api_base}/posts/{post_id}",
                json=update_data,
                timeout=30
            )
            
            if response.status_code == 200:
                post = response.json()
                logging.info(f"✅ Post updated successfully!")
                return {
                    'success': True,
                    'id': post['id'],
                    'url': post['link']
                }
            else:
                raise Exception(f"Failed to update post: {response.status_code} - {response.text}")
        
        except Exception as e:
            logging.error(f"❌ Update failed: {e}")
            raise
    
    def delete_post(self, post_id: int, force: bool = False) -> dict:
        """Delete a post (move to trash or permanent delete)"""
        logging.info(f"🗑️ Deleting post ID: {post_id}")
        
        try:
            url = f"{self.api_base}/posts/{post_id}"
            if force:
                url += "?force=true"
            
            response = self.session.delete(url, timeout=30)
            
            if response.status_code == 200:
                logging.info("✅ Post deleted successfully!")
                return {'success': True}
            else:
                raise Exception(f"Failed to delete post: {response.status_code}")
        
        except Exception as e:
            logging.error(f"❌ Delete failed: {e}")
            raise
    
    def get_categories(self) -> list:
        """Get all available categories"""
        try:
            response = self.session.get(
                f"{self.api_base}/categories",
                params={'per_page': 100},
                timeout=10
            )
            
            if response.status_code == 200:
                categories = response.json()
                logging.info(f"✅ Retrieved {len(categories)} categories")
                return categories
            else:
                logging.warning(f"⚠️ Failed to get categories: {response.status_code}")
                return []
        
        except Exception as e:
            logging.error(f"❌ Error getting categories: {e}")
            return []
