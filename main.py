from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import recommend, llm
from model_builders.store_index_builder import build_store_index
from model_builders.user_vector_builder import build_user_vectors

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버 시작 - 모델 빌드 중...")
    
    # 기존 추천 모델 빌드
    build_store_index()
    build_user_vectors()
    print("추천 모델 빌드 완료")
    
    # LLM 서비스 초기화
    try:
        print("LLM 서비스 초기화 중...")
        await llm.initialize_llm_service()
        print("✅ LLM 서비스 초기화 완료!")
    except Exception as e:
        print(f"❌ LLM 서비스 초기화 실패: {e}")
        print("LLM 서비스 없이 계속 진행합니다...")
    
    print("🚀 모든 모델 빌드 및 로드 완료")
    
    yield
    
    # 종료 시 처리
    print("🧹 서버 종료 - 리소스 정리 중...")
    try:
        llm.cleanup_llm_service()
        print("✅ LLM 서비스 정리 완료")
    except Exception as e:
        print(f"LLM 서비스 정리 중 오류: {e}")

app = FastAPI(
    title="COUFIT-AI API",
    description="COUFIT-AI의 AI 서버입니다.",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 서비스에서는 도메인 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(recommend.router)
app.include_router(llm.router)

@app.get("/")
def root():
    return {
        "message": "COUFIT-AI의 AI 서버가 정상 동작 중입니다!",
        "services": ["recommendation", "llm"]
    }

@app.get("/health")
async def health_check():
    """전체 서비스 상태 확인"""
    try:
        llm_status = await llm.llm_health()
    except Exception:
        llm_status = {"status": "error", "model_loaded": False}
    
    return {
        "status": "healthy",
        "services": {
            "recommendation": "active",  # 추천 서비스는 항상 활성화
            "llm": llm_status
        }
    }