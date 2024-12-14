# Skyview

A real-time analytics platform for the Bluesky social network, built with Django and Celery.

## Overview

1. **Ingestion Layer:**  
   Connects to the Bluesky Firehose using the `atproto==0.3.0` SDK and `websockets==11.0.3` to receive and decode real-time events.
   
2. **Storage:**  
   Events are stored in a PostgreSQL database, enhanced by TimescaleDB for efficient time-series queries.

3. **Processing & Analytics:**  
   Celery tasks run in the background to process raw events, extract hashtags, compute rolling trends, and prepare data for the frontend.

4. **API & Visualization:**  
   A Django-based API returns JSON responses with trending hashtags and activity metrics. The frontend uses D3.js to render dynamic charts and maps.

## Prerequisites

- Python 3.11.1
- PostgreSQL 15.x
- TimescaleDB (latest stable)
- Redis (for Celery and Channels)
- Node.js (optional, if you prefer a Node-based frontend toolchain)
- Git (to clone this repository)

## Local Development Setup

1. **Clone the Repository:**   ```bash
   git clone https://github.com/your-username/skyview.git
   cd skyview   ```

2. **Create and Activate Virtual Environment:**   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate   ```

3. **Install Dependencies:**   ```bash
   pip install -r requirements.txt   ```

4. **Environment Variables:**
   Create a `.env` file in the project root:   ```
   DJANGO_SETTINGS_MODULE=skyview.settings
   DATABASE_URL=postgres://user:password@localhost:5432/skyview
   REDIS_URL=redis://localhost:6379/0   ```

5. **Database Setup:**   ```bash
   python manage.py migrate   ```

6. **Start Services:**   ```bash
   # Start Celery worker and beat
   ./manage_celery.sh start

   # Start Django development server
   python manage.py runserver   ```

## Project Structure

```
skyview/
├── ingestion/          # Bluesky Firehose ingestion
├── analytics/          # Data processing and trend computation
├── api/               # REST API endpoints
├── frontend/          # Web interface (if applicable)
├── skyview/           # Project settings
└── manage.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License - see [LICENSE](LICENSE) for details