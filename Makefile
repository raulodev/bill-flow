
help:
	@echo "Usage: make <target>"
	@echo "  dev            Starts the development server"
	@echo "  pytest         Runs the tests"
	@echo "  celery         Starts the celery worker"
	@echo "  beat           Starts the celery beat"
	@echo "  flower         Starts the flower web server"
	@echo "  celery-beat    Starts the celery and beat together"
	@echo "  uvicorn        Starts the uvicorn server"
	@echo "  mkdocs         Starts the mkdocs server"

dev:
	fastapi dev app/main.py

pytest:
	pytest --cov=app --cov-report=xml tests/


celery:
	celery -A app.scheduler worker --loglevel=debug

beat:
	celery -A app.scheduler beat --loglevel=debug

flower:
	celery -A app.scheduler flower

celery-beat:
	celery -A app.scheduler worker --beat --loglevel=debug

uvicorn:
	uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 1

mkdocs:
	mkdocs serve