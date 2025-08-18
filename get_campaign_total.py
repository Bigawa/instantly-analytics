from instantly_campaign_analytics_api import InstantlyCampaignAnalyticsAPI
import json
from datetime import datetime, timedelta

def get_campaign_total_sent(campaign_id: str, start_date: str, end_date: str):
    """
    Get total sent emails for a campaign within a date range
    """
    API_KEY = "OTViMWNhOGYtZjE5Yi00NTczLTkxODctYzRlM2RlYzc1NzA5OlZvRGF0dHhoZWJuQQ=="
    api = InstantlyCampaignAnalyticsAPI(API_KEY)
    
    try:
        # Get analytics for date range
        analytics = api.get_daily_campaign_analytics(
            campaign_id=campaign_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Convert analytics list to dictionary for easy lookup
        analytics_dict = {day['date']: day['sent'] for day in analytics}
        
        # Generate all dates in range
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        date_range = []
        current = start
        while current <= end:
            date_str = current.strftime('%Y-%m-%d')
            date_range.append(date_str)
            current += timedelta(days=1)
            
        # Calculate total sent
        total_sent = sum(analytics_dict.get(date, 0) for date in date_range)
        
        # Analyze the data
        zero_days = [date for date in date_range if analytics_dict.get(date, 0) == 0]
        active_days = [date for date in date_range if analytics_dict.get(date, 0) > 0]
        max_day = max(date_range, key=lambda x: analytics_dict.get(x, 0))
        min_active_day = min((d for d in date_range if analytics_dict.get(d, 0) > 0), 
                           key=lambda x: analytics_dict.get(x, 0))

        # Analyze by day of week
        day_of_week_totals = {i: 0 for i in range(7)}  # 0 = Monday, 6 = Sunday
        day_of_week_counts = {i: 0 for i in range(7)}
        for date in date_range:
            day_num = datetime.strptime(date, '%Y-%m-%d').weekday()
            sends = analytics_dict.get(date, 0)
            day_of_week_totals[day_num] += sends
            if sends > 0:
                day_of_week_counts[day_num] += 1

        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        print(f"\nCampaign: {campaign_id}")
        print(f"Period: {start_date} to {end_date}")
        print(f"\nSummary:")
        print(f"Total Days: {len(date_range)}")
        print(f"Days with Activity: {len(active_days)}")
        print(f"Days with Zero Sends: {len(zero_days)}")
        print(f"Total Emails Sent: {total_sent}")
        print(f"Highest Day: {max_day} ({analytics_dict[max_day]} sends)")
        print(f"Lowest Active Day: {min_active_day} ({analytics_dict[min_active_day]} sends)")

        print(f"\nDay of Week Analysis:")
        for i, day in enumerate(days):
            total = day_of_week_totals[i]
            active_count = day_of_week_counts[i]
            avg = total / active_count if active_count > 0 else 0
            print(f"{day}: {total} total sends, {active_count} active days, {avg:.1f} avg sends per active day")
        
        print(f"\nZero Send Days:")
        for date in zero_days:
            day_name = days[datetime.strptime(date, '%Y-%m-%d').weekday()]
            print(f"Date: {date} ({day_name})")
        
        print("\nDaily Breakdown:")
        for date in date_range:
            sent = analytics_dict.get(date, 0)
            day_name = days[datetime.strptime(date, '%Y-%m-%d').weekday()]
            print(f"Date: {date} ({day_name}), Sent: {sent}")
            
        return total_sent
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    # Example: Get total sent for a month
    campaign_id = "fba231f6-234d-4e68-a426-8fa3f667aaf7"
    
    # Get last month's data
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    total = get_campaign_total_sent(campaign_id, start_date, end_date)
    
    if total is not None:
        print(f"\nTotal emails sent in the last 30 days: {total}")
