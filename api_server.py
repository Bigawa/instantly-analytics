from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from instantly_campaign_api import InstantlyCampaignAPI
from instantly_campaign_analytics_api import InstantlyCampaignAnalyticsAPI
import uvicorn

app = FastAPI()

class AnalyticsRequest(BaseModel):
    api_keys: List[str]
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD

def split_date_range(start_date: str, end_date: str) -> List[tuple]:
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

@app.post("/analytics/bulk")
async def get_bulk_analytics(request: AnalyticsRequest) -> Dict[str, Any]:
    results = {}
    
    for api_key in request.api_keys:
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
                campaign_ids = campaign_api.get_campaign_ids()
            except Exception as e:
                workspace_data["error"] = f"Failed to fetch campaign IDs: {str(e)}"
                results[api_key] = workspace_data
                continue
                
            # Split date range into 7-day chunks
            date_chunks = split_date_range(request.start_date, request.end_date)
            
            # Get analytics for each campaign
            for campaign_id in campaign_ids:
                campaign_data = {
                    "daily_sends": {},
                    "total_sent": 0,
                    "error": None
                }
                
                try:
                    # Get analytics for each date chunk
                    for chunk_start, chunk_end in date_chunks:
                        analytics = analytics_api.get_daily_campaign_analytics(
                            campaign_id=campaign_id,
                            start_date=chunk_start,
                            end_date=chunk_end
                        )
                        
                        # Process analytics data
                        for day in analytics:
                            date = day['date']
                            sends = day['sent']
                            campaign_data["daily_sends"][date] = sends
                            campaign_data["total_sent"] += sends
                            workspace_data["total_sent"] += sends
                            
                except Exception as e:
                    campaign_data["error"] = f"Failed to fetch analytics: {str(e)}"
                
                workspace_data["campaign_analytics"][campaign_id] = campaign_data
                
            results[api_key] = workspace_data
            
        except Exception as e:
            results[api_key] = {
                "campaign_analytics": {},
                "total_sent": 0,
                "error": f"Workspace error: {str(e)}"
            }
    
    return {
        "status": "success",
        "data": results
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
