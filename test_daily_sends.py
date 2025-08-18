import requests
import json
import time
from datetime import datetime, timedelta

def test_api():
    # Calculate date range for last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    # Format dates as YYYY-MM-DD
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')
    
    print(f"\nFetching data from {start_date_str} to {end_date_str} (30 days)")

    def check_job_status(run_id, delay=5):
        """Check job status until completion"""
        last_completion = -1
        last_update_time = time.time()
        
        while True:
            try:
                response = requests.get(f'http://localhost:5000/analytics/bulk/status/{run_id}')
                response.raise_for_status()
                data = response.json()
                
                completion = data['completion']
                if completion != last_completion:
                    print(f"\rJob completion: {completion}%", end="")
                    last_completion = completion
                    last_update_time = time.time()
                else:
                    # If no progress in 2 minutes, print a message but keep waiting
                    time_since_update = time.time() - last_update_time
                    if time_since_update >= 120:
                        print(f"\rNo progress in {int(time_since_update)}s, still waiting... Current: {completion}%", end="")
                        last_update_time = time.time()
                
                if data['status'] == 'completed':
                    print("\nJob completed successfully!")
                    return data
                elif data['status'] == 'failed':
                    print(f"\nJob failed: {data.get('error', 'Unknown error')}")
                    return None
                    
                time.sleep(delay)
            except requests.exceptions.RequestException as e:
                print(f"\nError checking status: {e}")
                print("Retrying in 10 seconds...")
                time.sleep(10)
                continue
            except Exception as e:
                print(f"\nUnexpected error: {e}")
                print("Retrying in 10 seconds...")
                time.sleep(10)
                continue

    # Test data with multiple API keys
    payload = {
        "api_keys": [
            "NDYxYzRlNjctOGU1OS00MzUxLWJkMzctNTVmMTA0ZDk4NGQ3OlpNem1reEtIdlVBSg==",  # Workspace 1
            "YTZjNTYyYzItYTFiMS00YjAyLWI0MzAtNGQwMjQ1NmNjYzJjOlZXakNhZ1RiWGlKYg==",  # Workspace 2
            "OTZmM2YxYjAtNTkxOC00MTZhLWIxMzAtNjY0ZmI3OWYwZjZlOkhySmd4QVNjVnBaRQ=="    # Workspace 3
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

        # Create a daily sends summary with all days initialized to 0
        daily_sends = {}
        current_date = start_date
        while current_date <= end_date:
            daily_sends[current_date.strftime('%Y-%m-%d')] = 0
            current_date += timedelta(days=1)
        
        # Update with actual send counts
        if result.get('daily_totals'):
            daily_sends.update(result['daily_totals'])

        # Save daily sends summary to file
        output_data = {
            'daily_totals': daily_sends,
            'workspace_data': result.get('data', {}),
            'total_sends': result.get('total_sends', 0)
        }
        
        with open('daily_sends.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, sort_keys=True)

        print("\nAnalytics data saved to daily_sends.json")
        print("\nWorkspace Summary:")
        print("-" * 50)
        
        for api_key, workspace in result.get('data', {}).items():
            masked_key = f"...{api_key[-4:]}"
            total_sent = workspace.get('total_sent', 0)
            error = workspace.get('error')
            
            print(f"\nWorkspace (API key: {masked_key})")
            print(f"Total Sends: {total_sent:,}")
            if error:
                print(f"Error: {error}")
            
            # Show campaign counts
            campaign_count = len(workspace.get('campaign_analytics', {}))
            print(f"Campaigns processed: {campaign_count}")
            
        print("\nOverall Statistics:")
        print("-" * 50)
        print(f"Total sends across all workspaces: {result.get('total_sends', 0):,}")
        print(f"\nDaily Totals (All Workspaces):")
        print("Date         Sends")
        print("-" * 20)
        for date, sends in sorted(daily_sends.items()):
            print(f"{date}: {sends:,}")
            
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
