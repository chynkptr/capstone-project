# Quick Reference - Capstone Flask API

## Start the Application

### Option 1: Docker Compose (Recommended)
```powershell
cd "C:\Users\kptry\OneDrive\Documents\Casptone Project\project"
docker-compose up --build
```
Access at: **http://localhost:8001**

### Option 2: Direct Python
```powershell
cd "C:\Users\kptry\OneDrive\Documents\Casptone Project\project"
python app1.py
```
Access at: **http://localhost:8000**

## Important URLs

- Home: http://localhost:8001/
- Health: http://localhost:8001/health
- Login: POST http://localhost:8001/login
- Signup: POST http://localhost:8001/signup
- Predict: POST http://localhost:8001/mole/predict

## Default Credentials

- Username: `admin`
- Password: `admin123`

## Key Configuration

| Setting | Docker | Local |
|---------|--------|-------|
| Flask Port | 8001 (mapped from 8000) | 8000 |
| Database Host | host.docker.internal | localhost |
| Database Port | 5432 | 5432 |
| Database Name | capstone | capstone |
| Database User | postgres | postgres |
| Database Password | 22Feb03 | 22Feb03 |

## Common Commands

```powershell
# Docker Compose
docker-compose up -d          # Start in background
docker-compose down           # Stop all services
docker-compose logs -f        # View logs
docker-compose restart        # Restart services

# Check PostgreSQL
Get-Service postgresql*       # Windows service status
psql -U postgres -l          # List databases

# Test API
curl http://localhost:8001/health
```

## Files Modified/Created

✅ `app1.py` - Uses environment variables, connects to host PostgreSQL
✅ `.env` - Configuration file with all settings
✅ `Dockerfile` - Lightweight, no PostgreSQL installation
✅ `docker-compose.yml` - Maps port 8001, connects to host PostgreSQL
✅ `requirements.txt` - Added TensorFlow
✅ `DOCKER_SETUP.md` - Complete documentation
✅ `.gitignore` - Protects sensitive files

## Troubleshooting

**Cannot connect to database:**
- Verify PostgreSQL is running: `Get-Service postgresql*`
- Check database exists: `psql -U postgres -l | Select-String "capstone"`

**Port conflict:**
- Edit `docker-compose.yml` line 9: change `"8001:8000"` to `"8002:8000"`

**Model not found:**
- Run: `python convert_model.py`
- Or copy: `Copy-Item "../keras_model.keras" "model_mole.keras"`
