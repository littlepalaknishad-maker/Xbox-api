# File: Dockerfile
# CLAUDE MYTHOS - WORKING DOCKERFILE

# Use specific Python version
FROM python:3.11.7-slim

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY xbox_c2_api.py .

# Create non-root user (optional)
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Run
CMD ["python", "xbox_c2_api.py"]
