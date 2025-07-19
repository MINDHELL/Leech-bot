# Use official Python slim image
FROM python:3.10-slim

# Set environment variables to avoid prompts during install
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Create downloads directory
RUN mkdir -p downloads

# Run your bot
CMD ["python", "bot.py"]
