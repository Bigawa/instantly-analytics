import requests
import json
import time
from datetime import datetime, timedelta

def test_api():
    # Calculate date range for last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Format dates as YYYY-MM-DD
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"\nFetching data from {start_date_str} to {end_date_str} (30 days)")

    def check_job_status(run_id, max_retries=60, delay=5):
        """Check job status with retries"""
        retries = 0
        while retries < max_retries:
            try:
                response = requests.get(f'http://localhost:5000/analytics/bulk/status/{run_id}')
                response.raise_for_status()
                data = response.json()
                
                print(f"\rJob completion: {data['completion']}%", end="")
                
                if data['status'] == 'completed':
                    print("\nJob completed successfully!")
                    return data
                elif data['status'] == 'failed':
                    print(f"\nJob failed: {data.get('error', 'Unknown error')}")
                    return None
                    
                retries += 1
                time.sleep(delay)
            except Exception as e:
                print(f"\nError checking status: {e}")
                return None
                
        print("\nTimeout waiting for job completion")
        return None

    # Test data with API key
    payload = {
        "api_keys": [
            "NDZhOGRkM2ItNTg1NS00YzJkLTkxOWYtNTlkNDJmYjFkY2M5OmdxVUNab1dKdWpnUQ=="
        ],
        "start_date": start_date_str,
        "end_date": end_date_str
    }

    try:
        # First check if server is healthy
        print("\nPerforming health check...")
        health_response = requests.get('http://localhost:5000/health')
        health_response.raise_for_status()
        health_data = health_response.json()
        print("Health Check Response:", health_data)
        
        if health_data.get('status') != 'healthy':
            raise Exception("Server is not healthy")

        # Start the analytics job
        print("\nStarting analytics job...")
        response = requests.post(
            'http://localhost:5000/analytics/bulk/start',
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        # Get the run ID
        start_result = response.json()
        if start_result.get('status') != 'accepted' or 'run_id' not in start_result:
            raise ValueError(f"Invalid start response: {start_result}")
            
        run_id = start_result['run_id']
        print(f"Job started successfully. Run ID: {run_id}")
        
        # Monitor job status
        result = check_job_status(run_id)
        if not result:
            raise Exception("Job failed or timed out")

        # Create structured analytics summary
        analytics_summary = {
            'metadata': {
                'query_period': {
                    'start_date': start_date_str,
                    'end_date': end_date_str,
                    'days': 30
                },
                'total_sends': result.get('total_sends', 0),
                'query_time': datetime.now().isoformat()
            },
            'daily_summary': {
                'by_date': result.get('daily_totals', {}),
                'by_week': {}
            },
            'workspaces': {}
        }

        # Process daily totals into weekly summaries
        daily_totals = result.get('daily_totals', {})
        for date, sends in sorted(daily_totals.items()):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            week_start = (date_obj - timedelta(days=date_obj.weekday())).strftime('%Y-%m-%d')
            week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
            week_key = f"{week_start} to {week_end}"
            
            if week_key not in analytics_summary['daily_summary']['by_week']:
                analytics_summary['daily_summary']['by_week'][week_key] = {
                    'week_total': 0,
                    'daily_sends': {}
                }
            analytics_summary['daily_summary']['by_week'][week_key]['week_total'] += sends
            analytics_summary['daily_summary']['by_week'][week_key]['daily_sends'][date] = sends

        # Process workspace and campaign data
        for api_key, workspace_data in result.get('data', {}).items():
            workspace_summary = {
                'workspace_total_sends': workspace_data.get('total_sent', 0),
                'total_campaigns': len(workspace_data.get('campaign_analytics', {})),
                'campaigns': {}
            }
            
            # Process each campaign
            for campaign_id, campaign_data in workspace_data.get('campaign_analytics', {}).items():
                campaign_summary = {
                    'campaign_total_sends': campaign_data.get('total_sent', 0),
                    'daily_sends': {},
                    'weekly_summary': {}
                }
                
                # Process campaign daily data into weekly summaries
                for date, sends in sorted(campaign_data.get('daily_sends', {}).items()):
                    campaign_summary['daily_sends'][date] = sends
                    
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    week_start = (date_obj - timedelta(days=date_obj.weekday())).strftime('%Y-%m-%d')
                    week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
                    week_key = f"{week_start} to {week_end}"
                    
                    if week_key not in campaign_summary['weekly_summary']:
                        campaign_summary['weekly_summary'][week_key] = {
                            'week_total': 0,
                            'daily_sends': {}
                        }
                    campaign_summary['weekly_summary'][week_key]['week_total'] += sends
                    campaign_summary['weekly_summary'][week_key]['daily_sends'][date] = sends
                
                workspace_summary['campaigns'][campaign_id] = campaign_summary
            
            analytics_summary['workspaces'][api_key] = workspace_summary

        # Save analytics summary to file
        summary_file = 'campaign_analytics_summary.json'
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(analytics_summary, f, indent=2, sort_keys=True)

        # Save raw API response to file
        response_file = 'campaign_analytics_raw.json'
        with open(response_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)

        print("\nAnalytics data saved to JSON files:")
        print(f"1. {summary_file} - Structured analytics summary:")
        print("   - Query metadata (date range, totals)")
        print("   - Daily and weekly summaries")
        print("   - Per-workspace campaign statistics")
        print(f"2. {response_file} - Raw API response")
            
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Is it running?")
    except requests.exceptions.Timeout:
        print("Error: Initial request timed out. Server might be overloaded.")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e}")
        print(f"Response: {e.response.text if hasattr(e, 'response') else 'No response text'}")
    except json.JSONDecodeError:
        print("Error: Invalid JSON response from server")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
    finally:
        print("\nTest completed")

if __name__ == '__main__':
    test_api()
