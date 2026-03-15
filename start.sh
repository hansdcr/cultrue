uv run uvicorn main:app \
  --host 0.0.0.0 \
  --port 8001 \
  --reload \
  --reload-exclude '.venv/*' \
  --reload-exclude '__pycache__/*' \
  --reload-exclude '*.pyc'