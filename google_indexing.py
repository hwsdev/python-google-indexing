import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("indexing.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("google_indexing")

class GoogleIndexingAPI:
    """
    Class for interacting with Google's Indexing API
    """
    def __init__(self, service_account_file: str):
        """
        Initialize the Google Indexing API with a service account file
        
        Args:
            service_account_file: Path to the service account JSON file
        """
        self.service_account_file = service_account_file
        self._service = None
        self._credentials = None
        self._initialize_service()
        
    def _initialize_service(self):
        """Initialize the Google API service with the service account credentials"""
        try:
            self._credentials = service_account.Credentials.from_service_account_file(
                self.service_account_file,
                scopes=['https://www.googleapis.com/auth/indexing']
            )
            self._service = build('indexing', 'v3', credentials=self._credentials)
            logger.info(f"Successfully initialized service with account: {self._credentials.service_account_email}")
        except Exception as e:
            logger.error(f"Failed to initialize service: {str(e)}")
            raise
    
    def request_indexing(self, url: str, action: str = "URL_UPDATED") -> Dict[str, Any]:
        """
        Submit a URL to Google for indexing
        
        Args:
            url: The URL to be indexed
            action: Either "URL_UPDATED" or "URL_DELETED"
            
        Returns:
            API response as dictionary
        """
        if action not in ["URL_UPDATED", "URL_DELETED"]:
            raise ValueError("Action must be either URL_UPDATED or URL_DELETED")
            
        try:
            response = self._service.urlNotifications().publish(
                body={
                    "url": url,
                    "type": action
                }
            ).execute()
            logger.info(f"Successfully submitted {url} for {action}")
            return response
        except HttpError as e:
            error_details = json.loads(e.content.decode())
            logger.error(f"Error submitting {url}: {error_details.get('error', {}).get('message', str(e))}")
            return {"error": str(e), "details": error_details}
        except Exception as e:
            logger.error(f"Unexpected error submitting {url}: {str(e)}")
            return {"error": str(e)}
    
    def get_status(self, url: str) -> Dict[str, Any]:
        """
        Get the indexing status of a URL
        
        Args:
            url: The URL to check status for
            
        Returns:
            Status information as dictionary
        """
        try:
            params = {
                'url': url,
                'fields': 'urlNotificationMetadata'
            }
            response = self._service.urlNotifications().getMetadata(
                **params
            ).execute()
            logger.info(f"Got status for {url}")
            return response
        except HttpError as e:
            error_details = json.loads(e.content.decode())
            logger.error(f"Error getting status for {url}: {error_details.get('error', {}).get('message', str(e))}")
            return {"error": str(e), "details": error_details}
        except Exception as e:
            logger.error(f"Unexpected error getting status for {url}: {str(e)}")
            return {"error": str(e)}

class IndexingManager:
    """
    Manager class for handling multiple API keys and URLs
    """
    def __init__(self, api_keys_dir: str):
        """
        Initialize the IndexingManager
        
        Args:
            api_keys_dir: Directory containing Google API service account JSON files
        """
        self.api_keys_dir = api_keys_dir
        self.api_clients = self._load_api_clients()
        self.current_key_index = 0
        
    def _load_api_clients(self) -> List[GoogleIndexingAPI]:
        """Load all API clients from the API keys directory"""
        clients = []
        
        if not os.path.exists(self.api_keys_dir):
            os.makedirs(self.api_keys_dir)
            logger.warning(f"Created API keys directory: {self.api_keys_dir}")
            return clients
            
        for filename in os.listdir(self.api_keys_dir):
            if filename.endswith('.json'):
                try:
                    file_path = os.path.join(self.api_keys_dir, filename)
                    client = GoogleIndexingAPI(file_path)
                    clients.append(client)
                    logger.info(f"Loaded API key from {filename}")
                except Exception as e:
                    logger.error(f"Failed to load API key from {filename}: {str(e)}")
        
        if not clients:
            logger.warning("No API clients loaded! Add service account JSON files to the api_keys directory.")
            
        return clients
    
    def add_api_key(self, service_account_file: str) -> bool:
        """
        Add a new API key to the manager
        
        Args:
            service_account_file: Path to the service account JSON file
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Copy the file to our keys directory
            filename = os.path.basename(service_account_file)
            destination = os.path.join(self.api_keys_dir, filename)
            
            # Don't copy if it's already in the directory
            if service_account_file != destination:
                with open(service_account_file, 'r') as src:
                    os.makedirs(self.api_keys_dir, exist_ok=True)
                    with open(destination, 'w') as dst:
                        dst.write(src.read())
                        
            # Create a new client and add it to our list
            client = GoogleIndexingAPI(destination)
            self.api_clients.append(client)
            logger.info(f"Added new API key: {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to add API key: {str(e)}")
            return False
    
    def _get_next_client(self) -> Optional[GoogleIndexingAPI]:
        """Get the next available API client using round-robin"""
        if not self.api_clients:
            logger.error("No API clients available")
            return None
            
        client = self.api_clients[self.current_key_index]
        self.current_key_index = (self.current_key_index + 1) % len(self.api_clients)
        return client
    
    def index_url(self, url: str, action: str = "URL_UPDATED") -> Dict[str, Any]:
        """
        Index a URL using the next available API key
        
        Args:
            url: URL to index
            action: Either "URL_UPDATED" or "URL_DELETED"
            
        Returns:
            API response or error information
        """
        client = self._get_next_client()
        if not client:
            return {"error": "No API clients available"}
        
        response = client.request_indexing(url, action)
        
        # Log the result
        self._log_result(url, action, response)
        
        return response
    
    def index_urls(self, urls: List[str], action: str = "URL_UPDATED") -> List[Dict[str, Any]]:
        """
        Index multiple URLs using available API keys
        
        Args:
            urls: List of URLs to index
            action: Either "URL_UPDATED" or "URL_DELETED"
            
        Returns:
            List of API responses
        """
        results = []
        
        for url in urls:
            result = self.index_url(url, action)
            results.append({"url": url, "result": result})
            # Add a small delay to avoid rate limiting
            time.sleep(1)
            
        return results
    
    def _log_result(self, url: str, action: str, response: Dict[str, Any]):
        """Log indexing results to a file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success = "error" not in response
        
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"indexing_{datetime.now().strftime('%Y-%m-%d')}.log")
        
        log_entry = {
            "timestamp": timestamp,
            "url": url,
            "action": action,
            "success": success,
            "response": response
        }
        
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n") 