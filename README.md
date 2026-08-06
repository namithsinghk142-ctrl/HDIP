# HDIP
Hospital Decision Intelligence Platform that combines operational analytics, predictive machine learning models, and interactive dashboards to help healthcare administrators make informed decisions.

-----

# 🏥 Hospital Decision Intelligence Platform (HDIP)

## Overview

HDIP is a web-based platform developed to help hospital administrators monitor hospital operations, analyze healthcare data, forecast patient demand, and support operational decision-making using predictive analytics, explainable machine learning, and interactive dashboards.

The platform combines operational analytics, predictive intelligence, scenario simulation, and decision support into a single application for resource planning and healthcare management.

---

## Features

### Authentication & Security
- JWT Authentication
- Role-Based Access Control (RBAC)
- Secure Password Hashing

### Operational Analytics
- Staffing Analytics
- Financial Analytics
- Emergency Department Flow Analytics
- Quality & Clinical Safety Monitoring

### Predictive Intelligence
- Patient Demand Forecasting
- Bed Occupancy Prediction
- Emergency Department Wait Time Prediction
- Readmission Risk Prediction

### Decision Intelligence
- Executive Decision Center
- Recommendation Engine
- Scenario Simulator
- Decision Audit Trail
- Decision Outcome Feedback

### Data Management
- Dataset Upload
- Data Profiling
- Data Health Monitoring

### Explainable AI
- SHAP Feature Importance
- Model Registry
- Model Monitoring
- Prediction Confidence Scoring

---

## Technology Stack

### Frontend
- React
- TypeScript
- Vite
- Ant Design
- Apache ECharts

### Backend
- FastAPI
- Python
- SQLAlchemy
- Pydantic

### Machine Learning
- XGBoost
- Scikit-learn
- Prophet
- SHAP
- Pandas
- NumPy

### Database
- SQLite (Development)

### DevOps
- Docker
- Docker Compose
- Nginx
- GitHub Actions

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/namithsinghk142-ctrl/HDIP.git
cd HDIP
```

### Backend

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

Backend runs on:

```text
http://localhost:8000
```

### Frontend

```bash
cd frontend

npm install

npm run dev
```

Frontend runs on:

```text
http://localhost:5173
```

---

## Default Login

```text
Email: admin@hospital.org
Password: admin123
```

---

## License

This project is intended for educational and portfolio purposes.
