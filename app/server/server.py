import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["WANDB_DISABLED"] = "true"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import sys

HERE = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
sys.path.insert(0, PROJECT_ROOT)

import warnings
warnings.filterwarnings('ignore')
import pandas as pd

from model.InstructABSA.data_prep import DatasetLoader
from model.InstructABSA.utils import T5Generator, T5Classifier
from model.instructions import InstructionsHandler
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import List, Tuple
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

task_name = 'joint_task'
experiment_name = 'aspe-absa2'
model_checkpoint = 'kevinscaria/joint_tk-instruct-base-def-pos-neg-neut-combined'
print('Experiment Name: ', experiment_name)
model_out_path = './model/Models'
model_out_path = os.path.join(model_out_path, task_name, f"{model_checkpoint.replace('/', '')}-{experiment_name}")
print('Model output path: ', model_out_path)

_tokenizer: AutoTokenizer | None = None
_model: AutoModelForSeq2SeqLM | None = None
_device = "cuda" if torch.cuda.is_available() else "cpu"

instr = InstructionsHandler()
instr.load_instruction_set2()
bos   = instr.aspe['bos_instruct1']
delim = instr.aspe['delim_instruct']
eos   = instr.aspe['eos_instruct']

# Pydantic schema
class ReviewRequest(BaseModel):
    review: str

class AspectPolarity(BaseModel):
    aspect: str
    polarity: str

class PredictionResponse(BaseModel):
    raw_output: str
    results: List[AspectPolarity]

# Khởi tạo FastAPI
app = FastAPI(
    title="InstructABSA API",
    description="API để phân tích aspect-polarity từ câu review",
)

def load_model():
    print (f"Loading model from {model_out_path}")
    global _tokenizer, _model
    if _model is None or _tokenizer is None:
        t5_exp = T5Generator(model_out_path)
        _tokenizer = t5_exp.tokenizer
        _model = t5_exp.model.to(t5_exp.device)
    return _tokenizer, _model

def absa_inference_single(text: str, bos_instruction: str, delim_instruction: str, eos_instruction: str):
    """
    Thực hiện ABSA inference cho một câu review.
    Trả về tuple (raw_output, list of (aspect, polarity)).
    """
    tokenizer, model = load_model()
    prompt = f"{bos_instruction}{text}{delim_instruction}"
    inputs = tokenizer(prompt, return_tensors='pt', truncation=True, max_length=512)
    inputs = inputs.to(_device)
    outputs = model.generate(
        **inputs,
        max_length=128,
        num_beams=4,
        early_stopping=True,
        use_cache=True
    )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    print("Decoded: ", decoded)
    results = []
    for segment in decoded.split(','):
        if ':' in segment:
            asp, pol = segment.split(':', 1)
            results.append((asp.strip(), pol.strip()))
    return decoded, results

# Endpoint
@app.post("/predict", response_model=PredictionResponse)
def predict(request: ReviewRequest):
    text = request.review.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Review text cannot be empty.")

    raw_out, pairs = absa_inference_single(text, bos, delim, eos)
    # Sử dụng vị trí xuất hiện trong review để sort
    positions = {asp: text.lower().find(asp.lower()) for asp, _ in pairs}
    sorted_pairs = sorted(pairs, key=lambda x: positions.get(x[0], float('inf')))
    result_items = [AspectPolarity(aspect=asp, polarity=pol) for asp, pol in sorted_pairs]

    return PredictionResponse(raw_output=raw_out, results=result_items)

# Endpoint root để kiểm tra
@app.get("/", include_in_schema=False)
def root():
    return {"message": "InstructABSA API is running."}