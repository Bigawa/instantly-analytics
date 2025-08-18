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

    # Test data with same API key used twice
    payload = {
        "api_keys": [
            "NDZhOGRkM2ItNTg1NS00YzJkLTkxOWYtNTlkNDJmYjFkY2M5OmdxVUNab1dKdWpnUQ==" # Same API key
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
            
# Create a structured summary
summary = {
    'total_sends': result.get('total_sends', 0),
    'daily_totals': result.get('daily_totals', {}),
    'weekly_summary': {},
    'workspaces': {}
}

# Group daily totals by week
for date, sends in sorted(result.get('daily_totals', {}).items()):
    date_obj = datetime.strptime(date, '%Y-%m-%d')
    week_start = (date_obj - timedelta(days=date_obj.weekday())).strftime('%Y-%m-%d')
    week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
    week_key = f"{week_start} to {week_end}"
    
    if week_key not in summary['weekly_summary']:
        summary['weekly_summary'][week_key] = {
            'total': 0,
            'days': {}
        }
    summary['weekly_summary'][week_key]['total'] += sends
    summary['weekly_summary'][week_key]['days'][date] = sends

# Process workspace data
for api_key, workspace_data in result.get('data', {}).items():
    workspace_summary = {
        'total_sends': workspace_data.get('total_sent', 0),
        'campaigns': {}
    }
    
    for campaign_id, campaign_data in workspace_data.get('campaign_analytics', {}).items():
        campaign_summary = {
            'total_sends': campaign_data.get('total_sent', 0),
            'weekly_sends': {},
            'daily_sends': campaign_data.get('daily_sends', {})
        }
        
        # Group campaign data by week
        for date, sends in sorted(campaign_data.get('daily_sends', {}).items()):
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            week_start = (date_obj - timedelta(days=date_obj.weekday())).strftime('%Y-%m-%d')
            week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
            week_key = f"{week_start} to {week_end}"
            
            if week_key not in campaign_summary['weekly_sends']:
                campaign_summary['weekly_sends'][week_key] = {
                    'total': 0,
                    'days': {}
                }
            campaign_summary['weekly_sends'][week_key]['total'] += sends
            campaign_summary['weekly_sends'][week_key]['days'][date] = sends
            
        workspace_summary['campaigns'][campaign_id] = campaign_summary
    
    summary['workspaces'][api_key] = workspace_summary

# Save structured summary to file
with open('campaign_summary.json', 'w', encoding='utf-8') as f:
    json.dump(summary, f, indent=2, sort_keys=True)

# Save raw response to file
with open('api_response.json', 'w', encoding='utf-8') as f:
    json.dump(result, f, indent=2)

print("\nResults saved to:")
print("- campaign_summary.json (structured summary)")
print("- api_response.json (raw API response)")        # Print detailed summary
        print("\n=== Analytics Summary ===")
        
        if result.get('status') == 'completed':
            # Print combined totals first
            print(f"\nCombined Statistics:")
            print(f"Total Sends Across All Workspaces: {result.get('total_sends', 0)}")
            
            # Print daily totals with visualization and week grouping
            print("\nDaily Send Totals:")
            daily_totals = result.get('daily_totals', {})
            total_sends = result.get('total_sends', 0)
            max_bar_length = 40  # Maximum length of the visualization bar
            
            if total_sends > 0:  # Avoid division by zero
                # Group by week
                week_totals = {}
                current_week = None
                week_start = None
                
                for date, sends in sorted(daily_totals.items()):
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    if week_start is None or date_obj - week_start >= timedelta(days=7):
                        week_start = date_obj - timedelta(days=date_obj.weekday())
                        current_week = week_start.strftime('%Y-%m-%d')
                        week_totals[current_week] = {'total': 0, 'days': []}
                    
                    week_totals[current_week]['total'] += sends
                    week_totals[current_week]['days'].append((date, sends))
                
                # Print weekly summaries and daily breakdowns
                for week_start, data in week_totals.items():
                    week_total = data['total']
                    week_percentage = (week_total / total_sends) * 100
                    week_bar_length = int((week_total / total_sends) * max_bar_length)
                    week_bar = '█' * week_bar_length
                    
                    week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')
                    print(f"\nWeek {week_start} to {week_end}:")
                    print(f"Weekly Total: {week_total:4d} sends ({week_percentage:5.1f}%) {week_bar}")
                    
                    # Print daily breakdown for this week
                    if data['days']:
                        print("Daily Breakdown:")
                        for date, sends in data['days']:
                            if sends > 0:  # Only show days with sends
                                day_percentage = (sends / total_sends) * 100
                                day_bar_length = int((sends / total_sends) * max_bar_length)
                                day_bar = '▌' * day_bar_length
                                print(f"  {date}: {sends:4d} sends ({day_percentage:5.1f}%) {day_bar}")
            
            # Print workspace details
            print("\nWorkspace Details:")
            for idx, (api_key, workspace_data) in enumerate(result.get('data', {}).items(), 1):
                print(f"\nWorkspace #{idx} (API Key: {api_key[:10]}...):")
                
                # Extract and validate workspace data
                campaign_analytics = workspace_data.get('campaign_analytics', {})
                total_sent = workspace_data.get('total_sent', 0)
                error = workspace_data.get('error')
                
                print(f"Total Campaigns: {len(campaign_analytics)}")
                print(f"Total Sends: {total_sent}")
                
                if error:
                    print(f"Error: {error}")
                    continue
                
                # Show campaign details
                if campaign_analytics:
                    print("\nCampaign Statistics:")
                    for campaign_id, data in list(campaign_analytics.items())[:5]:
                        print(f"\nCampaign {campaign_id}:")
                        print(f"Total Sends: {data.get('total_sent', 0)}")
                        
                        # Show daily sends for this campaign grouped by week
                        if data.get('daily_sends'):
                            # Group by week
                            week_totals = {}
                            current_week = None
                            week_start = None
                            
                            for date, sends in sorted(data['daily_sends'].items()):
                                date_obj = datetime.strptime(date, '%Y-%m-%d')
                                if week_start is None or date_obj - week_start >= timedelta(days=7):
                                    week_start = date_obj - timedelta(days=date_obj.weekday())
                                    current_week = week_start.strftime('%Y-%m-%d')
                                    week_totals[current_week] = {'total': 0, 'days': []}
                                
                                week_totals[current_week]['total'] += sends
                                week_totals[current_week]['days'].append((date, sends))
                            
                            if week_totals:
                                print("Weekly Breakdown:")
                                for week_start, week_data in week_totals.items():
                                    if week_data['total'] > 0:
                                        week_end = (datetime.strptime(week_start, '%Y-%m-%d') + 
                                                  timedelta(days=6)).strftime('%Y-%m-%d')
                                        week_percentage = (week_data['total'] / data['total_sent']) * 100
                                        week_bar_length = int((week_data['total'] / data['total_sent']) * 20)
                                        week_bar = '█' * week_bar_length
                                        
                                        print(f"\n  Week {week_start} to {week_end}:")
                                        print(f"  Weekly Total: {week_data['total']:4d} sends ({week_percentage:5.1f}%) {week_bar}")
                                        
                                        # Show daily breakdown for days with sends
                                        days_with_sends = [(d, s) for d, s in week_data['days'] if s > 0]
                                        if days_with_sends:
                                            print("  Daily Activity:")
                                            for date, sends in days_with_sends:
                                                day_percentage = (sends / data['total_sent']) * 100
                                                day_bar_length = int((sends / data['total_sent']) * 20)
                                                day_bar = '▌' * day_bar_length
                                                print(f"    {date}: {sends:4d} sends ({day_percentage:5.1f}%) {day_bar}")
                        
                        if data.get('error'):
                            print(f"  Error: {data['error']}")
                            
                    if len(campaign_analytics) > 5:
                        print(f"\n... and {len(campaign_analytics) - 5} more campaigns")
        else:
            print("\nError in response:", result.get('error', 'Unknown error'))
            
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
