# Docker Container Management Guide

## No Need to Rebuild Every Time!

Once containers are created, you **don't need to rebuild** unless you change:
- `Dockerfile`
- `requirements.txt`
- Python code (if you want changes reflected in the container)

---

## Exiting Containers (Stop Running)

### If running in foreground (you see logs):
```powershell
# Press Ctrl+C to stop
Ctrl+C
```

### If running in detached mode (`-d` flag):
```powershell
# Stop all containers and remove them
docker-compose down

# Stop containers but keep them (faster restart)
docker-compose stop
```

---

## Entering/Restarting Containers

### Start existing containers (no rebuild needed):
```powershell
# Start in foreground (see logs in terminal)
docker-compose up

# Start in background (detached mode)
docker-compose up -d
```

### View logs of running containers:
```powershell
# View all container logs (follow mode)
docker-compose logs -f

# View specific container logs
docker-compose logs -f flask_app
docker-compose logs -f capstone_postgres

# View last 50 lines
docker-compose logs --tail=50 flask_app
```

### Execute commands inside running containers:
```powershell
# Enter Flask app container (bash shell)
docker exec -it capstone_flask_app bash

# Enter PostgreSQL container (bash shell)
docker exec -it capstone_postgres bash

# Run psql directly in Postgres container
docker exec -it capstone_postgres psql -U postgres -d capstone

# Run a single command in Flask container
docker exec capstone_flask_app ls -la

# Run Python shell in Flask container
docker exec -it capstone_flask_app python
```

---

## Common Workflows

### 1. Daily Use (no code changes)
```powershell
# Start containers
docker-compose up -d

# Check status
docker-compose ps

# View logs if needed
docker-compose logs -f

# Stop containers when done
docker-compose down
```

### 2. After Code Changes (app1.py or Python files modified)
```powershell
# Option 1: Rebuild and restart all services
docker-compose up --build

# Option 2: Rebuild specific service only
docker-compose build flask_app
docker-compose up -d

# Option 3: Rebuild and recreate containers
docker-compose up --build --force-recreate
```

### 3. Fresh Database (clear all data)
```powershell
# Stop containers and remove volumes (WARNING: deletes all database data!)
docker-compose down -v

# Start fresh with clean database
docker-compose up --build
```

### 4. Restart After Configuration Changes
```powershell
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart flask_app
```

### 5. Check Container Status
```powershell
# See running containers (docker-compose)
docker-compose ps

# See all Docker containers
docker ps

# See all containers including stopped ones
docker ps -a
```

---

## Inside Container Commands

### Entering Flask App Container
```powershell
docker exec -it capstone_flask_app bash
```

Once inside:
```bash
# Check installed Python packages
pip list

# Check Python version
python --version

# Run Python interactive shell
python

# Check file structure
ls -la

# View app logs (if any)
cat /var/log/*.log

# Test database connection
python -c "from app1 import db; print('DB connected!' if db else 'DB failed')"

# Exit container
exit
```

### Entering PostgreSQL Container
```powershell
docker exec -it capstone_postgres psql -U postgres -d capstone
```

Once inside psql:
```sql
-- List all tables
\dt

-- List all users
\du

-- List all databases
\l

-- View user table
SELECT * FROM "user";

-- Count users
SELECT COUNT(*) FROM "user";

-- Describe user table structure
\d "user"

-- Quit psql
\q
```

Or enter bash shell first:
```powershell
docker exec -it capstone_postgres bash
```

Then inside container:
```bash
# Connect to database
psql -U postgres -d capstone

# Check PostgreSQL version
psql --version

# List databases
psql -U postgres -c "\l"

# Exit container
exit
```

---

## Useful Docker Commands

### Container Inspection
```powershell
# View container details
docker inspect capstone_flask_app

# View container resource usage
docker stats

# View container processes
docker top capstone_flask_app
```

### Network & Connectivity
```powershell
# List Docker networks
docker network ls

# Inspect capstone network
docker network inspect project_capstone_network

# Test connectivity between containers
docker exec capstone_flask_app ping capstone_postgres
```

### Volume Management
```powershell
# List all volumes
docker volume ls

# Inspect postgres data volume
docker volume inspect project_postgres_data

# Remove unused volumes (WARNING: data loss!)
docker volume prune
```

### Cleanup Commands
```powershell
# Remove stopped containers
docker container prune

# Remove unused images
docker image prune

# Remove everything unused (containers, networks, images, volumes)
docker system prune -a --volumes
```

---

## Deleting Built Docker Images & Containers

### Remove Specific Containers
```powershell
# Stop and remove specific container
docker stop capstone_flask_app
docker rm capstone_flask_app

# Stop and remove PostgreSQL container
docker stop capstone_postgres
docker rm capstone_postgres

# Or use docker-compose (recommended)
docker-compose down
```

### Remove Specific Images
```powershell
# List all images
docker images

# Remove specific image by name
docker rmi project_flask_app

# Remove specific image by ID
docker rmi <IMAGE_ID>

# Force remove image (if container exists)
docker rmi -f project_flask_app
```

### Complete Cleanup (Delete Everything)
```powershell
# Stop all containers and remove volumes
docker-compose down -v

# Remove all project images
docker rmi project_flask_app postgres:15-alpine

# Or remove all unused Docker resources
docker system prune -a --volumes

# Confirm deletion when prompted
```

### Nuclear Option (Full Reset)
```powershell
# Stop all running containers
docker stop $(docker ps -a -q)

# Remove all containers
docker rm $(docker ps -a -q)

# Remove all images
docker rmi $(docker images -q) -f

# Remove all volumes
docker volume prune -f

# Remove all networks
docker network prune -f

# Then rebuild from scratch
docker-compose up --build
```

### Remove Only This Project's Resources
```powershell
# Stop and remove containers, networks, volumes
docker-compose down -v

# Remove project-specific images
docker images | Select-String "project" | ForEach-Object { docker rmi ($_ -split '\s+')[2] -f }

# Or manually remove by name
docker rmi project_flask_app -f

# Remove project volume
docker volume rm project_postgres_data
```

### Check What Will Be Deleted (Dry Run)
```powershell
# See what containers would be removed
docker container ls -a

# See what images would be removed
docker images

# See what volumes would be removed
docker volume ls
```

---

## Quick Reference Table

| Action | Command |
|--------|---------|
| **Start (first time)** | `docker-compose up --build` |
| **Start (existing)** | `docker-compose up` |
| **Start (background)** | `docker-compose up -d` |
| **Stop (Ctrl+C)** | `Ctrl+C` |
| **Stop (detached)** | `docker-compose down` |
| **Rebuild after code change** | `docker-compose up --build` |
| **Restart services** | `docker-compose restart` |
| **View logs** | `docker-compose logs -f` |
| **View logs (specific)** | `docker-compose logs -f flask_app` |
| **Check status** | `docker-compose ps` |
| **Enter Flask container** | `docker exec -it capstone_flask_app bash` |
| **Enter Postgres (psql)** | `docker exec -it capstone_postgres psql -U postgres -d capstone` |
| **Fresh start (clear DB)** | `docker-compose down -v && docker-compose up --build` |
| **Run command in container** | `docker exec capstone_flask_app <command>` |
| **Delete containers** | `docker-compose down` |
| **Delete containers + volumes** | `docker-compose down -v` |
| **Delete images** | `docker rmi project_flask_app` |
| **Full cleanup** | `docker system prune -a --volumes` |

---

## Troubleshooting

### Container won't start
```powershell
# Check logs
docker-compose logs flask_app

# Force recreate
docker-compose up --build --force-recreate

# Remove everything and start fresh
docker-compose down -v
docker-compose up --build
```

### Can't connect to database from Flask
```powershell
# Check if Postgres is healthy
docker-compose ps

# Check Postgres logs
docker-compose logs capstone_postgres

# Test connection from Flask container
docker exec capstone_flask_app ping capstone_postgres
```

### Port already in use
```powershell
# Find process using port 8001
netstat -ano | findstr :8001

# Kill process (replace <PID>)
Stop-Process -Id <PID> -Force

# Or change port in docker-compose.yml
```

### Container uses old code
```powershell
# Rebuild without cache
docker-compose build --no-cache flask_app
docker-compose up -d
```

---

## Best Practices

1. **Use detached mode for development**: `docker-compose up -d` keeps your terminal free
2. **Check logs regularly**: `docker-compose logs -f` to catch errors early
3. **Don't delete volumes accidentally**: `docker-compose down` (good) vs `docker-compose down -v` (deletes data!)
4. **Rebuild after dependency changes**: Always run `--build` if you modify `requirements.txt`
5. **Use `docker-compose ps`**: Quick way to check if containers are running
6. **Stop gracefully**: Use `docker-compose down` instead of killing processes

---

## Summary

**Normal workflow:**
1. Start: `docker-compose up -d`
2. Work on your project
3. Check logs if needed: `docker-compose logs -f`
4. Stop: `docker-compose down`

**After code changes:**
1. Rebuild: `docker-compose up --build`

**No rebuilds needed** for normal stop/start cycles! 🚀
