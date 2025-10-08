# Use a lightweight official Python base image
FROM python:3.10-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Copy all project files into the container
COPY . /app

# Install system dependencies (optional but good for networking speed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl gcc libffi-dev libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -U \
    pyrogram==2.0.106 \
    telethon==1.36.0 \
    tgcrypto \
    python-dotenv==1.0.1 \
    aiofiles==23.2.1 \
    pillow==10.0.0 \
    uvloop==0.19.0 \
    httpx==0.27.0

# Show the Pyrogram version for debug
RUN python -c "import pyrogram; print('✅ Pyrogram version:', pyrogram.__version__)"

# Default command to start the bot (Heroku will run this)
CMD ["bash", "start"]