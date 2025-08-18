import requests
from typing import List, Optional

class InstantlyCampaignAPI:
    BASE_URL = "https://api.instantly.ai/api/v2/campaigns"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

    def get_campaign_ids(self, limit: int = 100, search: Optional[str] = None, tag_ids: Optional[List[str]] = None) -> List[str]:
        """
        Fetch all campaign IDs from Instantly workspace.
        Args:
            limit: Number of items to return (max 100).
            search: Search by campaign name.
            tag_ids: List of tag IDs to filter campaigns.
        Returns:
            List of campaign IDs.
        """
        params = {"limit": limit}
        if search:
            params["search"] = search
        if tag_ids:
            params["tag_ids"] = ",".join(tag_ids)
        campaign_ids = []
        starting_after = None
        while True:
            if starting_after:
                params["starting_after"] = starting_after
            response = requests.get(self.BASE_URL, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            items = data.get("items", [])
            campaign_ids.extend([item["id"] for item in items if "id" in item])
            starting_after = data.get("next_starting_after")
            if not starting_after or not items:
                break
        return campaign_ids
