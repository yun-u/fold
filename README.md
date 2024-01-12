# fold

<img src="assets/logo.svg" width="256">

_Manage your collected documents and perform vector-based searches._

## Supported features

- Web scraping to store text and metadata information
- Vector-based text search and similar document search
- Search by category, author, title, and content
- Document read-marking, bookmarking, document linking, and backlinking

## How to use

1. **Clone the Repository**: Start by cloning the repository to your local machine.

   ```bash
   git clone https://github.com/yun-u/fold.git
   cd fold
   ```

2. **Environment Setup**: Create a `.env` file in the root directory to store your environment variables.

   ```bash
   touch .env
   ```

   The example of `.env` file with necessary variables. This includes specifying the index name for Redis Search, ONNX model path, default Huggingface model ID, X user credentials, Papago API credentials, service hostnames, and the Arxiv directory to save PDF files.

   ```
   INDEX_NAME=idx
   ONNX_MODEL_HOME=/app/onnx_model

   DEFAULT_MODEL_ID=thenlper/gte-base

   X_ID=YOUR_X_ID
   X_PASSWORD=YOUR_X_PASSWORD

   PAPAGO_ID=YOUR_PAPAGO_ID
   PAPAGO_SECRET=YOUR_PAPAGO_SECRET

   RABBITMQ_HOST=rabbitmq
   REDIS_HOST=redis
   XSERVICE_HOST=xservice

   ARXIV_HOME=/arxiv
   ```

3. **Starting the Application**: Launch the application using Docker Compose. This will start all the necessary services defined in the `docker-compose.yml` file, including your application server, database, and any other dependent services. Make sure Docker is installed and running on your machine. Then, execute the following command in the root directory of the project:

   ```bash
   docker compose up
   ```

   This command initializes and starts all the containers required for the application. The services will be set up based on the configurations provided in the Docker Compose file and the `.env` file.

4. **Using the API**: To utilize the app's functionality, use the provided API endpoint. For instance, to embed a document from a URL, you can use a curl command like the following:

   ```bash
   curl -X POST \
   -H "Content-Type: application/json"\
   http://localhost/api/embed \
   -d '{
       "url": "https://arxiv.org/abs/1706.03762"
   }'
   ```

## Demo

The screenshot shows the main page of the interface. At the top, there is a filter bar that enables filtering based on various options. Below that, there is a search bar for vector searching. In the middle section, collected documents can be scrolled through vertically. Each document provides options to check linked and documents, mark as read, bookmark, and delete.

<img src="assets/main_page.png" width="1024">

Based on the cosine similarity between embeddings, it shows documents similar to the text entered in the search bar below. The results will be shown along with their cosine similarity scores, which are rescaled between 0 and 1.

<img src="assets/vector_search_page.png" width="1024">

Displays documents that are similar to other documents based on cosine similarity between their embeddings.

<img src="assets/vector_search_document_page.png" width="1024">

## How it Works

### Embed

To run the Huggingface model on a CPU, it is converted into an Optimized & Quantized ONNX model.

The system fetches text data from a URL provided by the user. This text is then segmented into sentences based on full stops ('.'). These sentences are further divided into chunks based on the model's context length. The embeddings for each chunk are calculated and stored in Redis.

<img src="assets/embed_diagram.png" width="1024">

### Search

RedisSearch has been used to implement vector search.

<img src="assets/search_diagram.png" width="1024">

## Tech Stack

### OS

![Ubuntu](https://img.shields.io/badge/Ubuntu-E95420?style=for-the-badge&logo=ubuntu&logoColor=white)

### ML/DL

![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=for-the-badge&logo=PyTorch&logoColor=white) ![HuggingFace](https://img.shields.io/badge/%F0%9F%A4%97%20huggingface-FFD21E?style=for-the-badge)

### Backend

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54) ![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi) ![Selenium](https://img.shields.io/badge/-selenium-%43B02A?style=for-the-badge&logo=selenium&logoColor=white)

![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white) ![RabbitMQ](https://img.shields.io/badge/Rabbitmq-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)

### Frontend

![TypeScript](https://img.shields.io/badge/typescript-%23007ACC.svg?style=for-the-badge&logo=typescript&logoColor=white) ![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB) ![Next JS](https://img.shields.io/badge/Next-black?style=for-the-badge&logo=next.js&logoColor=white) ![TailwindCSS](https://img.shields.io/badge/tailwindcss-%2338B2AC.svg?style=for-the-badge&logo=tailwind-css&logoColor=white) ![Radix UI](https://img.shields.io/badge/radix%20ui-161618.svg?style=for-the-badge&logo=radix-ui&logoColor=white)
