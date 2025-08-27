# Use lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Expose Cloud Run port (optional, Cloud Run injects PORT anyway)
EXPOSE 8080

# Start FastAPI with uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}
