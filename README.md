# 🏠 Open House Matchmaker

> AI-powered real estate agent matching system for optimizing open house performance and fair opportunity distribution.

## 🎯 Overview

The Open House Matchmaker is an intelligent system that automatically recommends the best real estate agents to host open houses based on:

- **Past Performance**: Conversion rates, lead quality, and feedback scores
- **Area Expertise**: Location familiarity from past deals and local knowledge
- **Buyer Pool Alignment**: Historical buyer demographics and price ranges
- **Fair Rotation**: Ensures newer agents get opportunities while preventing top agent overload
- **Smart Scheduling**: Calendar integration and availability checking

## ✨ Key Features

### 🤖 AI Agent Scoring Engine
- **XGBoost ML Model** for agent performance prediction
- **Multi-factor scoring** based on 12+ performance indicators
- **Explainable recommendations** with detailed reasoning
- **Cold-start handling** for new agents using rule-based scoring

### ⚖️ Fairness & Rotation System
- **Experience-tier based** opportunity distribution
- **Minimum/maximum** monthly hosting quotas
- **Diversity enforcement** in top recommendations
- **Anti-bias measures** to prevent system gaming

### 📅 Smart Scheduling
- **Google Calendar/Outlook** integration
- **Automated availability** checking
- **Calendar invite** generation
- **Conflict detection** and resolution

### 📊 Performance Tracking
- **Real-time dashboard** with key metrics
- **Weekly summary reports** via email
- **Feedback collection** system
- **ML model performance** monitoring

### 📧 Automated Notifications
- **Agent recommendations** to listing agents
- **Selection confirmations** to chosen hosts
- **Weekly team summaries** with insights
- **Feedback requests** post-event

## 🏗️ Architecture

### Backend (FastAPI + Python)
```
backend/
├── app/
│   ├── api/           # REST API endpoints
│   ├── ml/            # Machine learning models
│   ├── services/      # Business logic & fairness
│   ├── integrations/  # Calendar, email, MLS
│   ├── models/        # Database & Pydantic models
│   └── database/      # Database connection
├── tests/             # Unit & integration tests
└── main.py           # FastAPI application
```

### Frontend (React + Material-UI)
```
frontend/
├── src/
│   ├── components/    # Reusable UI components
│   ├── pages/         # Main application pages
│   ├── services/      # API client & utilities
│   └── utils/         # Helper functions
└── public/           # Static assets
```

### Key Technologies
- **Backend**: FastAPI, SQLAlchemy, XGBoost, scikit-learn
- **Frontend**: React, Material-UI, React Query, Recharts
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ML/AI**: XGBoost, pandas, numpy
- **Integrations**: Google Calendar API, SMTP email

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # Configure your settings
python setup_sample_data.py  # Load sample data
python main.py  # Start FastAPI server (port 8000)
```

### Frontend Setup
```bash
cd frontend
npm install
npm start  # Start React dev server (port 3000)
```

### Access the Application
- **Frontend Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

## 📚 API Documentation

### Core Endpoints

#### Agents
- `GET /api/v1/agents` - List all agents with filters
- `POST /api/v1/agents` - Create new agent
- `GET /api/v1/agents/{id}/fairness-score` - Get fairness metrics
- `GET /api/v1/agents/{id}/performance` - Get performance history

#### Open Houses
- `GET /api/v1/open-houses` - List open houses
- `POST /api/v1/open-houses` - Schedule new open house
- `POST /api/v1/open-houses/{id}/generate-recommendations` - Get AI recommendations
- `PUT /api/v1/open-houses/{id}` - Assign agent or update details

#### Dashboard
- `GET /api/v1/dashboard/stats` - Key performance metrics
- `GET /api/v1/dashboard/weekly-summary` - Weekly report data
- `POST /api/v1/dashboard/retrain-model` - Trigger ML model retraining
- `GET /api/v1/dashboard/fairness-report` - System fairness analysis

## 🤖 AI Model Details

### Agent Scoring Features
The ML model evaluates agents using these key features:

1. **Performance Metrics**
   - Historical conversion rate (leads/attendees)
   - Success rate (offers/leads)
   - Average feedback scores
   - Recent activity levels

2. **Match Quality**
   - Area familiarity (zip code overlap)
   - Price range alignment with buyer history
   - Property type experience

3. **Fairness Factors**
   - Recent hosting frequency
   - Experience tier (junior/mid/senior)
   - Opportunity distribution balance

### Model Training
- **Algorithm**: XGBoost Regression
- **Training Data**: Historical open house outcomes
- **Target Variable**: Success score (0-1) based on attendees, leads, offers
- **Retraining**: Automated weekly with new performance data
- **Cold Start**: Rule-based scoring for new agents

### Fairness Algorithm
```python
# Experience-based opportunity quotas
min_monthly_opportunities = {
    "junior": 2,    # < 2 years experience
    "mid": 3,       # 2-5 years experience  
    "senior": 4     # 5+ years experience
}

# Fairness score calculation
fairness_score = base_score + 
                 opportunity_deficit_bonus + 
                 time_since_last_bonus - 
                 overloading_penalty
```

## 📊 Dashboard Features

### Key Metrics
- **Active Agents**: Currently available agents
- **Upcoming Open Houses**: Next 7 days schedule
- **Conversion Rate**: System-wide performance average
- **Completion Rate**: Successfully hosted events

### Performance Analytics
- **Top Performers**: Best agents by lead generation
- **Fairness Report**: Opportunity distribution analysis
- **Model Performance**: AI accuracy and confidence metrics
- **Unassigned Houses**: Events needing agent assignment

### Automated Reporting
- **Weekly Summaries**: Email reports to management
- **Agent Notifications**: Selection confirmations
- **Feedback Requests**: Post-event performance collection

## 🔧 Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=sqlite:///./open_house_matchmaker.db

# Email Service
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=noreply@openhouse.com
SENDER_PASSWORD=your_app_password

# Google Calendar (Optional)
GOOGLE_CREDENTIALS_FILE=app/integrations/credentials.json
```

### Feature Toggles
- **ML_MODEL_ENABLED**: Use AI scoring vs rule-based
- **CALENDAR_INTEGRATION**: Enable Google Calendar sync
- **EMAIL_NOTIFICATIONS**: Send automated emails
- **FAIRNESS_ENFORCEMENT**: Apply rotation constraints

## 🧪 Sample Data

The system includes realistic sample data:
- **8 Sample Agents** with varying experience levels
- **8 Sample Listings** across different LA areas
- **Performance History** for last 6 months
- **Scheduled Open Houses** for next few weeks

Run `python backend/setup_sample_data.py` to populate the database.

## 🔮 Roadmap

### Phase 1: Core System ✅
- [x] AI agent scoring engine
- [x] Fairness and rotation logic
- [x] Basic dashboard and UI
- [x] Email notifications

### Phase 2: Enhanced Features 🚧
- [ ] Google Calendar integration
- [ ] Mobile-responsive design
- [ ] Advanced analytics dashboard
- [ ] MLS data integration

### Phase 3: Scale & Optimize 📋
- [ ] Multi-brokerage support
- [ ] Advanced ML models (deep learning)
- [ ] Real-time chat notifications
- [ ] Mobile app (React Native)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow Python PEP 8 for backend code
- Use ESLint/Prettier for frontend code
- Write unit tests for new features
- Update documentation for API changes

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions, issues, or feature requests:
- **GitHub Issues**: [Create an issue](https://github.com/your-org/open-house-matchmaker/issues)
- **Email**: support@openhousematchmaker.com
- **Documentation**: [Full API Docs](https://docs.openhousematchmaker.com)

---

**Built with ❤️ for the real estate community**

*Empowering agents with AI-driven insights for better open house outcomes and fair opportunity distribution.*
