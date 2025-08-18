from instantly_campaign_api import InstantlyCampaignAPI
from instantly_campaign_analytics_api import InstantlyCampaignAnalyticsAPI

def test_get_campaign_ids(api_key: str):
    api = InstantlyCampaignAPI(api_key)
    try:
        campaign_ids = api.get_campaign_ids(limit=10)
        print(f"Fetched {len(campaign_ids)} campaign IDs:", campaign_ids)
    except Exception as e:
        print(f"Error fetching campaign IDs: {e}")

def test_daily_campaign_analytics(api_key: str, campaign_ids: list, date: str):
    import json
    analytics_api = InstantlyCampaignAnalyticsAPI(api_key)
    results = {}
    for campaign_id in campaign_ids:
        try:
            analytics = analytics_api.get_daily_campaign_analytics(campaign_id, date)
            results[campaign_id] = analytics
        except Exception as e:
            results[campaign_id] = {"error": str(e)}
    # Save results to JSON file
    with open(f"daily_campaign_analytics_{date}.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved analytics results to daily_campaign_analytics_{date}.json")

if __name__ == "__main__":
    # Replace with your actual API key
    API_KEY = "OTViMWNhOGYtZjE5Yi00NTczLTkxODctYzRlM2RlYzc1NzA5OlZvRGF0dHhoZWJuQQ=="
    test_get_campaign_ids(API_KEY)
    # List of campaign IDs to test
    CAMPAIGN_IDS = [
        '2112-6c37-4a8c-b185-2dec375f1b80',
        '084b5665-3909-4f22-a2e4-e81527b5131d',
        '06c8d903-15bd-4226-9d93-c57795d22950',
        '04b1143f-5f33-4d32-8e1e-ff4b2debe3c5',
        '02aa4766-09c0-4fee-ae13-9ca92d891c2b'
    ]
    # Example date in YYYY-MM-DD format
    DATE = "2025-08-10"
    test_daily_campaign_analytics(API_KEY, CAMPAIGN_IDS, DATE)
