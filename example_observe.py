"""
Langfuse @observe 데코레이터를 사용한 간단한 추적 예시
"""
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context
import openai
from config import config

# Langfuse 초기화
langfuse = Langfuse(
    secret_key=config.LANGFUSE_SECRET_KEY,
    public_key=config.LANGFUSE_PUBLIC_KEY,
    host=config.LANGFUSE_HOST
)

# OpenAI 클라이언트
openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)


# ========================================
# 방법 1: @observe 데코레이터 (가장 간단)
# ========================================
@observe()
def simple_chat(user_message: str, model: str = "gpt-3.5-turbo"):
    """
    @observe 데코레이터만 붙이면 자동으로 추적됨
    - 함수 입력/출력 자동 기록
    - 실행 시간 자동 측정
    - 에러 자동 캡처
    """
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}]
    )
    return response.choices[0].message.content


# ========================================
# 방법 2: 메타데이터와 함께 추적
# ========================================
@observe()
def chat_with_metadata(
    user_message: str,
    user_id: str = None,
    session_id: str = None,
    model: str = "gpt-3.5-turbo"
):
    """
    메타데이터를 포함한 추적
    """
    # trace에 메타데이터 추가
    langfuse_context.update_current_trace(
        user_id=user_id,
        session_id=session_id,
        tags=["api", "chat"],
        metadata={"model": model}
    )

    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}]
    )

    result = response.choices[0].message.content

    # observation에 추가 정보 기록
    langfuse_context.update_current_observation(
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens,
            "total": response.usage.total_tokens
        }
    )

    return result


# ========================================
# 방법 3: 중첩 함수로 계층 추적
# ========================================
@observe()
def preprocess_message(message: str) -> str:
    """전처리 단계를 별도로 추적"""
    cleaned = message.strip().lower()
    return cleaned


@observe()
def call_openai(messages: list, model: str):
    """OpenAI 호출을 별도로 추적"""
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages
    )

    # 사용량 정보 기록
    langfuse_context.update_current_observation(
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens
        },
        metadata={"model": response.model}
    )

    return response.choices[0].message.content


@observe()
def hierarchical_chat(user_message: str, model: str = "gpt-3.5-turbo"):
    """
    여러 단계로 나뉜 처리를 계층적으로 추적
    Langfuse에서 트리 구조로 표시됨:

    hierarchical_chat
    ├── preprocess_message
    └── call_openai
    """
    # 1단계: 전처리 (자동으로 child span 생성)
    processed = preprocess_message(user_message)

    # 2단계: OpenAI 호출 (자동으로 child span 생성)
    messages = [{"role": "user", "content": processed}]
    result = call_openai(messages, model)

    return result


# ========================================
# 방법 4: Generation 명시적 추적
# ========================================
@observe(as_type="generation")
def tracked_generation(
    user_message: str,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7
):
    """
    LLM 호출을 'generation' 타입으로 명시적 추적
    - Langfuse에서 cost 자동 계산
    - 토큰 사용량 자동 집계
    """
    response = openai_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_message}],
        temperature=temperature
    )

    # generation 메타데이터 업데이트
    langfuse_context.update_current_observation(
        model=model,
        model_parameters={"temperature": temperature},
        usage={
            "input": response.usage.prompt_tokens,
            "output": response.usage.completion_tokens
        },
        output=response.choices[0].message.content
    )

    return response.choices[0].message.content


# ========================================
# 사용 예시
# ========================================
if __name__ == "__main__":
    print("=== Langfuse @observe 데코레이터 예시 ===\n")

    # 예시 1: 가장 간단한 방식
    print("1. 간단한 추적:")
    result1 = simple_chat("Python에서 리스트와 튜플의 차이는?")
    print(f"응답: {result1[:100]}...\n")

    # 예시 2: 메타데이터 포함
    print("2. 메타데이터 포함:")
    result2 = chat_with_metadata(
        "FastAPI의 장점은?",
        user_id="user_123",
        session_id="session_456"
    )
    print(f"응답: {result2[:100]}...\n")

    # 예시 3: 계층적 추적
    print("3. 계층적 추적:")
    result3 = hierarchical_chat("   LANGFUSE란 무엇인가?   ")
    print(f"응답: {result3[:100]}...\n")

    # 예시 4: Generation 타입 추적
    print("4. Generation 타입 추적:")
    result4 = tracked_generation(
        "Langfuse의 주요 기능 3가지",
        temperature=0.9
    )
    print(f"응답: {result4[:100]}...\n")

    # 모든 이벤트를 Langfuse로 전송
    langfuse.flush()
    print("✅ 모든 추적 데이터가 Langfuse로 전송되었습니다!")
    print(f"📊 대시보드: {config.LANGFUSE_HOST}")
