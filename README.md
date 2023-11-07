pip freeze > requirements.txt

python -m venv venv
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

uvicorn api:app --reload

http://localhost:8000/docs#/
http://localhost:8000/redoc#/
