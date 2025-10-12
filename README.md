# Langfuse Example Server

A comprehensive example demonstrating Langfuse integration with LLM APIs (OpenAI) in a FastAPI application. This project showcases all major Langfuse features including tracing, monitoring, scoring, prompt management, and session tracking.

## Features Demonstrated

- 🔍 **Automatic LLM Call Tracing**: Every LLM interaction is automatically traced
- 📊 **Session Tracking**: Track conversations across multiple interactions
- ⭐ **User Feedback & Scoring**: Collect multi-dimensional feedback
- 📝 **Prompt Template Management**: Manage and use prompt templates
- 🤖 **Auto-Evaluation**: LLM-based evaluation of generations
- 📌 **Custom Event Logging**: Log custom events and metadata
- 💰 **Cost & Token Tracking**: Monitor usage and costs
- 🏷️ **Metadata & Tagging**: Rich metadata support for better organization

## Project Structure

```
langfuse-test/
├── app.py              # Main FastAPI server with Langfuse integration
├── config.py           # Configuration management
├── test_client.py      # Example client demonstrating all features
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore          # Git ignore rules
└── README.md           # This file
```

## Setup

### 1. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy `.env.example` to `.env` and add your API keys:

```bash
cp .env.example .env
```

Then edit `.env` with your actual keys:

```env
# Langfuse Configuration
LANGFUSE_SECRET_KEY=your-langfuse-secret-key
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key
LANGFUSE_HOST=https://cloud.langfuse.com

# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=8000
```

**⚠️ Important**: Never commit `.env` file to Git. It's included in `.gitignore`.

## Running the Application

### Start the Server

```bash
# Activate virtual environment if not already activated
source venv/bin/activate

# Run the server
uvicorn app:app --reload --host 0.0.0.0 --port 8000
# Or simply: python app.py
```

The server will start at `http://localhost:8000`

**API Documentation**: `http://localhost:8000/docs`

### Run the Test Client

In a new terminal:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the demo
python test_client.py

# Or run a stress test (generates more data)
python test_client.py stress 20
```

## API Endpoints

### Core Endpoints

- `GET /` - Health check
- `POST /api/v1/chat` - Chat completion with tracing
- `POST /api/v1/feedback` - Submit feedback for a trace
- `POST /api/v1/prompt-completion` - Use prompt templates
- `POST /api/v1/evaluate` - Auto-evaluate generations
- `GET /api/v1/sessions/{session_id}` - Get session info
- `POST /api/v1/event` - Log custom events

### Example API Usage

#### Chat Completion
```python
response = await client.post("/api/v1/chat", json={
    "messages": [
        {"role": "user", "content": "Hello!"}
    ],
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "session_id": "unique-session-id",
    "user_id": "user-123",
    "metadata": {"feature": "chat"}
})
```

#### Submit Feedback
```python
response = await client.post("/api/v1/feedback", json={
    "trace_id": "trace-id-from-chat",
    "score": 0.9,
    "comment": "Great response!",
    "name": "user-satisfaction"
})
```

## Langfuse Features in Detail

### 1. Tracing
Every LLM call is automatically traced with:
- Input/output messages
- Token usage
- Latency metrics
- Model parameters
- User and session IDs

### 2. Session Management
- Track multiple interactions in a session
- Analyze conversation flow
- Understand user journeys

### 3. Scoring System
Multiple scoring dimensions:
- User satisfaction
- Accuracy
- Helpfulness
- Style
- Custom metrics

### 4. Prompt Management
- Template-based prompts
- Variable substitution
- Version control for prompts

### 5. Observability
- Real-time monitoring
- Cost tracking
- Performance metrics
- Error tracking

## Viewing Results in Langfuse

1. Go to [Langfuse Dashboard](https://cloud.langfuse.com)
2. Navigate to your project
3. View:
   - **Traces**: Detailed LLM interactions
   - **Sessions**: Conversation flows
   - **Users**: User analytics
   - **Scores**: Feedback metrics
   - **Analytics**: Usage statistics

## Development Tips

### Adding New Features

1. **New Endpoints**: Add to `app.py` with `@observe()` decorator
2. **Custom Scoring**: Use `langfuse.score()` with custom names
3. **Events**: Log with `langfuse.event()` for custom tracking
4. **Metadata**: Add to any trace for better filtering

### Best Practices

1. **Use Session IDs**: Group related interactions
2. **Add Metadata**: Include context for better analysis
3. **Score Consistently**: Use standard score names
4. **Handle Errors**: Wrap in try-catch with error logging
5. **Flush on Shutdown**: Ensure `langfuse.flush()` is called

## Troubleshooting

### Common Issues

1. **Connection Error**: Ensure server is running
2. **API Key Issues**: Check `.env` file and key validity
3. **Import Errors**: Verify virtual environment is activated
4. **Rate Limits**: Add retry logic for production

### Debug Mode

Set `DEBUG=true` in `.env` for detailed logging

## Resources

- [Langfuse Documentation](https://langfuse.com/docs)
- [Langfuse GitHub](https://github.com/langfuse/langfuse)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com)

## License

This example project is provided for educational purposes.