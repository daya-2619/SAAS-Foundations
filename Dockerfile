ARG PYTHON_VERSION=3.13.7
FROM python:${PYTHON_VERSION}-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set working directory to src for Django commands
WORKDIR /app/src

EXPOSE 8000

# Default command
CMD ["gunicorn", "cfehome.wsgi:application", "--bind", "0.0.0.0:8000"]
