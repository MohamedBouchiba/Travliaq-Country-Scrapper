FROM python:3.11

WORKDIR /app

# Install system dependencies including comprehensive SSL/TLS support
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    openssl \
    libssl-dev \
    build-essential \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Command to run the scraper
CMD ["python", "-m", "src.main"]
