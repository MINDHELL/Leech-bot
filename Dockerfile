FROM python:3.10-slim

# Install ffmpeg
RUN apt update && apt install -y ffmpeg

# Set working dir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy bot code
COPY . .

CMD ["python", "bot.py"]
