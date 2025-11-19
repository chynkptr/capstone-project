# Capstone Flask API - Docker Setup

## Prerequisites

- Docker and Docker Compose installed (Docker Desktop for Windows)
- `model_mole.keras` file in the project directory
- No local PostgreSQL setup required — fully containerized!

## Architecture

This setup runs **2 containers** orchestrated by Docker Compose:

### 1. PostgreSQL Container (`capstone_postgres`)
- **Image**: `postgres:15-alpine`
- **Port**: 5433 on host → 5432 in container
- **Credentials**: `postgres` / `capstone1234`
- **Database**: `capstone` (auto-created)
- **Persistence**: Data stored in Docker volume `postgres_data`

### 2. Flask App Container (`capstone_flask_app`)
- **Port**: 8001 on host → 8000 in container
- **Connects to**: `capstone_postgres:5432` via Docker network
- **Volumes**: `uploads/` and `model_mole.keras` mounted from host

## Configuration

All configuration is managed through the `.env` file. Key settings:

- **Flask Port**: Container runs on 8000, mapped to host port **8001**
- **PostgreSQL**: Containerized PostgreSQL on port **5433** (host), **5432** (container network)
- **Database**: `capstone` database with user `postgres` and password `capstone1234`

## Quick Start

### 1. Ensure Prerequisites

Make sure Docker Desktop is running:
```powershell
# Check Docker status
docker --version
docker-compose --version
```

### 2. Prepare Model File

Ensure `model_mole.keras` exists in the project directory. If not, run:
```powershell
python convert_model.py
```

### 3. Build and Run with Docker Compose

```powershell
# Navigate to project directory
cd "C:\Users\kptry\OneDrive\Documents\Casptone Project\project"

# Build and start both containers (Postgres + Flask)
docker-compose up --build
```

To run in detached mode (background):
```powershell
docker-compose up -d --build
```

**What happens:**
1. Creates Docker network `capstone_network`
2. Starts PostgreSQL container on port 5433
3. Waits for Postgres health check
4. Starts Flask app container on port 8001
5. Flask app auto-creates database tables and admin user

### 4. Access the API

The API will be available at:
- **API**: http://localhost:8001
- **PostgreSQL**: `localhost:5433` (from host machine)
- Health check: **http://localhost:8001/health**

## Connecting to PostgreSQL from Host

You can connect to the containerized PostgreSQL from Windows:

### Using psql
```powershell
psql -h localhost -p 5433 -U postgres -d capstone
# Password: capstone1234
```

### Using pgAdmin or DBeaver
- **Host**: `localhost`
- **Port**: `5433`
- **Username**: `postgres`
- **Password**: `capstone1234`
- **Database**: `capstone`

## Docker Compose Commands

```powershell
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services (keeps data)
docker-compose down

# Stop and remove volumes (deletes database data!)
docker-compose down -v

# View all logs
docker-compose logs -f

# View Flask app logs only
docker-compose logs -f flask_app

# View PostgreSQL logs only
docker-compose logs -f capstone_postgres

# Restart services
docker-compose restart

# Rebuild and start
docker-compose up --build
```

## Port Configuration

- **Host Port 8001** → Container Port 8000 (Flask app)
- **Host Port 5433** → Container Port 5432 (PostgreSQL)
- **Local PostgreSQL on 5432** (if running) is separate and untouched

If port conflicts occur, edit `docker-compose.yml`:
```yaml
# For Flask app
ports:
  - "8002:8000"  # Change 8001 to 8002

# For PostgreSQL
ports:
  - "5434:5432"  # Change 5433 to 5434
```

## Troubleshooting

### Port Already in Use

**Port 5433:**
```powershell
# Find process using port 5433
netstat -ano | findstr :5433
# Kill the process (replace PID)
Stop-Process -Id <PID> -Force
```

**Port 8001:**
```powershell
# Find and kill process on port 8001
netstat -ano | findstr :8001
Stop-Process -Id <PID> -Force
```

### Container Won't Start

```powershell
# Check Docker Desktop is running
docker info

# Remove old containers and rebuild
docker-compose down
docker-compose up --build --force-recreate
```

### Database Connection Issues

```powershell
# Check PostgreSQL container health
docker-compose ps

# View PostgreSQL logs
docker-compose logs capstone_postgres

# Verify database exists
docker exec -it capstone_postgres psql -U postgres -c "\l"
```

### Model Not Loading

```powershell
# Ensure model_mole.keras exists
Test-Path ".\model_mole.keras"

# If missing, create it first
python convert_model.py
```

### Data Persistence

Database data is stored in Docker volume `postgres_data`. To completely reset:
```powershell
docker-compose down -v  # Deletes volumes
docker volume rm project_postgres_data  # Force remove if needed
docker-compose up --build
```

## Environment Variables

Edit `.env` to customize configuration:

```env
# Flask Configuration
SECRET_KEY=capstone1234
FLASK_PORT=8000
FLASK_HOST=0.0.0.0
FLASK_DEBUG=True

# Database Configuration (Containerized PostgreSQL)
# Connects to PostgreSQL container via Docker network
DATABASE_URL=postgresql://postgres:capstone1234@capstone_postgres:5432/capstone

# Model Configuration
MOLE_MODEL_PATH=model_mole.keras
PREDICTION_THRESHOLD=0.37

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Admin User Configuration
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_DOB=01-01-2025
```

**Note**: The `DATABASE_URL` in `.env` is overridden by `docker-compose.yml` environment section.

## Docker Network Architecture

```
Windows Host Machine
├── Port 5432: Local PostgreSQL (if any) - SEPARATE & UNTOUCHED
├── Port 5433: → capstone_postgres:5432 (containerized)
└── Port 8001: → capstone_flask_app:8000

Docker Internal Network (capstone_network)
├── capstone_postgres:5432
│   └── Volume: postgres_data (persistent storage)
└── capstone_flask_app:8000
    ├── Connects to: capstone_postgres:5432
    └── Volumes: uploads/, model_mole.keras (read-only)
```

## Data Persistence

- **PostgreSQL Data**: Stored in Docker volume `postgres_data` (survives restarts)
- **Uploads**: Mounted from `./uploads` on host (always persists)
- **Model File**: Read-only mount from host (always persists)

## API Endpoints

Once running, test the API:

### Health Check
```powershell
curl http://localhost:8001/health
```

### Login (get token)
```powershell
curl -X POST http://localhost:8001/login `
  -H "Content-Type: application/json" `
  -d '{"username":"admin","password":"admin123"}'
```

### Mole Prediction
```powershell
$token = "your_jwt_token_here"
curl -X POST http://localhost:8001/mole/predict `
  -H "Authorization: Bearer $token" `
  -F "image=@path/to/image.jpg"
```

## Running Without Docker (Optional)

If you need to run directly with Python (not recommended for production):

```powershell
# Update .env DATABASE_URL to point to your local PostgreSQL
# DATABASE_URL=postgresql://postgres:<password>@localhost:5432/capstone

# Install dependencies
pip install -r requirements.txt

# Run the app
python app1.py
```

The app will run on `http://localhost:8000` (not 8001).

## Notes

- PostgreSQL data persists in Docker volume `postgres_data`
- Uploads are stored in `./uploads` directory (mounted from host)
- Model file is mounted read-only for easy updates without rebuilds
- Containers restart automatically unless stopped manually (`unless-stopped` policy)
- Flask app waits for PostgreSQL health check before starting
- Default admin user (`admin:admin123`) is created on first run
