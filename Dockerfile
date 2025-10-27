FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

# Install Podman inside container (for managing vaults)
RUN apt-get update && \
    apt-get install -y podman && \
    rm -rf /var/lib/apt/lists/*

EXPOSE 8080
CMD ["python", "run.py"]