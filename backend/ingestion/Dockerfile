FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies for the ingestion service
COPY backend/ingestion/ingestion-requirements.txt /app/
RUN pip install --no-cache-dir -r ingestion-requirements.txt

# Copy the entire application code into the container
COPY backend/ /app/backend/

EXPOSE 8000

CMD ["uvicorn", "backend.ingestion.main:app", "--host", "0.0.0.0", "--port", "8000"]