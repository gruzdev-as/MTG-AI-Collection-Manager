# MTG Cards Image Detection & Collection Manager

A modern, highly-scalable platform to automate cataloging Magic: The Gathering cards. Instead of manually searching and adding cards, this application lets you point your smartphone or webcam at a physical card, automatically detects it using computer vision and machine learning embeddings, fetches its real-time market price, and persists it to your personal digital portfolio.

## Project Motivation

I was inspired to simplify the process of managing my MTG cards for trading purposes. Manually updating a collection is time-consuming, so I set out to automate it. What started as a simple script has evolved into a fully containerized microservice architecture featuring an in-browser scanner, real-time asynchronous inference, and daily automated market price synchronization.

## Architecture & Tech Stack

This project has been heavily modernized from its original Flask roots. It now relies on a robust, asynchronous microservices architecture:

- **Frontend**: React + Vite + Tailwind CSS. Features an in-browser scanner HUD overlay that accesses your device's camera natively—no third-party IP Webcam apps required.
- **Backend API**: FastAPI + SQLAlchemy (async) + PostgreSQL. Manages the collection state, user portfolios, and orchestrates tasks.
- **Inference Worker**: A dedicated background worker processing image embeddings natively. Driven by Redis Streams for scalable, asynchronous task queuing.
- **Price Synchronization**: Integrates directly with the Scryfall API via `httpx` and `APScheduler` to update market prices (USD/EUR + Foil values) automatically every 24 hours.

## Key Features

- **Browser-Native Scanning**: Point your camera at a card directly from the web app. The frontend handles frame capture, cropping, and queuing.
- **Smart Matching**: Employs OpenAI's CLIP-VIT-LARGE model to generate 768-dimensional embeddings, efficiently queried via a Hierarchical Navigable Small World (HNSW) index.
- **Top 5 Selection**: The inference engine returns the top 5 closest matches for every scan, giving you a beautiful dropdown UI to confirm the exact set and printing of your card.
- **Foil & Condition Tracking**: Manage the physical condition and foil status of each card, which dynamically recalculates your portfolio value.
- **Automated Price Tracking**: A background cron-like engine keeps your collection's financial value strictly up-to-date.

## Data Files & Useful Links

1) Pretrained model - [CLIP-VIT-LARGE](https://huggingface.co/openai/clip-vit-large-patch14)
2) Images for embedding creation - [Kaggle MTG image Dataset](https://www.kaggle.com/datasets/strangerone/mtg-multilang-images) 
3) HNSW Index for embeddings - [HNSW_Index](https://drive.google.com/file/d/1JWQZn68z7fdvxXt1bywYjJR3DsHPW3eU/view?usp=sharing) 
4) JSON for HNSW index embeddings - [HNSW json](https://drive.google.com/file/d/1F0FgjCM91Wei4LcLvc7R6TrG2_ZefeSF/view?usp=sharing)
5) [ScryFall API](https://scryfall.com/docs/api)

## Installation & Running Locally

The entire application is orchestrated using Docker Compose.

1. Ensure you have Docker and Docker Compose installed.
2. Clone the repository and navigate to the project root.
3. Download the HNSW index `.bin` and `.json` files (linked above) and place them in the correct data directory (`data/embeddings/` or as mapped in your `docker-compose.yaml`).
4. Build and run the containers:
   ```bash
   docker compose up --build -d
   ```
5. Access the application in your browser:
   - Make sure you use the local IP address of the host machine (e.g., `https://192.168.1.X`) to access the frontend from your smartphone.
   - Note: Because camera access requires a secure context, the frontend Nginx proxy serves a self-signed HTTPS certificate.

## Process Flow

### 1. Card Detection & UI Framing
The frontend provides a targeting reticle. When you click capture, it crops the frame to the exact aspect ratio of an MTG card directly in the browser and submits it to the backend.

### 2. Async Queueing (Redis)
The FastAPI backend receives the image and immediately drops it into a Redis Stream queue, returning a Job ID to the frontend. The frontend begins polling for completion.

### 3. Embedding Generation & Matching
The Inference worker picks up the job, runs perspective correction (if necessary), and passes the image through the CLIP model. It then queries the HNSW index to find the 5 closest neighbors using cosine similarity.

### 4. Database & Pricing (Postgres)
When you confirm the match, the backend commits the card to PostgreSQL. A dedicated price synchronization engine runs daily batches against the Scryfall API, aggressively applying fallback strategies (e.g. matching non-English cards to their English pricing equivalents) to keep your portfolio accurately valued.