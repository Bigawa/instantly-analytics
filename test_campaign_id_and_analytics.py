from instantly_campaign_api import InstantlyCampaignAPI
from instantly_campaign_analytics_api import InstantlyCampaignAnalyticsAPI
import datetime
import json

def test_campaign_id_and_analytics(api_key: str):
    import logging
    logging.basicConfig(filename='campaign_analytics_debug.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    # Get first 10 campaign IDs
    campaign_api = InstantlyCampaignAPI(api_key)
    campaign_ids = campaign_api.get_campaign_ids(limit=10)
    print(f"Fetched {len(campaign_ids)} campaign IDs: {campaign_ids}")
    logging.info(f"Fetched campaign IDs: {campaign_ids}")

    # Prepare last 2 days
    today = datetime.date.today()
    last_2_days = [(today - datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(2)]

    analytics_api = InstantlyCampaignAnalyticsAPI(api_key)
    results = {}
    for campaign_id in campaign_ids:
        results[campaign_id] = {}
        for day in last_2_days:
            try:
                logging.info(f"Requesting analytics for campaign {campaign_id} on {day}")
                analytics = analytics_api.get_daily_campaign_analytics(campaign_id, day)
                logging.info(f"Response for {campaign_id} on {day}: {analytics}")
                sent = analytics.get('sent') if analytics else None
                results[campaign_id][day] = sent
            except Exception as e:
                logging.error(f"Error for {campaign_id} on {day}: {e}")
                results[campaign_id][day] = f"Error: {e}"
    # Save results to JSON
    with open('campaign_analytics_last_2_days.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Saved analytics to campaign_analytics_last_2_days.json")

    # Test the example campaign ID and date range from your curl example
    example_campaign_id = 'fba231f6-234d-4e68-a426-8fa3f667aaf7'
    start_date = '2025-04-11'
    end_date = '2025-08-11'
    try:
        logging.info(f"Requesting analytics for example campaign {example_campaign_id} from {start_date} to {end_date}")
        response = analytics_api.get_daily_campaign_analytics(example_campaign_id, start_date)
        # The current get_daily_campaign_analytics only supports one day, so let's fetch for all days in the range
        date_list = []
        start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        delta = end_dt - start_dt
        for i in range(delta.days + 1):
            date_list.append((start_dt + datetime.timedelta(days=i)).strftime('%Y-%m-%d'))
        example_results = {}
        for day in date_list:
            try:
                analytics = analytics_api.get_daily_campaign_analytics(example_campaign_id, day)
                logging.info(f"Example response for {example_campaign_id} on {day}: {analytics}")
                sent = analytics.get('sent') if analytics else None
                example_results[day] = sent
            except Exception as e:
                logging.error(f"Error for example campaign {example_campaign_id} on {day}: {e}")
                example_results[day] = f"Error: {e}"
        with open('example_campaign_analytics.json', 'w', encoding='utf-8') as f:
            json.dump(example_results, f, ensure_ascii=False, indent=2)
        print("Saved example campaign analytics to example_campaign_analytics.json")
    except Exception as e:
        logging.error(f"Error testing example campaign: {e}")

if __name__ == "__main__":
    API_KEY = "OTViMWNhOGYtZjE5Yi00NTczLTkxODctYzRlM2RlYzc1NzA5OlZvRGF0dHhoZWJuQQ=="  # Replace with your actual API key
    test_campaign_id_and_analytics(API_KEY)
