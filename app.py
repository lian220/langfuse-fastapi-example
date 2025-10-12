"""
Main FastAPI application with Langfuse integration
Demonstrates various Langfuse features including:
- Tracing and monitoring
- Scoring and feedback
- Prompt management
- Session tracking
- Cost tracking
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import json
from contextlib import asynccontextmanager

from langfuse import Langfuse, observe, get_client
import openai

from config import config


# Initialize Langfuse client
langfuse = Langfuse(
    secret_key=config.LANGFUSE_SECRET_KEY,
    public_key=config.LANGFUSE_PUBLIC_KEY,
    host=config.LANGFUSE_HOST
)

# Initialize OpenAI client
openai_client = openai.OpenAI(api_key=config.OPENAI_API_KEY)


# Pydantic models
class ChatMessage(BaseModel):
    role: str = Field(..., description="Message role (user/assistant/system)")
    content: str = Field(..., description="Message content")


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Chat messages")
    model: str = Field(default="gpt-3.5-turbo", description="Model name")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    max_tokens: Optional[int] = Field(default=500, description="Maximum tokens")
    session_id: Optional[str] = Field(default=None, description="Session ID for tracking")
    user_id: Optional[str] = Field(default=None, description="User ID for tracking")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")


class ChatResponse(BaseModel):
    response: str
    session_id: str
    trace_id: str
    usage: Optional[Dict[str, Any]] = None
    model: str


class FeedbackRequest(BaseModel):
    trace_id: str = Field(..., description="Trace ID to provide feedback for")
    score: float = Field(..., ge=0.0, le=1.0, description="Score between 0 and 1")
    comment: Optional[str] = Field(default=None, description="Optional feedback comment")
    name: str = Field(default="user-feedback", description="Score name")


class PromptRequest(BaseModel):
    prompt_name: str = Field(..., description="Name of the prompt to retrieve")
    variables: Optional[Dict[str, Any]] = Field(default=None, description="Variables for prompt template")
    model: str = Field(default="gpt-3.5-turbo", description="Model to use")
    temperature: float = Field(default=0.7, description="Temperature for generation")
    session_id: Optional[str] = Field(default=None, description="Session ID")
    user_id: Optional[str] = Field(default=None, description="User ID")




# Lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        config.validate()
        print(f"🚀 {config.APP_NAME} started successfully!")
        print(f"📊 Connected to Langfuse: {config.LANGFUSE_HOST}")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise

    yield

    # Shutdown
    langfuse.flush()
    print("👋 Server shutting down...")


# Initialize FastAPI app
app = FastAPI(
    title=config.APP_NAME,
    version=config.API_VERSION,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Helper functions
def prepare_messages(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    """Convert ChatMessage objects to dict format for OpenAI"""
    return [{"role": msg.role, "content": msg.content} for msg in messages]


async def generate_completion(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: Optional[int] = 500
):
    """Generate chat completion"""
    # Make OpenAI API call
    response = openai_client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response




# API Endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": config.APP_NAME,
        "version": config.API_VERSION,
        "langfuse_connected": True
    }


@app.post("/api/v1/chat", response_model=ChatResponse)
async def chat_completion(request: ChatRequest):
    """
    Main chat completion endpoint with full Langfuse tracking
    """
    try:
        # Generate or use existing session ID
        session_id = request.session_id or str(uuid.uuid4())

        # Prepare messages
        messages = prepare_messages(request.messages)

        # Create a new span for this operation using v3 SDK
        with langfuse.start_as_current_span(
            name="chat_completion",
            input={
                "messages": messages,
                "model": request.model,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens
            },
        ) as span:
            # Update trace with metadata
            span.update_trace(
                user_id=request.user_id,
                session_id=session_id,
                tags=["api", "chat"],
                metadata=request.metadata or {}
            )

            # Generate completion
            with langfuse.start_as_current_generation(
                name="openai_completion",
                model=request.model,
                input=messages,
                model_parameters={
                    "temperature": request.temperature,
                    "max_tokens": request.max_tokens
                }
            ) as generation:
                response = await generate_completion(
                    messages=messages,
                    model=request.model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens
                )

                # Update generation with output and usage
                generation.update(
                    output=response.choices[0].message.content,
                    usage_details={
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    }
                )

            # Get trace ID for reference
            trace_id = langfuse.get_current_trace_id()

            # Update span output
            span.update(
                output={
                    "response": response.choices[0].message.content,
                    "model": response.model
                }
            )

            return ChatResponse(
                response=response.choices[0].message.content,
                session_id=session_id,
                trace_id=trace_id if trace_id else str(uuid.uuid4()),
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                model=response.model
            )

    except Exception as e:
        print(f"Error in chat completion: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit feedback/score for a specific trace
    """
    try:
        langfuse.create_score(
            trace_id=request.trace_id,
            name=request.name,
            value=request.score,
            comment=request.comment
        )

        return {
            "status": "success",
            "message": f"Feedback recorded for trace {request.trace_id}",
            "score": request.score,
            "name": request.name
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/prompt-completion")
async def prompt_based_completion(request: PromptRequest):
    """
    Generate completion using a predefined prompt from Langfuse
    """
    try:
        session_id = request.session_id or str(uuid.uuid4())

        # In a real scenario, you would fetch prompts from Langfuse
        # For demo, we'll create a simple template
        prompt_templates = {
            "summarize": "Summarize the following text in a concise manner:\n\n{text}",
            "translate": "Translate the following text to {target_language}:\n\n{text}",
            "explain": "Explain the following concept in simple terms:\n\n{concept}",
            "code_review": "Review the following code and provide suggestions:\n\n{code}"
        }

        if request.prompt_name not in prompt_templates:
            raise HTTPException(status_code=404, detail=f"Prompt '{request.prompt_name}' not found")

        # Format prompt with variables
        prompt_template = prompt_templates[request.prompt_name]
        if request.variables:
            prompt = prompt_template.format(**request.variables)
        else:
            prompt = prompt_template

        # Create span for prompt completion
        with langfuse.start_as_current_span(
            name="prompt_completion",
            input={
                "prompt_name": request.prompt_name,
                "variables": request.variables,
                "prompt": prompt
            }
        ) as span:
            # Update trace
            span.update_trace(
                user_id=request.user_id,
                session_id=session_id
            )

            # Generate completion
            response = openai_client.chat.completions.create(
                model=request.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=request.temperature
            )

            trace_id = langfuse.get_current_trace_id()

            span.update(
                output={"response": response.choices[0].message.content}
            )

            return {
                "response": response.choices[0].message.content,
                "prompt_name": request.prompt_name,
                "session_id": session_id,
                "trace_id": trace_id if trace_id else str(uuid.uuid4()),
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/sessions/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a specific session
    Note: This would typically query Langfuse API for session details
    """
    return {
        "session_id": session_id,
        "message": "Session tracking is active. View details in Langfuse dashboard.",
        "dashboard_url": f"{config.LANGFUSE_HOST}/sessions/{session_id}"
    }


if __name__ == "__main__":
    import uvicorn

    try:
        config.validate()
        uvicorn.run(
            "app:app",
            host=config.SERVER_HOST,
            port=config.SERVER_PORT,
            reload=config.DEBUG
        )
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("Please check your .env file and ensure all required variables are set.")
        exit(1)