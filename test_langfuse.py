"""
Langfuse 연결 및 추적 테스트 스크립트
"""
from langfuse import Langfuse, observe
import openai
from config import config
import time

print("=" * 60)
print("Langfuse 연결 테스트")
print("=" * 60)

# 1. 설정 확인
print("\n[1단계] 환경변수 확인:")
print(f"  ✓ LANGFUSE_HOST: {config.LANGFUSE_HOST}")
print(f"  ✓ SECRET_KEY: {config.LANGFUSE_SECRET_KEY[:20]}...")
print(f"  ✓ PUBLIC_KEY: {config.LANGFUSE_PUBLIC_KEY[:20]}...")
print(f"  ✓ OPENAI_API_KEY: {config.OPENAI_API_KEY[:20]}...")

# 2. Langfuse 클라이언트 초기화
print("\n[2단계] Langfuse 클라이언트 초기화:")
try:
    langfuse = Langfuse(
        secret_key=config.LANGFUSE_SECRET_KEY,
        public_key=config.LANGFUSE_PUBLIC_KEY,
        host=config.LANGFUSE_HOST
    )
    print("  ✅ Langfuse 클라이언트 생성 성공!")
except Exception as e:
    print(f"  ❌ 초기화 실패: {e}")
    exit(1)

# 3. OpenAI 클라이언트 초기화
print("\n[3단계] OpenAI 클라이언트 초기화:")
try:
    openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)
    print("  ✅ OpenAI 클라이언트 생성 성공!")
except Exception as e:
    print(f"  ❌ 초기화 실패: {e}")
    exit(1)

# 4. 간단한 추적 테스트
print("\n[4단계] @observe 데코레이터 테스트:")

@observe()
def test_simple_tracking():
    """가장 간단한 추적 테스트"""
    return "Hello from Langfuse!"

try:
    result = test_simple_tracking()
    print(f"  ✅ 함수 실행 성공: {result}")
except Exception as e:
    print(f"  ❌ 실행 실패: {e}")

# 5. OpenAI + Langfuse 통합 테스트
print("\n[5단계] OpenAI API 호출 + Langfuse 추적 테스트:")

def test_openai_tracking(message: str):
    """OpenAI 호출을 Context Manager 방식으로 추적"""
    with langfuse.start_as_current_span(
        name="test_openai_call",
        input={"message": message}
    ) as span:
        # Trace 메타데이터 설정
        span.update_trace(
            user_id="test_user",
            session_id="test_session_001",
            tags=["test", "debugging"]
        )

        # OpenAI 호출
        with langfuse.start_as_current_generation(
            name="openai_completion",
            model="gpt-3.5-turbo",
            input=[{"role": "user", "content": message}]
        ) as generation:
            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}],
                max_tokens=50
            )

            result = response.choices[0].message.content

            # Generation 정보 업데이트
            generation.update(
                output=result,
                usage_details={
                    "input_tokens": response.usage.prompt_tokens,
                    "output_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            )

        # Span 출력 업데이트
        span.update(output={"response": result})

        return result

try:
    print("  🤖 OpenAI에 요청 중...")
    answer = test_openai_tracking("Say 'Hello Langfuse!' in one sentence.")
    print(f"  ✅ OpenAI 응답: {answer}")
except Exception as e:
    print(f"  ❌ 실행 실패: {e}")
    import traceback
    traceback.print_exc()

# 6. Langfuse로 데이터 전송
print("\n[6단계] Langfuse로 추적 데이터 전송:")
try:
    print("  📤 데이터 전송 중...")
    langfuse.flush()
    time.sleep(2)  # 전송 완료 대기
    print("  ✅ 전송 완료!")
except Exception as e:
    print(f"  ❌ 전송 실패: {e}")

# 7. 결과 확인 안내
print("\n" + "=" * 60)
print("테스트 완료!")
print("=" * 60)
print(f"\n📊 Langfuse 대시보드에서 확인:")
print(f"   {config.LANGFUSE_HOST}")
print("\n💡 팁:")
print("   - 대시보드의 'Traces' 메뉴에서 방금 생성된 추적 확인")
print("   - 'test_user'로 필터링하면 이 테스트 데이터만 볼 수 있음")
print("   - 'test_session_001' 세션 ID로도 검색 가능")
print("\n" + "=" * 60)
