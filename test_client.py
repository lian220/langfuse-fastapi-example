"""
Test client to demonstrate all Langfuse features
"""
import httpx
import json
import asyncio
from datetime import datetime
import uuid
from typing import Dict, Any, Optional


class LangfuseExampleClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.session_id = str(uuid.uuid4())
        self.user_id = f"test_user_{uuid.uuid4().hex[:8]}"

    async def health_check(self):
        """Check if server is healthy"""
        response = await self.client.get(f"{self.base_url}/")
        return response.json()

    async def chat(self,
                  messages: list,
                  model: str = "gpt-3.5-turbo",
                  temperature: float = 0.7,
                  max_tokens: int = 500,
                  metadata: Optional[Dict[str, Any]] = None):
        """Send chat request with Langfuse tracking"""
        payload = {
            "messages": messages,
            "model": model,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "metadata": metadata or {}
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/chat",
            json=payload
        )
        return response.json()

    async def submit_feedback(self,
                            trace_id: str,
                            score: float,
                            comment: Optional[str] = None,
                            name: str = "user-feedback"):
        """Submit feedback for a trace"""
        payload = {
            "trace_id": trace_id,
            "score": score,
            "comment": comment,
            "name": name
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/feedback",
            json=payload
        )
        return response.json()

    async def use_prompt(self,
                        prompt_name: str,
                        variables: Dict[str, Any],
                        model: str = "gpt-3.5-turbo",
                        temperature: float = 0.7):
        """Use a predefined prompt template"""
        payload = {
            "prompt_name": prompt_name,
            "variables": variables,
            "model": model,
            "temperature": temperature,
            "session_id": self.session_id,
            "user_id": self.user_id
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/prompt-completion",
            json=payload
        )
        return response.json()

    async def evaluate_generation(self,
                                 trace_id: str,
                                 evaluation_name: str = "quality",
                                 criteria: Optional[str] = None):
        """Evaluate a generation"""
        payload = {
            "trace_id": trace_id,
            "evaluation_name": evaluation_name,
            "criteria": criteria
        }

        response = await self.client.post(
            f"{self.base_url}/api/v1/evaluate",
            json=payload
        )
        return response.json()

    async def get_session_info(self, session_id: Optional[str] = None):
        """Get session information"""
        session = session_id or self.session_id
        response = await self.client.get(
            f"{self.base_url}/api/v1/sessions/{session}"
        )
        return response.json()

    async def log_event(self, name: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a custom event"""
        params = {"name": name}
        if metadata:
            params["metadata"] = json.dumps(metadata)

        response = await self.client.post(
            f"{self.base_url}/api/v1/event",
            params=params
        )
        return response.json()

    async def close(self):
        """Close the client"""
        await self.client.aclose()


async def demonstrate_features():
    """Demonstrate all Langfuse features"""
    print("🚀 Starting Langfuse Example Client Demo")
    print("-" * 50)

    client = LangfuseExampleClient()

    try:
        # 1. Health Check
        print("\n1️⃣  Health Check")
        health = await client.health_check()
        print(f"   Server Status: {health['status']}")
        print(f"   Langfuse Connected: {health['langfuse_connected']}")

        # 2. Basic Chat with Tracing
        print("\n2️⃣  Basic Chat Completion (with automatic tracing)")
        chat_response = await client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is Langfuse and why is it useful for LLM applications?"}
            ],
            metadata={
                "test_type": "demo",
                "feature": "basic_chat",
                "timestamp": datetime.now().isoformat()
            }
        )
        print(f"   Response: {chat_response['response'][:200]}...")
        print(f"   Session ID: {chat_response['session_id']}")
        print(f"   Trace ID: {chat_response['trace_id']}")
        print(f"   Tokens Used: {chat_response['usage']['total_tokens']}")

        trace_id = chat_response['trace_id']

        # 3. Submit User Feedback
        print("\n3️⃣  Submitting User Feedback")
        feedback_response = await client.submit_feedback(
            trace_id=trace_id,
            score=0.85,
            comment="Great explanation, very clear!",
            name="user-satisfaction"
        )
        print(f"   {feedback_response['message']}")
        print(f"   Score: {feedback_response['score']}")

        # 4. Use Prompt Templates
        print("\n4️⃣  Using Prompt Templates")
        prompt_response = await client.use_prompt(
            prompt_name="summarize",
            variables={
                "text": "Langfuse is an open-source observability platform specifically designed for Large Language Model (LLM) applications. It provides comprehensive tracking, monitoring, and analytics capabilities that help developers understand and optimize their AI applications. Key features include automatic tracing of LLM calls, cost tracking, latency monitoring, user feedback collection, prompt management, and detailed analytics dashboards."
            }
        )
        print(f"   Prompt Used: {prompt_response['prompt_name']}")
        print(f"   Summary: {prompt_response['response']}")

        # 5. Multi-turn Conversation (same session)
        print("\n5️⃣  Multi-turn Conversation (tracked in same session)")
        followup_response = await client.chat(
            messages=[
                {"role": "user", "content": "Can you give me 3 key benefits of using Langfuse?"}
            ],
            metadata={
                "test_type": "demo",
                "feature": "multi_turn",
                "turn": 2
            }
        )
        print(f"   Follow-up Response: {followup_response['response'][:200]}...")

        # 6. Auto-Evaluation
        print("\n6️⃣  Auto-Evaluation of Generation")
        eval_response = await client.evaluate_generation(
            trace_id=trace_id,
            evaluation_name="clarity",
            criteria="clarity and understandability"
        )
        print(f"   Evaluation Score: {eval_response['score']}")
        print(f"   Explanation: {eval_response['explanation']}")

        # 7. Custom Event Logging
        print("\n7️⃣  Logging Custom Events")
        event_response = await client.log_event(
            name="demo_completed",
            metadata={
                "client_version": "1.0.0",
                "features_tested": ["chat", "feedback", "prompts", "evaluation", "events"],
                "timestamp": datetime.now().isoformat()
            }
        )
        print(f"   Event Logged: {event_response['name']}")
        print(f"   Event ID: {event_response['event_id']}")

        # 8. Different Prompt Templates
        print("\n8️⃣  Testing Different Prompt Templates")

        # Code review example
        code_review_response = await client.use_prompt(
            prompt_name="code_review",
            variables={
                "code": """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    else:
        return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""
            }
        )
        print(f"   Code Review: {code_review_response['response'][:150]}...")

        # 9. Session Information
        print("\n9️⃣  Session Information")
        session_info = await client.get_session_info()
        print(f"   Session ID: {session_info['session_id']}")
        print(f"   Dashboard URL: {session_info['dashboard_url']}")

        # 10. Multiple Feedback Scores
        print("\n🔟  Multiple Feedback Dimensions")

        # Accuracy score
        await client.submit_feedback(
            trace_id=trace_id,
            score=0.9,
            comment="Factually accurate",
            name="accuracy"
        )
        print("   ✅ Accuracy score submitted")

        # Helpfulness score
        await client.submit_feedback(
            trace_id=trace_id,
            score=0.95,
            comment="Very helpful response",
            name="helpfulness"
        )
        print("   ✅ Helpfulness score submitted")

        # Style score
        await client.submit_feedback(
            trace_id=trace_id,
            score=0.8,
            comment="Good writing style",
            name="style"
        )
        print("   ✅ Style score submitted")

        print("\n" + "=" * 50)
        print("✨ Demo completed successfully!")
        print("\n📊 View your traces and analytics in Langfuse dashboard:")
        print(f"   https://cloud.langfuse.com")
        print("\nKey Features Demonstrated:")
        print("  ✅ Automatic LLM call tracing")
        print("  ✅ Session tracking across multiple interactions")
        print("  ✅ User feedback and scoring")
        print("  ✅ Prompt template management")
        print("  ✅ Auto-evaluation of generations")
        print("  ✅ Custom event logging")
        print("  ✅ Multi-dimensional feedback")
        print("  ✅ Cost and token usage tracking")
        print("  ✅ Metadata and tagging")

    except httpx.ConnectError:
        print("\n❌ Error: Could not connect to server.")
        print("   Please ensure the server is running with: python app.py")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        await client.close()


async def run_stress_test(num_requests: int = 10):
    """Run a simple stress test to generate more data"""
    print(f"\n🏃 Running stress test with {num_requests} requests...")

    client = LangfuseExampleClient()

    questions = [
        "What is machine learning?",
        "Explain quantum computing",
        "How does blockchain work?",
        "What is cloud computing?",
        "Describe artificial intelligence",
        "What are neural networks?",
        "Explain natural language processing",
        "What is computer vision?",
        "How do transformers work in AI?",
        "What is reinforcement learning?"
    ]

    try:
        tasks = []
        for i in range(num_requests):
            question = questions[i % len(questions)]
            task = client.chat(
                messages=[
                    {"role": "user", "content": question}
                ],
                metadata={
                    "test_type": "stress_test",
                    "request_id": i,
                    "batch_size": num_requests
                }
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        print(f"✅ Completed {len(responses)} requests")
        print(f"   Session ID: {client.session_id}")
        print(f"   Total tokens used: {sum(r['usage']['total_tokens'] for r in responses)}")

        # Submit feedback for all responses
        for i, response in enumerate(responses):
            score = 0.5 + (i % 6) * 0.1  # Vary scores between 0.5 and 1.0
            await client.submit_feedback(
                trace_id=response['trace_id'],
                score=score,
                comment=f"Automated test feedback #{i}",
                name="stress_test_score"
            )

        print(f"✅ Submitted feedback for all responses")

    finally:
        await client.close()


if __name__ == "__main__":
    import sys

    async def main():
        if len(sys.argv) > 1 and sys.argv[1] == "stress":
            num_requests = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            await run_stress_test(num_requests)
        else:
            await demonstrate_features()

    asyncio.run(main())