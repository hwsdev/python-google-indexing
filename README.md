# Google Indexing Tool

A Python tool for submitting URLs to Google's Indexing API with support for multiple API keys and automated scheduling.

## Features

- Submit URLs to Google's Indexing API
- Support for multiple Google API keys
- Automatic scheduling using cron or built-in scheduler
- Command-line interface for managing URLs and API keys
- Detailed logging of successes and errors

## Installation

1. Clone this repository:
```
git clone https://github.com/hwsdev/python-google-indexing.git
cd python-google-indexing
```

2. Install the required dependencies:
```
pip install -r requirements.txt
```

## Setup

### Google API Setup

1. Create a Google Search Console account if you don't have one: https://search.google.com/search-console
2. Verify ownership of your website in Search Console
3. Create a Google Cloud Platform project: https://console.cloud.google.com/
4. Enable the Indexing API in your GCP project
5. Create service account credentials with appropriate permissions:
   - Go to GCP Console > IAM & Admin > Service Accounts
   - Create a new service account
   - Grant the service account the "Owner" role
   - Create a JSON key for the service account and download it
6. Add the service account email as a user in Search Console with "Owner" permissions

### Adding API Keys

Use the CLI to add your service account JSON key:

```
python indexing_cli.py key add /path/to/your-service-account.json
```

You can add multiple API keys to increase your indexing quota.

## Usage

### Managing URLs

Add a single URL:
```
python indexing_cli.py url add https://example.com/new-page
```

Add multiple URLs from a file (one URL per line):
```
python indexing_cli.py url add-from-file urls.txt
```

List all URLs:
```
python indexing_cli.py url list
```

List URLs with a specific status:
```
python indexing_cli.py url list --status pending
```

### Running the Indexing Tool

Run once:
```
python indexing_scheduler.py --run-once
```

Run as a background process with the built-in scheduler:
```
python indexing_scheduler.py --interval 60 --batch-size 10
```

### Setting Up a Cron Job

For more reliable scheduling, you can use cron:

```
# Run the indexing tool every hour
0 * * * * cd /path/to/google-indexing-tool && python indexing_scheduler.py --run-once
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

## License

MIT License 
