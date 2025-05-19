# Google Indexing Tool

A Python tool for submitting URLs to Google's Indexing API with support for multiple API keys and automated scheduling.

## Features

- Submit URLs to Google's Indexing API
- Process XML sitemaps to automatically extract and add URLs
- Support for multiple Google API keys
- Automatic scheduling using cron or built-in scheduler
- Command-line interface for managing URLs and API keys
- Detailed logging of successes and errors

## Prerequisites

- Python 3.8+
- Google Cloud Platform account
- Verified website in Google Search Console

## Installation

1. Clone this repository:
```bash
git clone https://github.com/hwsdev/python-google-indexing.git
cd python-google-indexing
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Google API Setup (Detailed Guide)

### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select an existing project
3. Give your project a name (e.g., "Google Indexing Tool")

### Step 2: Enable the Indexing API
1. Go to APIs & Services > Library
2. Search for "Indexing API"
3. Click on the API and click "Enable"

### Step 3: Create a Service Account
1. Go to IAM & Admin > Service Accounts
2. Click "Create Service Account"
3. Name your service account (e.g., "google-indexing-service")
4. Grant the following roles:
   - Project > Editor
   - Search Console > Site Owner
5. Click "Create and Continue"
6. Click "Create Key" and choose JSON format
7. Save the JSON key file securely

### Step 4: Add Service Account to Search Console
1. Go to [Google Search Console](https://search.google.com/search-console)
2. Select your property
3. Go to Settings > Users and permissions
4. Add the email from your service account JSON file with "Owner" permissions

### Step 5: Add Service Account to the Tool
```bash
python indexing_cli.py key add /path/to/your-service-account.json
```

## Usage

### Managing URLs

Add a single URL:
```bash
python indexing_cli.py url add https://example.com/new-page
```

Add URLs from a sitemap:
```bash
python indexing_cli.py url add-from-sitemap https://example.com/sitemap.xml
```

Add multiple URLs from a file (one URL per line):
```bash
python indexing_cli.py url add-from-file urls.txt
```

List all URLs:
```bash
python indexing_cli.py url list
```

List URLs with a specific status:
```bash
python indexing_cli.py url list --status pending
```

### Running the Indexing Tool

Run once:
```bash
python indexing_scheduler.py --run-once
```

Run as a background process with the built-in scheduler:
```bash
python indexing_scheduler.py --interval 60 --batch-size 10
```

### Setting Up a Cron Job

For more reliable scheduling, you can use cron:

```bash
# Run the indexing tool every hour
0 * * * * cd /path/to/python-google-indexing && python indexing_scheduler.py --run-once
```

## Configuration Options

### Scheduler Options

- `--run-once`: Run once and exit
- `--batch-size`: Number of URLs to process in each batch (default: 10)
- `--retry-failed`: Retry failed URLs
- `--interval`: Minutes between scheduled runs (default: 60)
- `--api-keys-dir`: Directory containing API key files (default: "api_keys")
- `--urls-file`: File containing URLs to index (default: "urls.json")

## Logs

Logs are stored in the following files:

- `indexing.log`: Main application logs
- `scheduler.log`: Scheduler-specific logs
- `cli.log`: CLI operation logs
- `logs/indexing_YYYY-MM-DD.log`: Detailed daily indexing result logs

## Troubleshooting

- **No API Clients Loaded**: Ensure you've added a valid service account JSON file
- **Sitemap Parsing Errors**: Check that the sitemap URL is valid and accessible
- **Indexing Failures**: Verify your Search Console and API permissions

## License

MIT License 
