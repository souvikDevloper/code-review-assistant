# api/main.py

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch

# ------------------------------------------------------------
# 1) Configure logging (optional, but helps track startup errors)
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# ------------------------------------------------------------
# 2) Create FastAPI app and add CORS middleware
# ------------------------------------------------------------
app = FastAPI(
    title="Code Review Assistant API",
    description="Accepts a code snippet and returns review/suggestions as text",
    version="1.0",
)

# Allow browser requests from the React frontend (http://localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # ← your React app’s origin
    allow_credentials=True,
    allow_methods=["*"],                      # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],                      # allow all headers (e.g. Content-Type)
)

# ------------------------------------------------------------
# 3) Detect device (use GPU if available, else CPU)
# ------------------------------------------------------------
device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
logging.info(f"Using device: {device}")

# ------------------------------------------------------------
# 4) Load tokenizer + model from local directory “model”
#    - Docker Compose will mount ./models/codet5-lora → /app/model
# ------------------------------------------------------------
MODEL_DIR = os.getenv("MODEL_DIR", "model")

try:
    # Load pretrained tokenizer & model from the mounted folder
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)
    model.to(device)
    logging.info(f"Loaded tokenizer and model from '{MODEL_DIR}'")
except Exception as e:
    logging.error(f"Error loading model from '{MODEL_DIR}': {e}")
    raise RuntimeError(f"Failed to load model from {MODEL_DIR}: {e}")

# ------------------------------------------------------------
# 5) Pydantic schema for the POST /review endpoint
# ------------------------------------------------------------
class CodeRequest(BaseModel):
    code: str
    max_length: int = 256    # Maximum number of tokens in the generated review
    num_beams: int = 4       # Beam size for beam search during generation

# ------------------------------------------------------------
# 6) Health check (GET /health)
# ------------------------------------------------------------
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# ------------------------------------------------------------
# 7) Optional root endpoint (GET /)
# ------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Code Review Assistant API is running."}

# ------------------------------------------------------------
# 8) Main code‐review endpoint (POST /review)
# ------------------------------------------------------------
@app.post("/review")
async def review_code(request: CodeRequest):
    """
    Accepts a JSON body with:
      {
        "code": "<your code snippet here>",
        "max_length": 256,
        "num_beams": 4
      }
    Returns:
      { "review": "<model’s generated text>" }
    """
    # 8.1) Validate non‐empty code field
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="`code` field cannot be empty.")

    # 8.2) Tokenize the input snippet
    try:
        inputs = tokenizer(
            request.code,
            return_tensors="pt",
            truncation=True,
            padding="longest",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
    except Exception as tok_err:
        logging.error(f"Tokenization error: {tok_err}")
        raise HTTPException(status_code=500, detail=f"Tokenization failed: {tok_err}")

    # 8.3) Generate with the model
    try:
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_length=request.max_length,
                num_beams=request.num_beams,
                early_stopping=True,
            )
    except Exception as gen_err:
        logging.error(f"Generation error: {gen_err}")
        raise HTTPException(status_code=500, detail=f"Model generation failed: {gen_err}")

    # 8.4) Decode tokens back to text
    try:
        review_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    except Exception as dec_err:
        logging.error(f"Decoding error: {dec_err}")
        raise HTTPException(status_code=500, detail=f"Decoding failed: {dec_err}")

    return {"review": review_text}
