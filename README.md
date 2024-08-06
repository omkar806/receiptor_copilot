# Gmail Receipt Data Retriever API

## Overview

This FastAPI-powered API efficiently retrieves Gmail receipt/order data, utilizing WebSockets for optimized data transfer. The system is designed with API rate limiting and is deployed on Google Cloud Platform (GCP) Cloud Run, with PostgreSQL on Supabase for data persistence.

## Features

- **FastAPI Backend**: Leverages the high-performance FastAPI framework for building APIs with Python 3.7+.
- **Gmail Integration**: Retrieves receipt and order data from Gmail accounts.
- **WebSocket Support**: Utilizes WebSockets for real-time, efficient data transfer.
- **API Rate Limiting**: Implements rate limiting using Tenacity to prevent abuse and ensure fair usage.
- **Cloud Deployment**: Hosted on GCP Cloud Run for scalable, serverless deployment.
- **Database**: Uses PostgreSQL on Supabase for robust data storage and management.

## Technical Stack

- **Backend Framework**: FastAPI
- **Language**: Python 3.7+
- **WebSocket Library**: FastAPI's built-in WebSocket support
- **Rate Limiting**: Tenacity
- **Cloud Platform**: Google Cloud Platform (GCP) Cloud Run
- **Database**: PostgreSQL on Supabase
   
