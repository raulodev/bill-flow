
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
	uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 1 --reload

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

mkdocs:
	mkdocs serve