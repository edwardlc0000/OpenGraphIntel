FROM python:3.9-slim

WORKDIR /app

# Copy and install dependencies for the LLM query service
COPY open_graph_intel/ingestion/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container
COPY open_graph_intel/ /app/open_graph_intel/

EXPOSE 8000

CMD ["uvicorn", "open_graph_intel.llm_query.main:app", "--host", "0.0.0.0", "--port", "8000"]