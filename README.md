# Instantly.ai Analytics API Integration

A Flask-based application that integrates with Instantly.ai's API to fetch and aggregate campaign analytics data across multiple workspaces.

## Features

- Multiple workspace support (multiple API keys)
- Asynchronous processing of campaign analytics
- Exponential backoff retry logic
- Progress tracking and real-time status updates
- Daily analytics aggregation
- JSON output with detailed workspace statistics

## Project Structure

```
graph_api/
├── flask_server.py          # Main Flask application
├── instantly_campaign_api.py       # Campaign API client
├── instantly_campaign_analytics_api.py  # Analytics API client
├── test_daily_sends.py     # Test script
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Setup

1. Clone the repository:
```bash
git clone [repository-url]
cd graph_api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```
API_KEY_1=your_first_api_key
API_KEY_2=your_second_api_key
API_KEY_3=your_third_api_key
```

## Usage

1. Start the Flask server:
```bash
python flask_server.py
```

2. Run the test script:
```bash
python test_daily_sends.py
```

## API Endpoints

### POST /analytics/bulk/start
Start a new bulk analytics job

Request body:
```json
{
    "api_keys": ["key1", "key2", "key3"],
    "start_date": "2025-08-01",
    "end_date": "2025-08-18"
}
```

### GET /analytics/bulk/status/{run_id}
Get the status and results of a bulk analytics job

### GET /health
Simple health check endpoint

## Output

The script generates a `daily_sends.json` file containing:
- Daily send totals across all workspaces
- Per-workspace analytics data
- Campaign-level statistics
- Error reporting

## Error Handling

- Rate limiting with exponential backoff
- Per-workspace error tracking
- Connection error recovery
- Invalid response handling

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
