<file>
      <absolute_file_name>/app/README.md</absolute_file_name>
      <content"># AI Scrum Master MVP

Intelligent Agile Automation Platform with Jira, Slack, and GitHub integrations.

## Features

- AI-powered sprint summaries and standup automation
- Jira integration with OAuth 2.0
- Webhook processing via Redis Streams
- Sprint insights and analytics
- Real-time collaboration tools

## Tech Stack

- **Backend**: FastAPI + SQLAlchemy + OpenAI
- **Frontend**: Next.js 14 + TailwindCSS
- **Database**: PostgreSQL (SQLite for local dev)
- **Queue**: Redis Streams
- **Deployment**: Docker + docker-compose

## Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <repo-url>
   cd ai-scrum-master
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **Run with Docker**:
   ```bash
   docker-compose up --build
   ```

3. **Access the application**:
   - Backend API: http://localhost:8000/docs
   - Frontend: http://localhost:3000

### Manual Setup

1. **Backend**:
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```

2. **Frontend**:
   ```bash
   cd frontend
   yarn install
   yarn dev
   ```

## API Endpoints

- `GET /healthz` - Health check
- `GET /summarize/standup?accountId=demo` - AI standup summary
- `GET /insights/sprint?boardId=demo&accountId=demo` - Sprint metrics
- `POST /webhook/jira` - Jira webhook handler
- `GET /auth/start` - OAuth flow starter

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `OPENAI_API_KEY` - OpenAI API key for AI features
- `OAUTH_CLIENT_ID` - Jira OAuth client ID
- `OAUTH_CLIENT_SECRET` - Jira OAuth client secret
- `WEBHOOK_SHARED_SECRET` - Webhook validation secret

## Development

- Backend runs on http://localhost:8000
- Frontend runs on http://localhost:3000
- OpenAPI docs at http://localhost:8000/docs

## Deployment

The application is containerized and ready for deployment with Docker Compose or Kubernetes.

## License

MIT License
</content>
    </file>