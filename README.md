backend

to create and start venv
python -m venv .venv
python -m pip install --upgrade pip setuptools wheel build
.\.venv\Scripts\Activate
pip install -r requirements.txt

to exit venv
deactivate
