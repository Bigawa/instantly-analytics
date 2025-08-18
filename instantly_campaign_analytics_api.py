import requests
from typing import Optional, Dict, Any

class InstantlyCampaignAnalyticsAPI:
    BASE_URL = "https://api.instantly.ai/api/v2/campaigns/analytics/daily"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def get_daily_campaign_analytics(self, campaign_id: str, start_date: str, end_date: str = None, campaign_status: Optional[int] = None) -> list:
        """
        Fetch daily analytics for a given campaign between dates.
        Args:
            campaign_id: Campaign UUID.
            start_date: Start date in YYYY-MM-DD format.
            end_date: End date in YYYY-MM-DD format (optional, defaults to start_date).
            campaign_status: Optional campaign status filter.
        Returns:
            List of dictionaries with daily analytics data.
        """
        params = {
            "campaign_id": campaign_id,
            "start_date": start_date,
            "end_date": end_date or start_date
        }
        if campaign_status is not None:
            params["campaign_status"] = campaign_status

        response = requests.get(self.BASE_URL, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
