# CI/CD Pipeline Health Dashboard

A simplified, real-time dashboard for monitoring CI/CD pipelines with email notifications for failed builds. Built with Node.js, React, and SQLite for maximum simplicity and ease of deployment.

## 🚀 Features

- **Real-time Pipeline Monitoring**: Track success/failure rates across multiple CI/CD tools
- **GitHub Actions Integration**: Manual workflow triggers with success/fail options
- **Email Notifications**: Automatic failure alerts via SMTP (Gmail support)
- **Webhook Support**: Generic endpoint for any CI/CD tool integration
- **Responsive Dashboard**: Clean, mobile-friendly interface with auto-refresh
- **Simple Setup**: Single command deployment with Docker Compose

## 🏗️ Architecture Summary

```
Frontend (React) ←→ Backend (Node.js/Express) ←→ SQLite Database
       ↓                    ↓                        ↓
   Nginx Proxy         Email Service           Data Files
       ↓                    ↓
   Static Files        SMTP Server
```

### **Technology Stack**
- **Backend**: Node.js 18+, Express.js, TypeScript, SQLite
- **Frontend**: React 18, TypeScript, Vite, CSS Grid/Flexbox
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Email**: Nodemailer with SMTP integration
- **CI/CD**: GitHub Actions with manual workflow triggers

## 📋 Prerequisites

- Node.js 18+ and npm
- Docker and Docker Compose
- Git
- Gmail account (for email notifications)

## 🚀 Quick Start

### Option 1: Docker (Recommended)
```bash
# Clone and start everything
git clone <your-repo>
cd <application-directory>
docker-compose up -d

# Open http://localhost:3001
```

### Option 2: Development Mode
```bash
# Backend
npm install
npm run dev

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Open http://localhost:3001
```

## ⚙️ Configuration

### 1. Environment Setup
```bash
# .env file for environment template

# Edit .env with your settings
```

### 2. Email Configuration (Gmail)
1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password**:
   - Google Account → Security → 2-Step Verification → App passwords
   - Generate password for "Mail"
3. **Update `.env`**:
   ```env
   SMTP_USER=your_email@gmail.com
   SMTP_PASS=your_16_char_app_password
   NOTIFICATION_EMAIL=recipient@example.com
   ```

### 3. Test Email Configuration
```bash
curl -X POST http://localhost:3000/api/test-email \
  -H "Content-Type: application/json" \
  -d '{"to": "your_email@gmail.com"}'
```

## 🧪 Testing with GitHub Actions

### 1. Create Test Pipeline
```bash
curl -X POST http://localhost:3001/api/pipelines \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub Actions Test",
    "type": "github"
  }'
```

### 2. Trigger GitHub Actions Workflow
1. Go to your GitHub repository → Actions
2. Click "Test CI/CD Dashboard Pipeline"
3. Choose inputs:
   - **Test Type**: `fail` (to test email notifications)
   - **Pipeline Name**: `GitHub Actions Test`
4. Click "Run workflow"

### 3. Monitor Results
- **Dashboard**: Watch real-time updates at `http://localhost:3001`
- **Email**: Check inbox for failure notifications
- **API**: Verify webhook data with `curl http://localhost:3001/api/builds`

## 🔧 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/pipelines` | List all pipelines |
| `POST` | `/api/pipelines` | Create new pipeline |
| `GET` | `/api/builds` | List all builds |
| `POST` | `/api/webhooks` | CI/CD webhook endpoint |
| `GET` | `/api/metrics` | Dashboard metrics |


## 🤖 AI Tools Usage

This project was developed with extensive use of AI tools to accelerate development and ensure best practices.

### **Development Process with AI**

#### **1. Initial Project Setup**
**Prompt Example:**
```
"You are a Senior DevOps engineer. Build a CI/CD Pipeline Health Dashboard with:
- Real-time monitoring of pipeline success/failure rates
- Email notifications for failed builds
- Simple UI to display metrics and logs
- Docker containerization
- GitHub Actions integration"
```

**AI Contribution:**
- Generated complete project structure
- Set up Docker and Docker Compose files
- Designed database schema

#### **2. Backend Development**
**Prompt Example:**
```
"Create a simple Express.js server with:
- Postgre database integration
- RESTful API endpoints for pipelines and builds
- Webhook processing for CI/CD tools"
```

**AI Contribution:**
- Implemented Express.js server with TypeScript
- Created SQLite database wrapper
- Built email service with HTML templates
- Designed API endpoints with proper error handling

#### **3. Frontend Development**
**Prompt Example:**
```
"Build a React dashboard that:
- Displays pipeline metrics in real-time
- Shows recent builds with status indicators
- Auto-refreshes every 30 seconds
- Uses responsive design with CSS Grid"
```

**AI Contribution:**
- Created React components with TypeScript
- Implemented responsive CSS layouts
- Added real-time data fetching
- Designed status indicators and color coding

#### **4. GitHub Actions Integration**
**Prompt Example:**
```
"Create a GitHub Actions workflow that:
- Can be triggered manually with success/fail options
- Sends webhooks to our dashboard
- Simulates real pipeline work with delays
- Integrates with our webhook endpoint"
```

**AI Contribution:**
- Designed workflow with manual triggers
- Implemented webhook integration
- Added pipeline simulation logic
- Created proper error handling

#### **5. Problem Solving**
**Prompt Example:**
```
- Fix frontend and backend issues
- Environment variables not loading properly
- Email configuration validation issues"
```

**AI Contribution:**
- Fixed method name from `createTransporter` to `createTransport`
- Added proper environment variable loading
- Implemented configuration validation
- Created diagnostic endpoints for debugging

### **Key AI Learning Patterns**

1. **Iterative Development**: AI helped refine code through multiple iterations
2. **Error Resolution**: Quick identification and fixing of compilation issues
3. **Best Practices**: AI suggested TypeScript patterns and security considerations
4. **Documentation**: Generated comprehensive API documentation and setup guides

## 📚 Key Learnings

### **Technical Insights**

1. **Simplicity Over Complexity**
   - No need for complex authentication initially
   - Simple file-based configuration works well

2. **TypeScript Benefits**
   - Caught many errors during development
   - Better IDE support and autocomplete

3. **Docker Simplification**
   - Single `docker-compose up` command for full stack
   - Consistent environment across development and production
   - Easy to share and deploy

4. **Email Integration Challenges**
   - Gmail requires app passwords (not regular passwords)
   - SMTP configuration needs proper error handling
   - HTML email templates improve user experience

### **Development Process Learnings**

1. **AI-Assisted Development**
   - AI tools significantly accelerated initial setup
   - Great for boilerplate code and standard patterns
   - Human oversight still needed for business logic

2. **Iterative Refinement**
   - Started with complex features, simplified based on needs
   - Removed unnecessary dependencies (Redux, Material-UI)
   - Focused on core functionality first

3. **Testing Strategy**
   - Manual testing with curl commands proved effective
   - GitHub Actions provided real-world testing scenarios
   - Email testing required careful configuration

### **Architecture Decisions**

1. **Database Choice**: PostgreSQL for simplicity
2. **Frontend Framework**: React with hooks over complex state management
3. **Styling**: CSS Grid/Flexbox over component libraries
4. **Containerization**: Docker Compose for easy deployment
5. **Email Service**: Nodemailer with SMTP over third-party services

## 🔍 Troubleshooting

### **Common Issues**

1. **Email Not Working**
 ```bash
   # Verify Gmail app password is correct
   # Check spam folder for test emails
   ```
2. **Frontend Not Loading**
   ```bash
   # Check if backend is running
   curl http://localhost:3000/api/health
   
   # Verify frontend is built
   ls frontend/dist/
   ```

### **Debugging Commands**
```bash
# Check all services
docker-compose ps

# View logs
docker-compose logs -f

# Test API endpoints
curl http://localhost:3001/api/health
curl http://localhost:3001/api/metrics
curl http://localhost:3001/api/pipelines
```

## 🚀 Deployment

### **Production Deployment**
```bash
# Build production images
docker-compose up -d

# Set environment variables
export SMTP_USER=your_email@gmail.com
export SMTP_PASS=your_app_password
export NOTIFICATION_EMAIL=alerts@company.com
```

### **Environment Variables**
```env
# Required
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
NOTIFICATION_EMAIL=recipient@example.com
```
