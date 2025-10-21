# Base image with Python 3.12
FROM python:3.12-slim

# Install PostgreSQL and required tools
RUN apt-get update && apt-get install -y postgresql postgresql-contrib libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Set environment variables for PostgreSQL
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=admin123
ENV POSTGRES_DB=capstone
ENV POSTGRES_PORT=5432

# Create PostgreSQL data directory
RUN mkdir -p /var/lib/postgresql/data && chown -R postgres:postgres /var/lib/postgresql

# Copy application files
WORKDIR /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose Flask and PostgreSQL ports
EXPOSE 8000 5432

# Initialize PostgreSQL database and run both services
CMD service postgresql start && \
    sudo -u postgres psql -c "ALTER USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';" && \
    sudo -u postgres createdb ${POSTGRES_DB} && \
    python app.py 