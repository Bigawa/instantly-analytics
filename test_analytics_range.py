from instantly_campaign_analytics_api import InstantlyCampaignAnalyticsAPI
import json
from datetime import datetime, timedelta

def test_analytics_range():
    # Your API key
    API_KEY = "OTViMWNhOGYtZjE5Yi00NTczLTkxODctYzRlM2RlYzc1NzA5OlZvRGF0dHhoZWJuQQ=="
    
    # Example campaign ID
    campaign_id = "fba231f6-234d-4e68-a426-8fa3f667aaf7"
    
    # Get analytics for last 7 days
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    api = InstantlyCampaignAnalyticsAPI(API_KEY)
    
    try:
        # Get analytics for date range
        analytics = api.get_daily_campaign_analytics(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date
        )
        
        print(f"\nAnalytics for campaign {campaign_id} from {start_date} to {end_date}:")
        for day in analytics:
            print(f"Date: {day['date']}, Sent: {day['sent']}, Replies: {day['replies']}")
            
        # Save full results to JSON
        with open('analytics_range_results.json', 'w') as f:
            json.dump(analytics, f, indent=2)
            print(f"\nFull results saved to analytics_range_results.json")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_analytics_range()
