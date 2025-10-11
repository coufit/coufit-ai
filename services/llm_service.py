from model_builders.model_loader import get_loader
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        # Qwen 모델 로더 초기화
        self.loader = get_loader()

    async def initialize(self):
        """서비스 초기화 - 모델 로딩"""
        try:
            if self.loader.model is None:
                logger.info("LLM 서비스 초기화 중...")
                # get_loader()가 내부에서 자동 로딩하므로 별도 load_model() 불필요
                logger.info("LLM 서비스 초기화 완료")
        except Exception as e:
            logger.error(f"LLM 서비스 초기화 실패: {e}")
            raise

    def is_ready(self) -> bool:
        """서비스 준비 상태 확인"""
        return self.loader.model is not None

    async def generate_response(
        self,
        prompt: str,
        max_tokens: int = 100,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: Optional[int] = None,
    ) -> str:
        """텍스트 생성"""
        if not self.is_ready():
            raise RuntimeError("LLM 서비스가 초기화되지 않았습니다")

        try:
            return self.loader.generate_text(
                prompt,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                top_k=top_k,
            )
        except Exception as e:
            logger.error(f"텍스트 생성 실패: {e}")
            raise

    async def chat_with_context(
        self,
        user_message: str,
        context: Optional[str] = None,
        max_tokens: int = 200,
    ) -> str:
        """컨텍스트를 포함한 채팅"""
        if context:
            prompt = f"다음 정보를 참고해서 답변해주세요:\n{context}\n\n질문: {user_message}"
        else:
            prompt = user_message

        return await self.generate_response(prompt, max_tokens=max_tokens)

    def cleanup(self):
        """서비스 정리"""
        try:
            self.loader.cleanup()
            logger.info("LLM 리소스 정리 완료")
        except Exception as e:
            logger.error(f"LLM 서비스 정리 중 오류 발생: {e}")
