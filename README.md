backend

to create and start venv
python -m venv .venv
.\.venv\Scripts\Activate
python -m pip install --upgrade pip setuptools wheel build
pip install -r requirements.txt

to exit venv
deactivate

docker-compose up --build
Ctrl+C
docker-compose up -d