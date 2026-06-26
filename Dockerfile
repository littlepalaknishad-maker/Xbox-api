FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY xbox_c2_api.py .

# Create non-root user
RUN useradd -m -u 1000 c2user && chown -R c2user:c2user /app
USER c2user

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "xbox_c2_api.py"]
