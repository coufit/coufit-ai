from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from services.recommendation import recommend_stores   # FAISS 추천
from services.llm_service import LLMService             # Qwen 모델

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommend", tags=["recommend"])

# ✅ 전역 서비스 인스턴스
llm_service = LLMService()

# 요청 body 모델
class RecommendRequest(BaseModel):
    user_id: int
    user_lat: Optional[float] = None
    user_lon: Optional[float] = None
    k: int = 10


# ---------------------------
# 1️⃣ 기본 추천 엔드포인트
# ---------------------------
@router.post("/top-stores")
def recommend_top_stores(request: RecommendRequest):
    """FAISS 기반 기본 추천"""
    try:
        logger.info(f"user_id={request.user_id}, lat={request.user_lat}, lon={request.user_lon}")
        result = recommend_stores(
            user_id=request.user_id,
            user_lat=request.user_lat,
            user_lon=request.user_lon,
            k=request.k,
        )
        if not result:
            raise HTTPException(status_code=404, detail="추천 결과가 없습니다.")
        return {"recommendations": result}
    except Exception as e:
        logger.exception("추천 중 오류 발생")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------
# 2️⃣ LLM 기반 설명형 추천
# ---------------------------
@router.post("/with-llm")
async def recommend_with_explanation(request: RecommendRequest):
    recommendations = recommend_stores(
        user_id=request.user_id,
        user_lat=request.user_lat,
        user_lon=request.user_lon,
        k=request.k,
    )

    if not recommendations:
        raise HTTPException(status_code=404, detail="추천 결과가 없습니다.")

    # LLM에 프롬프트 생성
    store_list_text = "\n".join([
        f"{i+1}. {r['name']} ({r['category']})"
        for i, r in enumerate(recommendations)
    ])
    context = f"유저 {request.user_id}의 추천 결과:\n{store_list_text}"

    prompt = "아래 가맹점 목록을 기반으로 친근한 말투로 추천 이유를 설명해주세요."

    explanation = await llm_service.chat_with_context(user_message=prompt, context=context, max_tokens=800)
    return {"recommendations": recommendations, "explanation": explanation}
