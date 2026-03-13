# Use official Python slim image
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (needed for psycopg2 / SQLAlchemy with PostgreSQL)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend source code
COPY . .

# Expose the port FastAPI/Uvicorn will run on
EXPOSE 8000

# Start the FastAPI app with Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
