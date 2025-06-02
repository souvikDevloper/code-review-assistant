AI-Powered Code Review Assistant


A full-stack application that leverages a fine-tuned CodeT5 model to automatically review code snippets. It consists of:

Data Pipeline:

Scripts to collect and preprocess code–review pairs.

Finetuning: 

A Python script for LoRA-based fine-tuning of CodeT5 on your data.

Backend API: 

A FastAPI service that loads the fine-tuned model and exposes endpoints for health checking and code review.

Frontend UI: 

A React + TailwindCSS single-page app that allows users to submit code and receive automated reviews.

Docker & Docker-Compose: 

Preconfigured containers for easy local deployment of the entire stack (model + API + UI).

Table of Contents
Features

Architecture & Directory Structure

Prerequisites

Local Setup (Without Docker)

Backend (FastAPI)

Frontend (React)

Model Finetuning

Data Pipeline

Docker-Compose Setup (Recommended)

Build & Run All Services

Stopping & Cleaning Up

Usage

API Endpoints

Frontend Interaction

Example cURL Requests

Deployment

Contributing

License

Features:

Automatic Code Review: 

Leverages a fine-tuned CodeT5 (with LoRA) to generate suggestions for Python code snippets.

Interactive UI: 

Simple React + Tailwind interface that accepts code input and displays the model’s review.

Scalable Backend: 

FastAPI service with asynchronous endpoints for health checks and code review (batchable, beam search).

Containerized: 

Fully Dockerized stack—run everything locally with a single docker-compose up.

Easy Finetuning: 

LoRA-based finetuning script to adapt CodeT5 on your own code–review dataset.

Modular Pipeline: 

A data_pipeline folder for ingesting, cleaning, and preparing data for finetuning.

Architecture & Directory Structure



code-review-assistant/


├── data_pipeline/

│
  └── crawl_and_prepare.py     # Script to crawl GitHub PRs or StackOverflow threads
├── data/   


├── finetune/


│   └── finetune_codet5_lora.py  # LoRA finetuning script (Python)

├── api/


│   ├── main.py    

│   ├── requirements.txt  
                              # Python dependencies for the API
│  
    └── Dockerfile.backend       # Dockerfile for creating the backend container

├── frontend/
│
    ├── public/
│   │   ├── index.html           # HTML template
│
│       └── favicon.ico
│     ├── src/
│   │
      ├── App.jsx              # Main React component
│

│     └── index.jsx  
                                 # React entry point
│   ├── package.json 
                                 # Frontend dependencies & scripts
│   ├── tailwind.config.js       # TailwindCSS configuration

│   └── Dockerfile               # Multi-stage build (Node → Nginx)
├── models/
│   └── codet5-lora/   
                                 # Fine-tuned model artifacts (tokenizer, weights, config)
│       ├── adapter_config.json


│       ├── adapter_model.safetensors

│       ├── merges.txt

│       ├── special_tokens_map.json

│       ├── tokenizer_config.json

│       ├── vocab.json

│       └── checkpoint-*/   
                                     # Intermediate checkpoints (if any)
├── Dockerfile.backend     

                                 # Alias for api/Dockerfile.backend (for GH)
├── docker-compose.yml      

                                        # Compose file to spin up `api` + `frontend`
└── README.md                                       # This documentation
Prerequisites
Python 3.8+

Node.js v14+ & npm (or yarn)

Git

Docker (Engine + Compose), if you plan to run via containers

(Optional) CUDA-enabled GPU + compatible NVIDIA drivers (for faster finetuning/inference)

Local Setup (Without Docker)
You can develop each part independently (API, frontend, finetuning) on your host machine.

Backend (FastAPI)
Navigate to the api/ folder


cd api
Create & activate a virtual environment (recommended)


python -m venv .venv
source .venv/bin/activate        # Linux/macOS
.venv\Scripts\activate           # Windows PowerShell
Install Python dependencies


pip install --upgrade pip
pip install -r requirements.txt
The key requirements include:

fastapi

uvicorn

transformers

torch

pydantic

Ensure models/codet5-lora is present
The FastAPI app expects to find the codet5-lora folder inside api/../models. If you cloned the entire repo, it should be there.


ls ../models/codet5-lora
Run the API server


uvicorn main:app --reload --host 0.0.0.0 --port 8000
Your {"GET /health"} endpoint is live at http://localhost:8000/health.

The {"POST /review"} endpoint lives at http://localhost:8000/review.

Frontend (React + TailwindCSS)
Navigate to the frontend/ folder


cd ../frontend
Install Node.js dependencies


npm install
(Or use yarn if you prefer.)

Tailwind Setup

The default tailwind.config.js is already configured to scan src/**/* and public/index.html.

If you wish to regenerate your own CSS, you can run:



npx tailwindcss -i ./src/index.css -o ./public/output.css --watch
(But the project is preconfigured to import Tailwind via postcss.)

Start React in Development Mode




npm start
React’s dev server will run on http://localhost:3000 by default.

It proxies API requests to http://localhost:8000 (see package.json → "proxy": "http://localhost:8000").

Open your browser at http://localhost:3000. You should see the code submission form.

Model Finetuning (LoRA)
The finetune/finetune_codet5_lora.py script expects that you have a prepared dataset in a Hugging Face–compatible format (e.g., a JSON lines file with {"input": "...", "target": "..."}).

Navigate to the finetune/ directory




cd ../finetune

Install required Python packages (in the same or a new virtualenv)



pip install transformers datasets peft bitsandbytes torch


NOTE: If you want 8-bit or 4-bit quantization, ensure you have a recent bitsandbytes and a compatible GPU + CUDA toolkit.

Run the finetuning script



python finetune_codet5_lora.py \
    --train_file ../data/train.jsonl \
    --validation_file ../data/valid.jsonl \
    --output_dir ../models/codet5-lora \
    --num_train_epochs 3 \
    --per_device_train_batch_size 4 \
    --learning_rate 1e-4 \
    --lora_r 8 \
    --lora_alpha 32 \
    --lora_dropout 0.05 \
    --seed 42
Adjust hyperparameters as needed (e.g., --num_train_epochs, --per_device_train_batch_size, --learning_rate).

After training, your fine-tuned adapter weights and tokenizer config will be saved under models/codet5-lora/.

Data Pipeline
Optional: This repository includes a sample script (data_pipeline/crawl_and_prepare.py) to collect code–review pairs from GitHub or StackOverflow. It’s meant as a starting point for building your own dataset.

Install any required libraries


pip install requests beautifulsoup4 pandas
Run the crawler/preparation script


python data_pipeline/crawl_and_prepare.py --output_dir data/processed
Modify the script to point at your target sources (e.g., public GitHub PR URLs or StackOverflow questions).

The script will produce a cleaned .jsonl or .csv file in data/processed/, which can then be used by the finetuning step.

Docker-Compose Setup (Recommended)
The easiest way to spin up the entire stack (API + React UI) is via Docker and Docker Compose. The repository already includes:

Dockerfile.backend (for the FastAPI service)

frontend/Dockerfile (multi-stage build: Node → Nginx)

docker-compose.yml (orchestrates api and frontend services)

Build & Run All Services
Open a terminal in the project root


cd /path/to/code-review-assistant
Build both containers


docker-compose build
This will create two images:

code-review-assistant-api

code-review-assistant-frontend

Launch the stack


docker-compose up
The FastAPI backend will be available at http://localhost:8000.

The React frontend (served by Nginx) will be available at http://localhost:3000.

Verify both are running

In another terminal:


curl -I http://localhost:8000/health
-- You should get HTTP/1.1 200 OK and a JSON payload {"status":"ok"}.

Then:


curl -I http://localhost:3000
-- You should see HTTP/1.1 200 OK served by Nginx.

Stopping & Cleaning Up
Stop & tear down the containers


docker-compose down
(Optional) Remove images/volumes


docker-compose down --rmi all --volumes
Usage
API Endpoints
Once the backend is running (either via uvicorn locally or via Docker), you have the following endpoints:

Health Check

URL: GET /health

Response: { "status": "ok" }

Code Review

URL: POST /review

Headers:

Content-Type: application/json

Request Body:


{
  "code": "for i in range(len(my_list)):\n    print(my_list[i])",
  "max_length": 128,      // optional; defaults to 256
  "num_beams": 4          // optional; defaults to 4
}
Response Body:


{
  "review": "<model-generated suggestions>"
}
Example cURL (Linux/macOS):


curl -X POST http://localhost:8000/review \
     -H "Content-Type: application/json" \
     -d '{"code": "for i in range(len(my_list)):\n    print(my_list[i])", "max_length": 128, "num_beams": 4}'
PowerShell (Windows):


Invoke-RestMethod -Method POST `
  -Uri http://localhost:8000/review `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{ "code": "for i in range(len(my_list)):`n    print(my_list[i])", "max_length": 128, "num_beams": 4 }'
Frontend Interaction
Open your browser to http://localhost:3000.

You’ll see a textarea where you can paste a Python code snippet (or any code your model was trained on).

Click Get Review—the React UI will send a request to http://localhost:8000/review.

The model’s suggested review appears below the button once the API responds.

CORS

In development, the React dev server proxies all /review calls to http://localhost:8000 (see "proxy": "http://localhost:8000" in frontend/package.json).

In production (Docker), the React bundle is served by Nginx, but calls to localhost:8000/review still work because both services share the same network.

Example cURL Requests
Health Check


curl -i http://localhost:8000/health

HTTP/1.1 200 OK
content-type: application/json
content-length: 15

{"status":"ok"}
Review a Snippet


curl -X POST http://localhost:8000/review \
     -H "Content-Type: application/json" \
     -d '{ 
           "code": "for i in range(len(my_list)):\n    print(my_list[i])", 
           "max_length": 128, 
           "num_beams": 4 
         }'

{
  "review": "print(my_list[i]) print(my_list[i]) …"
}
Deployment
You can deploy this stack in various ways:

On-Premises / Local Server

Install Docker ± Docker Compose on your host machine.

Clone this repo, place your fine-tuned models/codet5-lora under ./models, then run:


docker-compose build
docker-compose up -d
The UI will be accessible on port 3000 and API on port 8000.

If your environment requires HTTPS, you can place Nginx or Traefik in front of the containers and configure SSL termination.

Cloud VPS / VM

Provision a small cloud VM (e.g., AWS EC2, DigitalOcean Droplet).

Install Docker Engine + Compose, clone this repo, and run the same Docker Compose commands.

Point your domain (e.g., code-review.example.com) to the VM’s IP and optionally set up a Let’s Encrypt certificate.

Kubernetes

Convert the docker-compose.yml into Kubernetes manifests (Deployments, Services, Ingress).

Store your fine-tuned model in a shared volume or in object storage (S3, GCS).

Use a GPU-enabled node pool if you plan to do inference with a GPU (otherwise, CPU inference is supported out of the box).

Contributing
Fork the Repository

Click ▶️ Code → Fork in the top right of GitHub to create your own copy.

Clone Your Fork Locally


git clone https://github.com/<your-username>/code-review-assistant.git
cd code-review-assistant
Create a New Branch


git checkout -b feature/your-description
Develop & Commit

Make changes to code, tests, or documentation.

Stage + commit:


git add .
git commit -m "feat: Describe your change here"
Push & Open a Pull Request


git push -u origin feature/your-description
Go to GitHub → Compare & pull request → Create pull request.

Add a clear description of what you’ve changed and why.

Code Review & Merge

Project maintainers will review your PR.

Address any feedback, then the PR can be merged once approved.

License
By default, this repository is released under the MIT License.
Feel free to adapt the license to your organization’s policy.


MIT License

Copyright (c) 2025 SouvikDeveloper

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the “Software”), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

… (standard MIT terms) …
Thank you for using AI-Powered Code Review Assistant! If you encounter any issues or have suggestions, please open an issue or submit a pull request.
