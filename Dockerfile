# Use the official Python slim image for smaller size
FROM python:3.11.4-slim-buster

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libc-dev && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements and install dependencies
COPY ./requirements /app/requirements
RUN pip install -r /app/requirements/production.txt

# Copy entrypoint script and make it executable
COPY ./entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Copy the rest of the project
COPY . /app

# Expose the app port
EXPOSE 8000

# Set the entrypoint command
ENTRYPOINT ["/app/entrypoint.sh"]

# Start the server
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
