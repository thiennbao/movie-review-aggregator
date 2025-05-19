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

task_name = 'aoste'
experiment_name = 'aspe-absa2'
model_checkpoint = 'PhatLe12344/AOSTE_InstructABSA'
print('Model checkpoint from Hugging Face Hub:', model_checkpoint)

instr = InstructionsHandler()
instr.load_instruction_set2()
bos   = instr.aoste['bos_instruct1']
delim = instr.aoste['delim_instruct']
eos   = instr.aoste['eos_instruct']

# Pydantic schema
class ReviewRequest(BaseModel):
    review: str

class UnifiedAspectPolarity(BaseModel):
    aspects: List[str]
    opinions: List[str]
    polarities: List[str]
    positions_aspects: List[Tuple[int, int]]  # list of (start, end) in content
    positions_opinions: List[Tuple[int, int]]  # list of (start, end) in content
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

def get_word_positions_1idx(content: str, phrase: str) -> Tuple[int, int]:
    """
    Trả về vị trí start/end của `phrase` trong `content`,
    đếm theo từ (space-separated), 1-based index.
    Nếu không tìm thấy, trả về (-1, -1).
    """
    words = content.split()
    phrase_words = phrase.split()

    for idx in range(len(words) - len(phrase_words) + 1):
        if words[idx:idx+len(phrase_words)] == phrase_words:
            # Chuyển sang 1-based:
            return idx + 1, idx + len(phrase_words)
    return -1, -1

# Single inference function
def absa_inference_single(text: str, bos_instruction: str, delim_instruction: str, eos_instruction: str) -> Tuple[str, List[Tuple[str, str, str]]]:
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
            num_return_sequences=4,
            early_stopping=True,
            use_cache=True
        )
    decoded = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
    print("DEBUG decoded:", decoded)
    # parse aspect:polarity
    results: List[Tuple[str, str, str]] = []
    for seg in decoded.split(","):
        parts = [p.strip() for p in seg.split(":")]
        # Chỉ xử lý khi đúng 3 phần
        if len(parts) == 3:
            aspect, opinion, polarity = parts
            results.append((aspect, opinion, polarity))

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
    raw_output, triples = absa_inference_single(text, bos, delim, eos)

    # 3. Tách toàn bộ review thành câu con dựa trên dấu . ! ?
    sentence_re = re.compile(r'(?<=[.!?])\s*')
    sentences = sentence_re.split(text)

    # 4. Gom nhóm các cặp theo từng câu (content) và tính vị trí trong content
    grouped: Dict[str, Dict[str, List]] = {}
    for asp, opin, pol in triples:
        # 4.1. Xác định câu chứa aspect (nếu không tìm thấy thì dùng toàn review)
        content = next(
            (s for s in sentences if asp.lower() in s.lower() and opin.lower() in s.lower()),
            text
        ).strip()
        if content not in grouped:
            grouped[content] = {
                "aspects": [], "opinions": [], "polarities": [],
                "pos_aspect": [], "pos_opin": []
            }
        # 4.2. Tính vị trí start và end của aspect trong câu content
        start_asp, end_asp = get_word_positions_1idx(content, asp)
        start_op, end_op = get_word_positions_1idx(content, opin)
        # 4.3. Khởi tạo group nếu câu chưa có

        # 4.4. Thêm aspect, polarity và position vào nhóm
        grouped[content]["aspects"].append(asp)
        grouped[content]["opinions"].append(opin)
        grouped[content]["polarities"].append(pol)
        grouped[content]["pos_aspect"].append((start_asp, end_asp))
        grouped[content]["pos_opin"].append((start_op, end_op))

    # 5. Build result list, dedup identical (asp, pol, pos)
    results: List[UnifiedAspectPolarity] = []
    for content, data in grouped.items():
        # dedupe while preserving order
        seen = set()
        unique = []
        for a, o, p, pa, po in zip(
                data["aspects"], data["opinions"], data["polarities"],
                data["pos_aspect"], data["pos_opin"]
        ):
            key = (a, o, p, pa, po)
            if key not in seen:
                seen.add(key)
                unique.append((a, o, p, pa, po))
        # sort by start index
        unique.sort(key=lambda x: x[3][0] if x[3][0] >= 0 else float('inf'))
        # unzip back
        aspects, opinions, polarities, pos_as, pos_op = zip(*unique) if unique else ([], [], [], [], [])
        results.append(
            UnifiedAspectPolarity(
                aspects=list(aspects),
                opinions=list(opinions),
                polarities=list(polarities),
                positions_aspects=list(pos_as),
                positions_opinions=list(pos_op),
                content=content
            )
        )

    return PredictionResponse(raw_output=raw_output, results=results)

# Endpoint root để kiểm tra
@app.get("/", include_in_schema=False)
def root():
    return {"message": "InstructABSA API is running."}