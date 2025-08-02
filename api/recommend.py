from fastapi import APIRouter, HTTPException
from services.recommendation import recommend_stores
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommend", tags=["recommend"])

@router.get("/top-stores")
def recommend_top_stores(user_id: int, user_lat: float = None, user_lon: float = None, k: int = 10):
    try:
        logger.info(f"user_id: {user_id}, user_lat: {user_lat}, user_lon: {user_lon}")
        result = recommend_stores(user_id, user_lat, user_lon, k)
        if not result:
            raise HTTPException(status_code=404, detail="User ID not found or no recommendations")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))