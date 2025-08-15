# 🤖 AI Scrum Master MVP

An intelligent Agile automation platform that integrates with Jira, Slack, and GitHub to streamline your development workflow using GPT-4 powered insights.

## 🎯 Features

- **🔐 Secure Jira OAuth Integration**: Complete OAuth 2.0 PKCE flow with persistent sessions
- **📋 AI-Powered Summaries**: Daily standups, blocker analysis, and sprint retrospectives
- **📊 Real-time Insights**: Sprint metrics, burndown charts, and team performance analytics
- **🤖 Intelligent Automation**: GPT-4 powered analysis of your Jira data
- **🔄 Multi-Platform Integration**: Jira, Slack, and GitHub support
- **🛡️ Production Ready**: Built with FastAPI, Next.js, SQLite/PostgreSQL, and Redis

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose (optional)

### 1. Clone & Setup

```bash
git clone <your-repo-url>
cd ai-scrum-master-demo
cp .env.example backend/.env
cp .env.example frontend/.env.local
```

### 2. Configure Jira OAuth

1. Go to [Atlassian Developer Console](https://developer.atlassian.com/console/myapps/)
2. Create a new OAuth 2.0 (3LO) app
3. Set redirect URI to: `http://localhost:8000/auth/callback`
4. Copy your credentials to `backend/.env`:

```env
OAUTH_CLIENT_ID=your-atlassian-client-id
OAUTH_CLIENT_SECRET=your-atlassian-client-secret
REDIRECT_URI=http://localhost:8000/auth/callback
```

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Frontend Setup

```bash
cd ../frontend
yarn install

# Update .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start frontend
yarn dev
```

### 5. Test the Integration

1. Open http://localhost:3000
2. Click "Connect to Jira"
3. Complete OAuth flow
4. Test "Get Jira Projects" and "Get Jira Boards"

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Integrations  │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│      (Jira)     │
│   Port: 3000    │    │   Port: 8000    │    │   (Slack/GitHub)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │               ┌─────────────────┐            │
         └──────────────►│   Database      │◄───────────┘
                         │ (SQLite/Postgres)│
                         └─────────────────┘
```

## 🔧 API Endpoints

### Authentication
- `GET /auth/jira/login` - Start OAuth flow (redirects to Atlassian)
- `GET /auth/callback` - OAuth callback handler
- `GET /auth/connection` - Check authentication status
- `POST /auth/logout` - Logout and clear session

### Jira Integration
- `GET /auth/jira/projects` - Fetch user's Jira projects
- `GET /auth/jira/boards` - Fetch user's Jira boards

### AI Features
- `POST /summarize/standup` - Generate AI standup summary
- `POST /summarize/blockers` - Analyze blockers
- `POST /summarize/retrospective` - Sprint retrospective insights

### System
- `GET /healthz` - Health check
- `GET /metrics` - Prometheus metrics
- `GET /version` - API version info

## 🔒 OAuth Flow Details

The application implements OAuth 2.0 with PKCE (Proof Key for Code Exchange) for secure authentication:

1. **Initiate**: `GET /auth/jira/login` generates PKCE parameters and redirects to Atlassian
2. **Authorize**: User grants permissions on Atlassian's consent page
3. **Callback**: Atlassian redirects to `/auth/callback` with authorization code
4. **Exchange**: Backend exchanges code for access/refresh tokens
5. **Persist**: User identity and tokens stored in database with secure cookie
6. **Access**: Subsequent API calls use stored tokens with automatic refresh

### OAuth URL Structure
```
https://auth.atlassian.com/authorize?
  audience=api.atlassian.com&
  client_id=YOUR_CLIENT_ID&
  scope=read:jira-user read:jira-work write:jira-work offline_access&
  redirect_uri=http://localhost:8000/auth/callback&
  state=RANDOM_STATE&
  response_type=code&
  prompt=consent&
  code_challenge=PKCE_CHALLENGE&
  code_challenge_method=S256
```

## 🛠️ Development

### Backend Testing

```bash
# Test health endpoint
curl http://localhost:8000/healthz

# Test OAuth URL generation
curl http://localhost:8000/auth/jira/login?redirect=false

# Test connection status
curl -b cookies.txt http://localhost:8000/auth/connection
```

### Environment Variables

#### Backend (.env)
```env
# Required
OAUTH_CLIENT_ID=your-atlassian-client-id
OAUTH_CLIENT_SECRET=your-atlassian-client-secret
REDIRECT_URI=http://localhost:8000/auth/callback

# Optional
OPENAI_API_KEY=sk-your-openai-key
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-api-token
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📦 Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Services will be available at:
# Frontend: http://localhost:3000
# Backend: http://localhost:8000
```

## 🔍 Troubleshooting

### Common Issues

1. **"Incorrect request parameters" on Atlassian**
   - Verify redirect URI matches exactly: `http://localhost:8000/auth/callback`
   - Check OAuth app configuration in Atlassian Developer Console

2. **"Failed to fetch" errors**
   - Ensure backend is running on port 8000
   - Check CORS configuration
   - Verify NEXT_PUBLIC_API_URL in frontend

3. **Database connection issues**
   - Ensure `/data` directory is writable for SQLite
   - Check DATABASE_URL format for PostgreSQL

### Logging

```bash
# Backend logs
tail -f backend/logs/app.log

# Check backend health
curl http://localhost:8000/healthz
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📝 License

MIT License - see LICENSE file for details

## 🔗 Resources

- [Atlassian OAuth 2.0 Guide](https://developer.atlassian.com/cloud/jira/platform/oauth-2-3lo-apps/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

---

Built with ❤️ for better Agile workflows