# Use a minimal Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY twitter_bot.py /app/
COPY requirements.txt /app/

# Install required packages
RUN pip install --no-cache-dir -r requirements.txt

# Default run command
CMD ["python", "twitter_bot.py"]
