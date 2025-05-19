import os
import json
import logging
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin

logger = logging.getLogger("url_manager")

class URLManager:
    """
    Class for managing URLs to be indexed
    """
    def __init__(self, urls_file: str = "urls.json"):
        """
        Initialize the URL manager
        
        Args:
            urls_file: Path to the JSON file storing URL data
        """
        self.urls_file = urls_file
        self.urls = self._load_urls()
        
    def _load_urls(self) -> List[Dict[str, Any]]:
        """Load URLs from the JSON file"""
        if not os.path.exists(self.urls_file):
            logger.info(f"URLs file not found. Creating new file: {self.urls_file}")
            return []
            
        try:
            with open(self.urls_file, 'r') as f:
                urls = json.load(f)
                logger.info(f"Loaded {len(urls)} URLs from {self.urls_file}")
                return urls
        except Exception as e:
            logger.error(f"Error loading URLs from {self.urls_file}: {str(e)}")
            return []
            
    def _save_urls(self):
        """Save URLs to the JSON file"""
        try:
            with open(self.urls_file, 'w') as f:
                json.dump(self.urls, f, indent=2)
                logger.info(f"Saved {len(self.urls)} URLs to {self.urls_file}")
        except Exception as e:
            logger.error(f"Error saving URLs to {self.urls_file}: {str(e)}")
            
    def add_url(self, url: str, priority: int = 1, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Add a URL to be indexed
        
        Args:
            url: The URL to add
            priority: Priority level (higher is more important)
            metadata: Optional metadata for the URL
            
        Returns:
            True if added successfully, False if already exists
        """
        # Check if URL already exists
        for existing_url in self.urls:
            if existing_url["url"] == url:
                logger.info(f"URL already exists: {url}")
                return False
                
        # Add the new URL
        url_data = {
            "url": url,
            "priority": priority,
            "status": "pending",
            "metadata": metadata or {}
        }
        
        self.urls.append(url_data)
        self._save_urls()
        logger.info(f"Added new URL: {url}")
        return True
        
    def add_urls(self, urls: List[str], priority: int = 1) -> int:
        """
        Add multiple URLs to be indexed
        
        Args:
            urls: List of URLs to add
            priority: Priority level for all URLs
            
        Returns:
            Number of URLs added successfully
        """
        count = 0
        for url in urls:
            if self.add_url(url, priority):
                count += 1
                
        return count
        
    def add_sitemap(self, sitemap_url: str, priority: int = 1) -> int:
        """
        Parse a sitemap and add all contained URLs for indexing
        
        Args:
            sitemap_url: URL of the sitemap
            priority: Priority level for all URLs
            
        Returns:
            Number of URLs added successfully
        """
        logger.info(f"Fetching sitemap from {sitemap_url}")
        try:
            # Fetch the sitemap
            response = requests.get(sitemap_url, timeout=30)
            response.raise_for_status()
            
            # Parse the XML
            soup = BeautifulSoup(response.content, 'xml')
            
            # First check if this is a sitemap index
            sitemap_tags = soup.find_all('sitemap')
            if sitemap_tags:
                logger.info(f"Found sitemap index with {len(sitemap_tags)} sitemaps")
                urls_added = 0
                
                # Process each child sitemap
                for sitemap_tag in sitemap_tags:
                    loc = sitemap_tag.find('loc')
                    if loc and loc.text:
                        child_sitemap_url = loc.text
                        urls_added += self.add_sitemap(child_sitemap_url, priority)
                        
                return urls_added
            
            # Extract URLs from the sitemap
            url_tags = soup.find_all('url')
            if not url_tags:
                logger.warning(f"No URLs found in sitemap: {sitemap_url}")
                return 0
                
            logger.info(f"Found {len(url_tags)} URLs in sitemap")
            
            # Extract and add each URL
            urls_to_add = []
            for url_tag in url_tags:
                loc = url_tag.find('loc')
                if loc and loc.text:
                    urls_to_add.append(loc.text.strip())
            
            # Add all URLs
            count = self.add_urls(urls_to_add, priority)
            logger.info(f"Added {count} URLs from sitemap {sitemap_url}")
            return count
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching sitemap {sitemap_url}: {str(e)}")
            return 0
        except Exception as e:
            logger.error(f"Error processing sitemap {sitemap_url}: {str(e)}")
            return 0
        
    def get_pending_urls(self, limit: Optional[int] = None, priority_threshold: Optional[int] = None) -> List[str]:
        """
        Get pending URLs for indexing
        
        Args:
            limit: Maximum number of URLs to return
            priority_threshold: Minimum priority level
            
        Returns:
            List of URL strings
        """
        # Filter by status and priority
        filtered_urls = [
            url_data["url"] for url_data in self.urls 
            if url_data["status"] == "pending" and 
            (priority_threshold is None or url_data["priority"] >= priority_threshold)
        ]
        
        # Sort by priority (highest first)
        sorted_urls = sorted(
            filtered_urls, 
            key=lambda url: next((u["priority"] for u in self.urls if u["url"] == url), 0),
            reverse=True
        )
        
        # Apply limit if provided
        if limit is not None:
            sorted_urls = sorted_urls[:limit]
            
        return sorted_urls
        
    def mark_as_indexed(self, url: str, success: bool = True) -> bool:
        """
        Mark a URL as indexed
        
        Args:
            url: The URL to update
            success: Whether indexing was successful
            
        Returns:
            True if updated successfully, False if URL not found
        """
        for url_data in self.urls:
            if url_data["url"] == url:
                url_data["status"] = "indexed" if success else "failed"
                self._save_urls()
                logger.info(f"Marked URL {url} as {'indexed' if success else 'failed'}")
                return True
                
        logger.warning(f"URL not found for status update: {url}")
        return False
        
    def remove_url(self, url: str) -> bool:
        """
        Remove a URL from the list
        
        Args:
            url: The URL to remove
            
        Returns:
            True if removed successfully, False if URL not found
        """
        initial_count = len(self.urls)
        self.urls = [url_data for url_data in self.urls if url_data["url"] != url]
        
        if len(self.urls) < initial_count:
            self._save_urls()
            logger.info(f"Removed URL: {url}")
            return True
        else:
            logger.warning(f"URL not found for removal: {url}")
            return False
            
    def reset_failed_urls(self) -> int:
        """
        Reset all failed URLs to pending status
        
        Returns:
            Number of URLs reset
        """
        count = 0
        for url_data in self.urls:
            if url_data["status"] == "failed":
                url_data["status"] = "pending"
                count += 1
                
        if count > 0:
            self._save_urls()
            logger.info(f"Reset {count} failed URLs to pending status")
            
        return count 