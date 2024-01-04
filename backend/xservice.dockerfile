FROM python:3.8-slim

WORKDIR /app

COPY . .

# Install Geckodriver
RUN apt update \                             
    && apt install -y --no-install-recommends \
    ca-certificates curl firefox-esr \
    && rm -rf /var/lib/apt/lists/* \
    && curl -L https://github.com/mozilla/geckodriver/releases/download/v0.33.0/geckodriver-v0.33.0-linux64.tar.gz | tar xz -C /usr/local/bin \
    && apt purge -y ca-certificates curl

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r xservice.requirements.txt

EXPOSE 50051

CMD ["python", "-m", "app.xservice.server"]
