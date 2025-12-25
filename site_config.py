"""
Site Configuration Manager
Loads and manages WordPress site configurations from JSON
"""
import json
import os
import logging
from typing import Optional, List, Dict

class SiteConfig:
    """WordPress site configuration"""
    
    def __init__(self, config_dict: dict):
        self.id = config_dict['id']
        self.name = config_dict['name']
        self.site_url = config_dict['site_url']
        self.username = config_dict['username']
        self.app_password = config_dict['app_password']
        self.author_id = config_dict.get('author_id', 1)
        self.category_id = config_dict.get('category_id')
        self.info_category_id = config_dict.get('info_category_id')
        self.status = config_dict.get('status', 'publish')
        self.keyword_file = config_dict['keyword_file']
    
    def __repr__(self):
        return f"<SiteConfig #{self.id}: {self.name}>"


class SiteConfigManager:
    """Manages multiple site configurations"""
    
    def __init__(self, config_file: str = 'sites_config.json'):
        self.config_file = config_file
        self.sites: List[SiteConfig] = []
        self._load_config()
    
    def _load_config(self):
        """Load site configurations from JSON file"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}\n"
                f"Please create sites_config.json with your site configurations."
            )
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'sites' not in data or not data['sites']:
                raise ValueError("No sites defined in configuration file")
            
            for site_data in data['sites']:
                site = SiteConfig(site_data)
                self.sites.append(site)
            
            logging.info(f"✅ Loaded {len(self.sites)} site(s) from {self.config_file}")
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {self.config_file}: {e}")
        except KeyError as e:
            raise ValueError(f"Missing required field in site config: {e}")
    
    def get_site(self, site_id: int) -> Optional[SiteConfig]:
        """Get site by ID"""
        for site in self.sites:
            if site.id == site_id:
                return site
        return None
    
    def list_sites(self) -> List[SiteConfig]:
        """Get all sites"""
        return self.sites
    
    def select_site_interactive(self) -> SiteConfig:
        """Interactive site selection menu"""
        if len(self.sites) == 1:
            site = self.sites[0]
            logging.info(f"✅ Auto-selected: {site.name}")
            return site
        
        print("\n" + "="*80)
        print("📋 SELECT WORDPRESS SITE")
        print("="*80 + "\n")
        
        for site in self.sites:
            # Count keywords if file exists
            keyword_count = "?"
            if os.path.exists(site.keyword_file):
                try:
                    with open(site.keyword_file, 'r', encoding='utf-8') as f:
                        keyword_count = len([line for line in f if line.strip()])
                except:
                    pass
            
            print(f"[{site.id}] {site.name}")
            print(f"    URL: {site.site_url}")
            print(f"    Keywords: {site.keyword_file} ({keyword_count} keywords)")
            print()
        
        while True:
            try:
                choice = input(f"Choose site (1-{len(self.sites)}): ").strip()
                site_id = int(choice)
                site = self.get_site(site_id)
                
                if site:
                    print(f"\n✅ Selected: {site.name}")
                    print(f"✅ Keyword file: {site.keyword_file}\n")
                    return site
                else:
                    print(f"❌ Invalid choice. Please enter 1-{len(self.sites)}")
            except ValueError:
                print(f"❌ Invalid input. Please enter a number.")
            except KeyboardInterrupt:
                print("\n\n❌ Cancelled by user")
                exit(0)
