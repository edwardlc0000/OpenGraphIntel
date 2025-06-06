FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies for the graph service
COPY backend/graph/graph-requirements.txt /app/
RUN pip install --no-cache-dir -r graph-requirements.txt

# Copy the entire application code into the container
COPY backend/ /app/backend/

EXPOSE 8001

CMD ["uvicorn", "backend.graph.main:app", "--host", "0.0.0.0", "--port", "8001"]