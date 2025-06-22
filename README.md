# Pulse Activity Tracker

**Intelligent work-life balance automation system that tracks desktop activity, generates smart todos, and manages productivity reporting.**

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

**Creates an intelligent productivity dashboard that learns your work patterns and automatically manages your todo lists.**

## What It Does

### Smart Activity Monitoring
- **Desktop Tracking** - Monitors applications, websites, file usage, and work patterns
- **Time Analysis** - Learns when you're most productive and suggests optimal scheduling
- **Perfect for:** Remote workers who need intelligent productivity management

### Intelligent Todo Generation
- **Pattern Learning** - Analyzes your work habits to suggest relevant tasks
- **Auto-completion** - Detects completed work and checks off corresponding todos
- **Best for:** Maintaining productivity without manual task management overhead

### Work-Life Balance Automation
- **Smart Compensation** - Automatically adjusts work schedules for life interruptions
- **Boss Reporting** - Generates professional productivity summaries
- **Seamless Integration** - Balances personal time with work accountability

## Features

### Activity Intelligence
- **Real-time Monitoring** - Tracks all computer activity with privacy controls
- **Pattern Recognition** - ML-powered work habit analysis and prediction
- **Context Awareness** - Understands project continuity and task relationships

### Todo Management
- **Auto-generation** - Creates tomorrow's tasks based on today's work patterns
- **Smart Suggestions** - Recommends tasks based on calendar, deadlines, and energy levels
- **Manual Override** - Full control to add, edit, or remove any suggested items

### Reporting & Communication
- **Professional Summaries** - Automated reports highlighting key accomplishments
- **Time Accountability** - Tracks productive hours with intelligent categorization
- **Privacy Controls** - You control what information gets shared externally

## Development Roadmap

### Phase 1: Core Desktop Monitoring (Weeks 1-2)
- Basic activity tracking (applications, websites, files)
- Simple todo list with manual entry
- Local SQLite database setup
- Basic web dashboard

### Phase 2: Intelligence Layer (Weeks 3-4)
- Pattern recognition for work habits
- Smart todo generation based on activity
- Basic auto-completion detection
- Simple reporting system

### Phase 3: Advanced Features (Weeks 5-6)
- Mobile app with sync capabilities
- Advanced ML for better predictions
- Integration with calendars and external tools
- Professional reporting dashboard

### Phase 4: Polish & Deploy (Weeks 7-8)
- Performance optimization
- Security hardening
- API documentation
- Deployment automation

## Architecture

### Backend (Python)
```
pulse/
├── core/
│   ├── activity_monitor.py    # Desktop activity tracking
│   ├── pattern_analyzer.py    # ML pattern recognition
│   ├── todo_generator.py      # Intelligent task creation
│   └── report_builder.py      # Professional summaries
├── api/
│   ├── server.py              # FastAPI web server
│   ├── routes/                # API endpoints
│   └── models/                # Data models
├── database/
│   ├── models.py              # SQLAlchemy models
│   └── migrations/            # Database changes
└── utils/
    ├── config.py              # Configuration management
    └── helpers.py             # Utility functions
```

### Frontend (React)
```
web/
├── src/
│   ├── components/            # React components
│   ├── pages/                 # Page components
│   ├── hooks/                 # Custom React hooks
│   └── services/              # API communication
└── public/                    # Static assets
```

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, psutil
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: React, TypeScript, Tailwind CSS
- **ML/AI**: scikit-learn, pandas, OpenAI API (optional)
- **Mobile**: React Native (future)
- **Deployment**: Docker, cloud hosting

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Node.js 18+ (for frontend development)
- Git

### Installation
```bash
# Clone the repository
git clone [repo-url]
cd pulse-activity-tracker

# Install Python dependencies
pip install -r requirements.txt

# Install frontend dependencies (optional for development)
cd web && npm install
```

### First Run
```bash
# Start the activity monitor
python main.py

# Access web dashboard (if frontend is set up)
# http://localhost:3000
```

## Privacy & Security

- **Local-first**: All data stored locally by default
- **Granular Controls**: Choose exactly what to track and share
- **Encryption**: Sensitive data encrypted at rest
- **Open Source**: Full transparency in data handling

## Integration Capabilities

- **Calendar Sync**: Google Calendar, Outlook integration
- **Communication**: Slack, Teams, Email reporting
- **Project Management**: Jira, Asana, Linear integration
- **Mobile Sync**: Cross-platform todo synchronization

## Time Savings

- **Manual time tracking** - 15-30 minutes daily
- **With Pulse** - 0-2 minutes daily (just review suggestions)
- **Key benefits** - Eliminates productivity guilt, optimizes work patterns, maintains professional accountability

## Perfect Integration

**Works perfectly with existing tools:**
1. **Calendar Apps** - Syncs with your existing schedule management
2. **Project Management** - Enhances rather than replaces current tools  
3. **Communication** - Integrates with Slack, Teams, email workflows

**Complete intelligent productivity automation that learns how you work best and handles the administrative overhead of remote work accountability.**
