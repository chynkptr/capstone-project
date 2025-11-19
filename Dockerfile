# Base image with Python 3.11 (TensorFlow 2.15.0 compatible)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (PostgreSQL client library for psycopg2)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /app/.venv

# Activate virtual environment and upgrade pip tools
ENV PATH="/app/.venv/bin:$PATH"
RUN python -m pip install --no-cache-dir --upgrade pip setuptools wheel build

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies in virtual environment
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose Flask port
EXPOSE 8000

# Run the Flask application using venv python
CMD ["/app/.venv/bin/python", "app1.py"]
