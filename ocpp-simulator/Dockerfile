# Base image with Python and Node.js
FROM python:3.10-slim as base

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y curl npm && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Move build to static directory
WORKDIR /app
RUN mkdir -p backend/static
RUN cp -r frontend backend/static/

# Copy backend
COPY backend ./app/backend

# Run Flask server (make sure app.py is in backend and launches simulator + serves UI)
CMD ["python", "backend/main.py"]
