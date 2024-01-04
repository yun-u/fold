FROM python:3.8-slim

WORKDIR /app

COPY . .

RUN apt update \    
    && apt install -y build-essential

RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

CMD ["celery", "-A", "app.pipeline.celery", "worker", "--loglevel=INFO"]
