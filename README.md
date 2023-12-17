# fold

<img src="assets/logo.svg" width="256">

_**Manage linked documents and utilize vector search.**_

## Features

The screenshot shows the main page of the interface. At the top, there is a filter bar that enables filtering based on various options. Below that, there is a search bar for vector searching. In the middle section, collected documents can be scrolled through vertically. Each document provides options to check linked and documents, mark as read, bookmark, and delete.

<img src="assets/main_page.png" width="1024">

Based on the cosine similarity between embeddings, it shows documents similar to the text entered in the search bar below. The results will be shown along with their cosine similarity scores, which are rescaled between 0 and 1.

<img src="assets/vector_search_page.png" width="1024">

Displays documents that are similar to other documents based on cosine similarity between their embeddings.

<img src="assets/vector_search_document_page.png" width="1024">

## How it Works?

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

## TODO

- Use Docker
- Use Celery to manage RabbitMQ
