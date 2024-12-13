# SkyView

SkyView is a public-facing web application that ingests, analyzes, and visualizes real-time trends from the Bluesky Firehose API. It focuses on delivering keyword and hashtag trend analysis and interactive visualizations without requiring user authentication.

## Features

- **Real-Time Event Ingestion:** Streams posts, likes, follows, and other events from the Bluesky Firehose.
- **Trend Analysis:** Identifies trending hashtags, keywords, and activity spikes over rolling time windows.
- **Interactive Visualizations:** Uses D3.js for geo-maps, bar charts, and line graphs to display real-time data trends.
- **Public API Endpoints:** Exposes aggregated trend data through a public API for third-party integrations.

## Tech Stack

- **Backend:** Python 3.11, Django 4.2.4, Channels 4.0.0
- **Database:** PostgreSQL 15 + TimescaleDB extension for time-series optimization
- **Asynchronous Processing:** Celery 5.3.1 + Redis 4.6.0 for background tasks
- **Data Visualization:** D3.js 7.8.5
- **Data Analysis:** numpy 1.25.1, pandas 2.0.3

## Architecture

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

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/your-username/skyview.git
   cd skyview
