from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from services.llm_service import LLMService

router = APIRouter(prefix="/llm", tags=["LLM"])

# 전역 LLM 서비스 인스턴스
llm_service = LLMService()

class ChatRequest(BaseModel):
    prompt: str
    max_tokens: Optional[int] = 100
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = 0.9
    top_k: Optional[int] = 50

class ChatWithContextRequest(BaseModel):
    user_message: str
    context: Optional[str] = None
    max_tokens: Optional[int] = 200

class ChatResponse(BaseModel):
    response: str
    prompt: str

@router.get("/health")
async def llm_health():
    """LLM 서비스 상태 확인"""
    return {
        "status": "healthy" if llm_service.is_ready() else "loading",
        "model_loaded": llm_service.is_ready()
    }

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """기본 채팅 엔드포인트"""
    try:
        if not llm_service.is_ready():
            raise HTTPException(status_code=503, detail="LLM 서비스가 아직 초기화 중입니다")
        
        response = await llm_service.generate_response(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k
        )
        
        return ChatResponse(response=response, prompt=request.prompt)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"응답 생성 실패: {str(e)}")

@router.post("/chat-with-context")
async def chat_with_context(request: ChatWithContextRequest):
    """컨텍스트를 포함한 채팅"""
    try:
        if not llm_service.is_ready():
            raise HTTPException(status_code=503, detail="LLM 서비스가 아직 초기화 중입니다")
        
        response = await llm_service.chat_with_context(
            user_message=request.user_message,
            context=request.context,
            max_tokens=request.max_tokens
        )
        
        return {"response": response, "user_message": request.user_message}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"응답 생성 실패: {str(e)}")

@router.post("/generate")
async def generate_text_endpoint(request: ChatRequest):
    """간단한 텍스트 생성"""
    try:
        if not llm_service.is_ready():
            raise HTTPException(status_code=503, detail="LLM 서비스가 아직 초기화 중입니다")
        
        response = await llm_service.generate_response(
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k
        )
        
        return {"generated_text": response}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"텍스트 생성 실패: {str(e)}")

# 서비스 초기화 함수
async def initialize_llm_service():
    """LLM 서비스 초기화"""
    await llm_service.initialize()

def cleanup_llm_service():
    """LLM 서비스 정리"""
    llm_service.cleanup()