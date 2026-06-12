# LogCenter: Real-Time Log Aggregation & Anomaly Detection

LogCenter is a distributed, high-throughput logging pipeline designed to ingest, monitor, and analyze server logs in real-time. Built with a robust full-stack architecture, it features automated anomaly detection using background workers and provides a beautiful "Command Center" dashboard with live visualizations.

## 🚀 Key Features

- **High-Throughput Ingestion Engine**: A REST API built with Django and PostgreSQL to securely ingest thousands of server logs via secure, UUID-based endpoint authentication.
- **Asynchronous Anomaly Detection**: Utilizes Celery and Redis as a background worker queue to constantly analyze streaming data, establishing error-rate baselines and flagging statistical anomalies without blocking the main web server.
- **Automated Incident Response**: Integrated live-trigger notification system that automatically dispatches emergency Email alerts to engineering teams the exact moment a critical failure or traffic spike is detected in production.
- **Real-Time Data Visualization**: Built a responsive "Command Center" UI featuring live, auto-updating Chart.js area graphs powered by a custom JavaScript polling engine and optimized PostgreSQL time-series aggregations.

## 🛠️ Tech Stack

- **Backend:** Python, Django, REST API
- **Database:** PostgreSQL (NeonDB), optimized for time-series data
- **Async Workers & Broker:** Celery, Redis
- **Frontend:** HTML5, TailwindCSS, JavaScript, Chart.js

## 💻 Getting Started

### Clone & Setup

```bash
git clone https://github.com/daya-2619/SAAS-Foundations .
cd SAAS-Foundations
```

### Create Virtual Environment
*Windows*
```bash
python -m venv venv
.\venv\Scripts\activate
```
*macOS/Linux*
```bash
python3 -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.sample` to `.env` and fill in the values:
- `DJANGO_SECRET_KEY`
- `DATABASE_URL` (PostgreSQL connection string)
- `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` (For anomaly email alerts)
- `CELERY_BROKER_URL="redis://localhost:6379/0"`

### Run Migrations & Start Server
```bash
cd src
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Start Background Workers (Celery)
In a separate terminal, start the Celery worker and beat scheduler for Anomaly Detection:
```bash
celery -A cfehome worker --pool=solo -l info
celery -A cfehome beat -l info
```
