"""
Langfuse 연결 및 데이터 전송 디버깅
"""
from langfuse import Langfuse
from config import config
import time

print("=" * 60)
print("Langfuse 디버깅")
print("=" * 60)

# 설정 출력
print(f"\n환경변수:")
print(f"  HOST: {config.LANGFUSE_HOST}")
print(f"  SECRET_KEY: {config.LANGFUSE_SECRET_KEY}")
print(f"  PUBLIC_KEY: {config.LANGFUSE_PUBLIC_KEY}")

# Langfuse 클라이언트 생성
print(f"\nLangfuse 클라이언트 초기화 중...")
langfuse = Langfuse(
    secret_key=config.LANGFUSE_SECRET_KEY,
    public_key=config.LANGFUSE_PUBLIC_KEY,
    host=config.LANGFUSE_HOST,
    debug=True  # 디버그 모드 활성화
)
print("✅ 초기화 완료")

# Context manager 방식으로 trace 생성
print("\n테스트 trace 생성 중...")
trace_id = None
with langfuse.start_as_current_span(
    name="debug_test_trace",
    input={"message": "debugging test"}
) as span:
    span.update_trace(
        user_id="debug_user",
        session_id="debug_session_001",
        tags=["debug", "test"],
        metadata={"test": "debugging"}
    )

    trace_id = langfuse.get_current_trace_id()
    print(f"✅ Trace 생성됨: {trace_id}")

    # Generation 추가
    print("\nGeneration 추가 중...")
    with langfuse.start_as_current_observation(
        as_type="generation",
        name="test_generation",
        model="gpt-3.5-turbo",
        input="test input"
    ) as generation:
        generation.update(
            output="test output",
            usage_details={
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30
            }
        )
        print(f"✅ Generation 추가됨")

    span.update(output={"result": "success"})

# 즉시 flush
print("\n데이터 전송 중 (flush)...")
langfuse.flush()
print("✅ Flush 완료")

# 전송 확인을 위해 대기
print("\n전송 완료 대기 중 (3초)...")
time.sleep(3)

print("\n" + "=" * 60)
print("완료!")
print("=" * 60)
print(f"\n📊 Langfuse 대시보드 확인:")
print(f"   {config.LANGFUSE_HOST}")
print(f"\n🔍 필터:")
print(f"   - User ID: debug_user")
print(f"   - Session ID: debug_session_001")
print(f"   - Trace ID: {trace_id}")
print("\n" + "=" * 60)
