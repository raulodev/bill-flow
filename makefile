dev:
	fastapi dev app/main.py

pytest:
	pytest tests/ -s

test-cov:
	pytest --cov=app tests/

celery:
	celery -A app.scheduler worker --loglevel=debug

beat:
	celery -A app.scheduler beat --loglevel=debug

flower:
	celery -A app.scheduler flower

celery-beat:
	celery -A app.scheduler worker --beat --loglevel=debug

uvicorn:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 4