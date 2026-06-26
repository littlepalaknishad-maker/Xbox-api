# File: Dockerfile
# CLAUDE MYTHOS - OPTIMIZED DOCKERFILE
# For authorized security testing only

FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies - NO SYSTEM DEPENDENCIES NEEDED
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY xbox_c2_api.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "xbox_c2_api.py"]
