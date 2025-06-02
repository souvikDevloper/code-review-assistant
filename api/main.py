# api/main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import torch
import logging

# Create FastAPI app
app = FastAPI()

# Device configuration (CPU by default)
device = torch.device("cpu")

# Directory where the fine-tuned model is stored (inside container: /app/model)
MODEL_DIR = "model"

# Load tokenizer and model at startup
try:
    tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_DIR)
    model.to(device)
    logging.info(f"Loaded tokenizer and model from '{MODEL_DIR}'")
except Exception as e:
    logging.error(f"Error loading model from '{MODEL_DIR}': {e}")
    raise RuntimeError(f"Failed to load model from {MODEL_DIR}: {e}")

# Request schema for code review
class CodeRequest(BaseModel):
    code: str
    max_length: int = 256    # Maximum length of generated output
    num_beams: int = 4       # Number of beams for beam search

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Root endpoint (optional)
@app.get("/")
async def root():
    return {"message": "Code Review Assistant API is running."}

# Code review/generation endpoint
@app.post("/review")
async def review_code(request: CodeRequest):
    """
    Accepts a code snippet and returns the model's review/suggestions as text.
    """
    if not request.code.strip():
        raise HTTPException(status_code=400, detail="`code` field cannot be empty.")

    # Tokenize input code
    inputs = tokenizer(
        request.code,
        return_tensors="pt",
        truncation=True,
        padding="longest",
    ).to(device)

    # Generate output with the fine-tuned model
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

    # Decode the generated tokens back into string
    review_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
    return {"review": review_text}
