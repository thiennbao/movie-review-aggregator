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

from model.InstructABSA.utils import T5Generator
from model.instructions import InstructionsHandler
import torch
from typing import List, Tuple, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import re

_tokenizer = None
_model     = None
_device    = None

task_name = 'joint_task'
experiment_name = 'aspe-absa2'
model_checkpoint = 'PhatLe12344/InstructABSAFineTune-fp16'
print('Model checkpoint from Hugging Face Hub:', model_checkpoint)

instr = InstructionsHandler()
instr.load_instruction_set2()
bos   = instr.aspe['bos_instruct1']
delim = instr.aspe['delim_instruct']
eos   = instr.aspe['eos_instruct']

# Pydantic schema
class ReviewRequest(BaseModel):
    review: str

class UnifiedAspectPolarity(BaseModel):
    aspects: List[str]
    polarities: List[str]
    positions: List[Tuple[int, int]]  # list of (start, end) in content
    content: str

class PredictionResponse(BaseModel):
    raw_output: str
    results: List[UnifiedAspectPolarity]

# Khởi tạo FastAPI
app = FastAPI(
    title="InstructABSA API",
    description="API để phân tích aspect-polarity từ câu review",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)
def load_model():
    global _tokenizer, _model, _device
    if _model is None or _tokenizer is None:
        t5_exp = T5Generator(model_checkpoint, max_new_tokens=128)
        _tokenizer = t5_exp.tokenizer
        _model     = t5_exp.model.to(t5_exp.device)
        _device    = t5_exp.device
    return _tokenizer, _model, _device

# Single inference function
def absa_inference_single(text: str, bos_instruction: str, delim_instruction: str, eos_instruction: str) -> Tuple[str, List[Tuple[str, str]]]:
    tokenizer, model, device = load_model()
    # build prompt
    prompt = f"{bos_instruction}{text}{delim_instruction}{eos_instruction}"
    # tokenize without fixed max length, cap at model capacity
    inputs = tokenizer(
        prompt,
        return_tensors='pt',
        add_special_tokens=True,
        truncation=True,
        max_length=tokenizer.model_max_length
    ).to(device)
    # dynamic max_length: prompt_len + max_new_tokens
    prompt_len = inputs['input_ids'].shape[1]
    max_length = prompt_len + 128
    model.eval()
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_length=max_length,
            num_beams=4,
            early_stopping=True,
            use_cache=True
        )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    # parse aspect:polarity
    results = []
    for seg in decoded.split(','):
        if ':' in seg:
            a, p = seg.split(':', 1)
            results.append((a.strip(), p.strip()))
    return decoded, results

# Endpoint
@app.post("/predict", response_model=PredictionResponse, tags=["absa"], response_model_exclude_none=True)
def predict(request: ReviewRequest) -> PredictionResponse:
    # 1. Read and validate input review text
    text = request.review.strip()
    if not text:
        # Nếu review rỗng, trả về HTTP 400
        raise HTTPException(status_code=400, detail="Review text cannot be empty.")

    # 2. Gọi hàm inference để lấy raw_output và cặp (aspect, polarity)
    raw_out, pairs = absa_inference_single(text, bos, delim, eos)

    # 3. Tách toàn bộ review thành câu con dựa trên dấu . ! ?
    sentence_re = re.compile(r'(?<=[.!?])\s*')
    sentences = sentence_re.split(text)

    # 4. Gom nhóm các cặp theo từng câu (content) và tính vị trí trong content
    grouped: Dict[str, Dict[str, List]] = {}
    for asp, pol in pairs:
        # 4.1. Xác định câu chứa aspect (nếu không tìm thấy thì dùng toàn review)
        content = next((s for s in sentences if asp.lower() in s.lower()), text).strip()
        # 4.2. Tính vị trí start và end của aspect trong câu content
        start = content.lower().find(asp.lower())
        end = start + len(asp) if start != -1 else -1
        # 4.3. Khởi tạo group nếu câu chưa có
        if content not in grouped:
            grouped[content] = {"aspects": [], "polarities": [], "positions": []}
        # 4.4. Thêm aspect, polarity và position vào nhóm
        grouped[content]["aspects"].append(asp)
        grouped[content]["polarities"].append(pol)
        grouped[content]["positions"].append((start, end))

    # 5. Build result list, dedup identical (asp, pol, pos)
    result_items: List[UnifiedAspectPolarity] = []
    for content, data in grouped.items():
        # zip into triples
        triples = list(zip(data["aspects"], data["polarities"], data["positions"]))
        # dedupe while preserving order
        seen = set()
        unique_triples = []
        for asp, pol, pos in triples:
            key = (asp, pol, pos)
            if key not in seen:
                seen.add(key)
                unique_triples.append((asp, pol, pos))
        # sort by start index
        unique_triples.sort(key=lambda x: x[2][0])
        # unzip back
        aspects, polarities, positions = zip(*unique_triples) if unique_triples else ([], [], [])
        result_items.append(
            UnifiedAspectPolarity(
                aspects=list(aspects),
                polarities=list(polarities),
                positions=list(positions),
                content=content
            )
        )

    return PredictionResponse(raw_output=raw_out, results=result_items)

# Endpoint root để kiểm tra
@app.get("/", include_in_schema=False)
def root():
    return {"message": "InstructABSA API is running."}

if __name__ == "__main__":
    print("🧪 Loading model...")
    load_model()
    print("🌱 Successfully")