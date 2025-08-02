from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from api import recommend
from model_builders.store_index_builder import build_store_index
from model_builders.user_vector_builder import build_user_vectors

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("서버 시작 - 모델 빌드 중...")
    build_store_index()
    print("모델 빌드 및 로드 완료")
    yield
    # 종료 시 처리 필요하면 여기에 작성

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

app.include_router(recommend.router)

@app.get("/")
def root():
    return {"message": "COUFIT-AI의 AI 서버가 정상 동작 중입니다!"}
