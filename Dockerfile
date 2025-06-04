FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY bot.py .

# Create volume mount point for Obsidian vault
VOLUME /vault

CMD ["python", "bot.py"]
