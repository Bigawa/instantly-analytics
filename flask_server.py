from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import uuid
import asyncio
import aiohttp
import random
import logging
import os
from instantly_campaign_api import InstantlyCampaignAPI
from instantly_campaign_analytics_api import InstantlyCampaignAnalyticsAPI
from typing import List, Dict, Any, Tuple
import threading
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/flask_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuration for concurrent requests
MAX_CONCURRENT_REQUESTS = 10  # Maximum number of concurrent requests
MAX_RETRIES = 5              # Maximum number of retries for failed requests
BASE_DELAY = 1              # Base delay for exponential backoff (seconds)
MAX_DELAY = 32             # Maximum delay for exponential backoff (seconds)

async def fetch_with_retry(session: aiohttp.ClientSession, url: str, headers: Dict, params: Dict) -> Dict:
    """Fetch data with exponential backoff retry logic"""
    for attempt in range(MAX_RETRIES):
        try:
            logger.debug(f"Making request to {url} (attempt {attempt + 1}/{MAX_RETRIES})")
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 429:  # Too Many Requests
                    delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
                    logger.warning(f"Rate limited on {url}. Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    continue
                    
                response.raise_for_status()
                logger.debug(f"Successfully fetched data from {url}")
                return await response.json()
                
        except aiohttp.ClientError as e:
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Failed to fetch data from {url} after {MAX_RETRIES} attempts: {str(e)}")
                raise
            delay = min(BASE_DELAY * (2 ** attempt) + random.uniform(0, 1), MAX_DELAY)
            logger.warning(f"Request to {url} failed. Retrying in {delay:.2f} seconds... (attempt {attempt + 1}/{MAX_RETRIES})")
            await asyncio.sleep(delay)
            
    error_msg = f"Max retries ({MAX_RETRIES}) exceeded for {url}"
    logger.error(error_msg)
    raise Exception(error_msg)

# Store for job status and results
job_store = {}

def split_date_range(start_date: str, end_date: str) -> List[Tuple[str, str]]:
    """Split date range into 7-day chunks"""
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    chunks = []
    
    current = start
    while current < end:
        chunk_end = min(current + timedelta(days=6), end)
        chunks.append((
            current.strftime('%Y-%m-%d'),
            chunk_end.strftime('%Y-%m-%d')
        ))
        current = chunk_end + timedelta(days=1)
    
    return chunks

def validate_request(data: Dict) -> Tuple[bool, str]:
    """Validate the request data"""
    if not isinstance(data, dict):
        return False, "Invalid request format"
    
    if 'api_keys' not in data or not isinstance(data['api_keys'], list):
        return False, "api_keys field is required and must be an array"
    
    if not data['api_keys']:
        return False, "api_keys array cannot be empty"
    
    if 'start_date' not in data or 'end_date' not in data:
        return False, "start_date and end_date are required"
    
    try:
        datetime.strptime(data['start_date'], '%Y-%m-%d')
        datetime.strptime(data['end_date'], '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD"
    
    return True, ""

async def fetch_campaign_analytics(session: aiohttp.ClientSession, api_key: str, 
                                campaign_id: str, chunk_start: str, chunk_end: str) -> Dict:
    """Fetch analytics for a single campaign in a date range"""
    url = InstantlyCampaignAnalyticsAPI.BASE_URL
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {
        "campaign_id": campaign_id,
        "start_date": chunk_start,
        "end_date": chunk_end
    }
    
    return await fetch_with_retry(session, url, headers, params)

async def process_campaign_batch(api_key: str, campaign_ids: List[str], 
                               date_chunks: List[Tuple[str, str]]) -> Dict:
    """Process a batch of campaigns concurrently"""
    logger.info(f"Starting batch processing for {len(campaign_ids)} campaigns with {len(date_chunks)} date chunks")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for campaign_id in campaign_ids:
            for chunk_start, chunk_end in date_chunks:
                task = fetch_campaign_analytics(
                    session, api_key, campaign_id, chunk_start, chunk_end
                )
                tasks.append(task)
        
        total_tasks = len(tasks)
        logger.info(f"Created {total_tasks} tasks for processing")
                
        # Process tasks in batches to avoid overwhelming the API
        analytics_results = []
        batch_count = (total_tasks + MAX_CONCURRENT_REQUESTS - 1) // MAX_CONCURRENT_REQUESTS
        for i in range(0, len(tasks), MAX_CONCURRENT_REQUESTS):
            batch = tasks[i:i + MAX_CONCURRENT_REQUESTS]
            current_batch = (i // MAX_CONCURRENT_REQUESTS) + 1
            logger.info(f"Processing batch {current_batch}/{batch_count} ({len(batch)} tasks)")
            
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            success_count = sum(1 for r in batch_results if not isinstance(r, Exception))
            error_count = len(batch_results) - success_count
            logger.info(f"Batch {current_batch} completed: {success_count} successful, {error_count} failed")
            
            analytics_results.extend(batch_results)
            
        logger.info(f"Batch processing completed. Total tasks processed: {total_tasks}")
        return analytics_results

def process_analytics_job(run_id: str, api_keys: List[str], start_date: str, end_date: str):
    """Background task to process analytics"""
    logger.info(f"Starting analytics job {run_id} for date range {start_date} to {end_date}")
    try:
        results = {
            'data': {},
            'daily_totals': {},  # Combined daily totals across all workspaces
            'total_sends': 0,    # Total sends across all workspaces
            'status': 'processing',
            'error': None,
            'completion': 0
        }
        job_store[run_id] = results
        logger.debug(f"Initialized job store for run_id: {run_id}")
        
        total_items = len(api_keys)
        processed_items = 0
        
        for api_key in api_keys:
            try:
                workspace_data = {
                    "campaign_analytics": {},
                    "total_sent": 0,
                    "error": None
                }
                
                # Get all campaign IDs for this workspace
                campaign_api = InstantlyCampaignAPI(api_key)
                analytics_api = InstantlyCampaignAnalyticsAPI(api_key)
                
                try:
                    logger.info(f"Fetching campaign IDs for workspace (API key ending: ...{api_key[-4:]})")
                    campaign_ids = campaign_api.get_campaign_ids()
                    logger.info(f"Found {len(campaign_ids)} campaigns for workspace (API key ending: ...{api_key[-4:]})")
                except Exception as e:
                    error_msg = f"Failed to fetch campaign IDs: {str(e)}"
                    logger.error(f"Workspace (API key ending: ...{api_key[-4:]}) - {error_msg}")
                    workspace_data["error"] = error_msg
                    results['data'][api_key] = workspace_data
                    continue
                
                # Split date range into 7-day chunks
                date_chunks = split_date_range(start_date, end_date)
                print(f"Split date range into {len(date_chunks)} chunks")
                
                # Process campaigns in batches
                date_chunks = split_date_range(start_date, end_date)
                print(f"Split date range into {len(date_chunks)} chunks")
                
                # Create event loop in the thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Process campaigns concurrently
                analytics_results = loop.run_until_complete(
                    process_campaign_batch(api_key, campaign_ids, date_chunks)
                )
                
                # Process results
                campaign_analytics = {}
                for campaign_id in campaign_ids:
                    campaign_data = {
                        "daily_sends": {},
                        "total_sent": 0,
                        "error": None
                    }
                    campaign_analytics[campaign_id] = campaign_data
                
                # Process the analytics results
                for i, result in enumerate(analytics_results):
                    if isinstance(result, Exception):
                        print(f"Error in batch request {i}: {str(result)}")
                        continue
                        
                    campaign_idx = i // len(date_chunks)
                    campaign_id = campaign_ids[campaign_idx]
                    campaign_data = campaign_analytics[campaign_id]
                    
                    try:
                        # Process analytics data
                        for day in result:
                            date = day['date']
                            sends = day['sent']
                            
                            # Update campaign daily sends
                            if date not in campaign_data["daily_sends"]:
                                campaign_data["daily_sends"][date] = 0
                            campaign_data["daily_sends"][date] += sends
                            campaign_data["total_sent"] += sends
                            workspace_data["total_sent"] += sends
                            
                            # Update combined daily totals
                            if date not in results['daily_totals']:
                                results['daily_totals'][date] = 0
                            results['daily_totals'][date] += sends
                            results['total_sends'] += sends
                            
                    except Exception as e:
                        print(f"Error processing result for campaign {campaign_id}: {str(e)}")
                
                workspace_data["campaign_analytics"] = campaign_analytics
                results['data'][api_key] = workspace_data
                
            except Exception as e:
                results['data'][api_key] = {
                    "campaign_analytics": {},
                    "total_sent": 0,
                    "error": f"Workspace error: {str(e)}"
                }
            
            processed_items += 1
            results['completion'] = (processed_items / total_items) * 100
            
        results['status'] = 'completed'
        results['completion'] = 100
        
    except Exception as e:
        results['status'] = 'failed'
        results['error'] = str(e)
    finally:
        job_store[run_id].update(results)

@app.route('/analytics/bulk/start', methods=['POST'])
def start_bulk_analytics():
    """Start a new bulk analytics job"""
    try:
        logger.info("Received new bulk analytics job request")
        data = request.get_json()
        
        # Validate request
        logger.debug("Validating request data")
        is_valid, error_message = validate_request(data)
        if not is_valid:
            logger.warning(f"Invalid request received: {error_message}")
            return jsonify({
                "status": "error",
                "message": error_message
            }), 400
            
        # Generate unique run ID
        run_id = str(uuid.uuid4())
        
        # Start background processing
        thread = threading.Thread(
            target=process_analytics_job,
            args=(run_id, data['api_keys'], data['start_date'], data['end_date'])
        )
        thread.daemon = True  # Daemon thread will be killed when main thread exits
        thread.start()
        
        return jsonify({
            "status": "accepted",
            "run_id": run_id,
            "message": "Job started successfully"
        }), 202
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/analytics/bulk/status/<run_id>', methods=['GET'])
def get_bulk_analytics_status(run_id):
    """Get the status and results of a bulk analytics job"""
    logger.info(f"Checking status for job {run_id}")
    if run_id not in job_store:
        logger.warning(f"Job not found: {run_id}")
        return jsonify({
            "status": "error",
            "message": "Job not found"
        }), 404
        
    job = job_store[run_id]
    response = {
        "status": job['status'],
        "completion": job['completion']
    }
    
    # Include results if job is completed
    if job['status'] == 'completed':
        response.update({
            'data': job['data'],
            'daily_totals': dict(sorted(job['daily_totals'].items())),  # Sort by date
            'total_sends': job['total_sends']
        })
    elif job['status'] == 'failed':
        response['error'] = job['error']
        
    return jsonify(response)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
