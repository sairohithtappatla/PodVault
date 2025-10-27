FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . /app

# Expose Flask port
EXPOSE 8080

# Run the application
CMD ["python", "run.py"]