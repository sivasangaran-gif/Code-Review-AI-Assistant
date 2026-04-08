FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose the API Port (7860) and UI Port (8501)
EXPOSE 7860
EXPOSE 8501

# MANDATORY: Run FastAPI on 7860 and Streamlit on 8501
# We use & to run both. The validator will hit the Space URL on 7860.
CMD ["sh", "-c", "uvicorn server.app:app --host 0.0.0.0 --port 7860 & streamlit run frontend/app.py --server.port 8501 --server.address 0.0.0.0"]