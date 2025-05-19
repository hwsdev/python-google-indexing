import os
import sys
import logging
import argparse
from typing import List, Optional

from google_indexing import IndexingManager
from url_manager import URLManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cli.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("indexing_cli")

class IndexingCLI:
    """
    Command Line Interface for Google Indexing tool
    """
    def __init__(self, api_keys_dir: str = "api_keys", urls_file: str = "urls.json"):
        """
        Initialize the CLI
        
        Args:
            api_keys_dir: Directory containing Google API service account JSON files
            urls_file: Path to the JSON file storing URL data
        """
        self.api_keys_dir = api_keys_dir
        self.urls_file = urls_file
        
        # Create directories if they don't exist
        os.makedirs(api_keys_dir, exist_ok=True)
        
        self.indexing_manager = IndexingManager(api_keys_dir)
        self.url_manager = URLManager(urls_file)
        
    def add_url(self, url: str, priority: int = 1):
        """Add a single URL"""
        success = self.url_manager.add_url(url, priority)
        if success:
            print(f"Successfully added URL: {url}")
        else:
            print(f"URL already exists: {url}")
            
    def add_urls_from_file(self, file_path: str, priority: int = 1):
        """Add URLs from a text file (one URL per line)"""
        try:
            with open(file_path, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
                
            if not urls:
                print(f"No URLs found in file: {file_path}")
                return
                
            count = self.url_manager.add_urls(urls, priority)
            print(f"Added {count} URLs from {file_path}")
            
        except Exception as e:
            print(f"Error reading URLs from file: {str(e)}")
            
    def list_urls(self, status: Optional[str] = None):
        """List URLs with optional status filter"""
        urls = self.url_manager.urls
        
        if status:
            urls = [url for url in urls if url.get("status") == status]
            
        if not urls:
            print("No URLs found")
            return
            
        print(f"{'URL':<60} {'Status':<10} {'Priority':<8}")
        print("-" * 80)
        
        for url_data in urls:
            print(f"{url_data['url']:<60} {url_data.get('status', 'unknown'):<10} {url_data.get('priority', 1):<8}")
            
        print(f"\nTotal: {len(urls)} URLs")
        
    def add_api_key(self, service_account_file: str):
        """Add a Google API service account key"""
        if not os.path.exists(service_account_file):
            print(f"Service account file not found: {service_account_file}")
            return
            
        success = self.indexing_manager.add_api_key(service_account_file)
        if success:
            print(f"Successfully added API key from: {service_account_file}")
        else:
            print(f"Failed to add API key from: {service_account_file}")
            
    def list_api_keys(self):
        """List available API keys"""
        if not os.path.exists(self.api_keys_dir):
            print(f"API keys directory not found: {self.api_keys_dir}")
            return
            
        keys = [f for f in os.listdir(self.api_keys_dir) if f.endswith('.json')]
        
        if not keys:
            print("No API keys found")
            return
            
        print("Available API keys:")
        for i, key in enumerate(keys, 1):
            print(f"{i}. {key}")
            
        print(f"\nTotal: {len(keys)} API keys")
        
    def test_api_key(self, key_file: Optional[str] = None):
        """Test a specific API key or all keys"""
        if key_file:
            # Test a specific key
            file_path = key_file if os.path.exists(key_file) else os.path.join(self.api_keys_dir, key_file)
            
            if not os.path.exists(file_path):
                print(f"API key file not found: {file_path}")
                return
                
            try:
                from google_indexing import GoogleIndexingAPI
                api = GoogleIndexingAPI(file_path)
                print(f"API key is valid: {file_path}")
                print(f"Service account email: {api._credentials.service_account_email}")
            except Exception as e:
                print(f"Error testing API key {file_path}: {str(e)}")
        else:
            # Test all keys
            if not self.indexing_manager.api_clients:
                print("No API keys loaded")
                return
                
            print("Testing all API keys:")
            for i, client in enumerate(self.indexing_manager.api_clients, 1):
                print(f"{i}. {client.service_account_file} - Valid (Email: {client._credentials.service_account_email})")
                
            print(f"\nTotal: {len(self.indexing_manager.api_clients)} valid API keys")


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Google Indexing CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # URL commands
    url_parser = subparsers.add_parser("url", help="URL management commands")
    url_subparsers = url_parser.add_subparsers(dest="url_command", help="URL command to run")
    
    # Add URL
    add_url_parser = url_subparsers.add_parser("add", help="Add a URL")
    add_url_parser.add_argument("url", help="URL to add")
    add_url_parser.add_argument("--priority", type=int, default=1, help="Priority level (higher is more important)")
    
    # Add URLs from file
    add_urls_parser = url_subparsers.add_parser("add-from-file", help="Add URLs from a file")
    add_urls_parser.add_argument("file", help="File containing URLs (one per line)")
    add_urls_parser.add_argument("--priority", type=int, default=1, help="Priority level for all URLs")
    
    # List URLs
    list_urls_parser = url_subparsers.add_parser("list", help="List URLs")
    list_urls_parser.add_argument("--status", choices=["pending", "indexed", "failed"], help="Filter by status")
    
    # API key commands
    key_parser = subparsers.add_parser("key", help="API key management commands")
    key_subparsers = key_parser.add_subparsers(dest="key_command", help="API key command to run")
    
    # Add API key
    add_key_parser = key_subparsers.add_parser("add", help="Add a Google API service account key")
    add_key_parser.add_argument("file", help="Path to the service account JSON file")
    
    # List API keys
    key_subparsers.add_parser("list", help="List available API keys")
    
    # Test API key
    test_key_parser = key_subparsers.add_parser("test", help="Test API key(s)")
    test_key_parser.add_argument("--file", help="Specific key file to test (tests all if not specified)")
    
    # Global options
    parser.add_argument("--api-keys-dir", type=str, default="api_keys", help="Directory containing API key files")
    parser.add_argument("--urls-file", type=str, default="urls.json", help="File containing URLs to index")
    
    return parser.parse_args()


def main():
    """Main CLI entry point"""
    args = parse_arguments()
    
    if not args.command:
        print("No command specified. Use --help for usage information.")
        return
        
    # Initialize the CLI
    cli = IndexingCLI(
        api_keys_dir=args.api_keys_dir,
        urls_file=args.urls_file
    )
    
    # Handle URL commands
    if args.command == "url":
        if args.url_command == "add":
            cli.add_url(args.url, args.priority)
        elif args.url_command == "add-from-file":
            cli.add_urls_from_file(args.file, args.priority)
        elif args.url_command == "list":
            cli.list_urls(args.status)
        else:
            print("Unknown URL command. Use --help for usage information.")
            
    # Handle API key commands
    elif args.command == "key":
        if args.key_command == "add":
            cli.add_api_key(args.file)
        elif args.key_command == "list":
            cli.list_api_keys()
        elif args.key_command == "test":
            cli.test_api_key(args.file)
        else:
            print("Unknown API key command. Use --help for usage information.")
    else:
        print("Unknown command. Use --help for usage information.")


if __name__ == "__main__":
    main() 