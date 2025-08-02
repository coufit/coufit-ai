from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.recommendation import recommend_stores
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommend", tags=["recommend"])

# 요청 body 모델
class RecommendRequest(BaseModel):
    user_id: int
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None
    k: int = 10

@router.post("/top-stores")
def recommend_top_stores(request: RecommendRequest):
    try:
        logger.info(f"user_id: {request.user_id}, user_lat: {request.user_lat}, user_lon: {request.user_lon}")
        result = recommend_stores(
            user_id=request.user_id,
            user_lat=request.user_lat,
            user_lon=request.user_lon,
            k=request.k
        )
        if not result:
            raise HTTPException(status_code=404, detail="User ID not found or no recommendations")
        return result
    except Exception as e:
        logger.exception("추천 중 오류 발생")
        raise HTTPException(status_code=500, detail=str(e))
