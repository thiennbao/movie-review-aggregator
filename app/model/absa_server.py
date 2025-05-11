# services/server/absa_server.py
import os

os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["WANDB_DISABLED"] = "true"
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TF_USE_LEGACY_KERAS"] = "1"
os.environ["HF_HUB_DISABLE_XET"] = "1"
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' # Đặt level log thấp hơn

import sys

HERE = os.path.dirname(__file__)
# PROJECT_ROOT = os.path.abspath(os.path.join(HERE, os.pardir)) # Dự án gốc có thể ở cấp cao hơn
# sys.path.insert(0, PROJECT_ROOT) # Dòng này có thể gây lỗi nếu PROJECT_ROOT không đúng
# Hãy đảm bảo thư mục 'model' chứa InstructABSA có thể được import

import warnings
warnings.filterwarnings('ignore')
# import pandas as pd # Pandas có vẻ không dùng trong API này, có thể xóa

# --- Import model và tokenizer từ transformers ---
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# --- Import các thành phần từ model.InstructABSA ---
# Đảm bảo thư mục 'model' và cấu trúc bên trong nó có thể import được từ nơi chạy absa_server.py
# Ví dụ, nếu 'model' nằm ngang hàng với thư mục 'app', bạn cần điều chỉnh sys.path
# hoặc cách chạy script.
# Dòng sys.path.insert(0, PROJECT_ROOT) có thể cần sửa PROJECT_ROOT
# Giả định các import này đúng nếu thư mục 'model' có thể truy cập.
from model.InstructABSA.utils import T5Generator # <- Chỉ cần T5Generator

# Import InstructionsHandler và instructions
from model.instructions import InstructionsHandler


import torch # Import torch
from typing import List, Tuple, Dict # Import typing
from fastapi import FastAPI, HTTPException # Import FastAPI và HTTPException
from pydantic import BaseModel # Import BaseModel
import re # Import re

task_name = 'joint_task'
experiment_name = 'aspe-absa2'
model_checkpoint = 'kevinscaria/joint_tk-instruct-base-def-pos-neg-neut-combined'
print('Experiment Name: ', experiment_name)
model_out_path = './model/Models' # <-- Đảm bảo đường dẫn này đúng từ nơi chạy absa_server.py
model_out_path = os.path.join(model_out_path, task_name, f"{model_checkpoint.replace('/', '')}-{experiment_name}")
print('Model output path: ', model_out_path)

# --- Định nghĩa các biến global cho model và trạng thái tải ---
_tokenizer: AutoTokenizer | None = None
_model: AutoModelForSeq2SeqLM | None = None
_model_loaded = False # <-- Khai báo và khởi tạo biến global trạng thái


# Xác định thiết bị
if torch.backends.mps.is_available():
    _device = "mps"
elif torch.cuda.is_available():
    _device = "cuda"
else:
    _device = "cpu"
print(f"Using device: {_device}")


# Tải instructions Handler và instructions ngay khi khởi tạo module
# Có thể thêm try/except nếu load instructions cũng có thể lỗi
try:
    instr = InstructionsHandler()
    instr.load_instruction_set2() # <-- Kiểm tra hàm này có đúng không, code cũ dùng load_instruction_set2
    # instr.load_instructions() # Code cũ dùng load_instructions
    # Đảm bảo tên hàm load instruction là đúng với phiên bản InstructionsHandler bạn dùng
    bos   = instr.aspe['bos_instruct1']
    delim = instr.aspe['delim_instruct']
    eos   = instr.aspe['eos_instruct']
    print("Instructions loaded successfully.")
except Exception as e:
    print(f"Error loading Instructions: {e}. ABSA inference might fail.")
    # Quyết định xử lý lỗi load instructions (ví dụ: API không chạy nếu instructions lỗi)
    # raise # Có thể raise lỗi để server không khởi động nếu instructions là bắt buộc


# --- Định nghĩa các lớp Pydantic Model (ĐÃ SẮP XẾP LẠI) ---
# Sắp xếp từ lớp đơn giản nhất được dùng trong các lớp khác
# 1. Model cho một phần tử kết quả khía cạnh
class ApiAspectResultItem(BaseModel):
     aspect: str
     sentiment: str # Hoặc kiểu dữ liệu phù hợp với output API của bạn
     confidence: float | None # <-- Confidence có thể là None nếu model không trả về

# 2. Model cho kết quả dự đoán của MỘT review
class ApiReviewPrediction(BaseModel):
     review_id: str # ID của review này (từ input Celery)
     aspects: List[ApiAspectResultItem] # Danh sách các khía cạnh và sentiment cho review này

# 3. Model cho toàn bộ body phản hồi của API (danh sách kết quả cho tất cả review trong batch)
class ApiBatchPredictionResponse(BaseModel):
     results: List[ApiReviewPrediction]

# Model cho một phần tử review trong danh sách request body gửi từ Celery task
class CeleryReviewItem(BaseModel):
    review_id: str # ID của review (từ Celery task)
    text: str # Nội dung review (từ Celery task)

# --- Các Model CŨ (Đã xóa để làm code sạch) ---
# Xóa các lớp ReviewRequest, UnifiedAspectPolarity, PredictionResponse nếu không dùng

# Khởi tạo FastAPI
app = FastAPI(
    title="InstructABSA API",
    description="API để phân tích aspect-polarity từ câu review",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# --- Event handler tải model khi server khởi động ---
@app.on_event("startup")
def on_startup():
    print("FastAPI app starting up, loading model...")
    # Hàm load_model sẽ tự xử lý việc set cờ hiệu _model_loaded
    try:
        load_model() # Gọi hàm tải model
        print("Model loading complete.")
    except Exception as e:
        # Bắt lỗi khi tải model tại startup
        print(f"FATAL ERROR during model loading at startup: {e}")
        # FastAPI sẽ không khởi động hoàn toàn nếu startup event handler raise exception
        # hoặc nếu bạn không muốn server chạy khi model lỗi, có thể raise lại hoặc sys.exit()
        # Để API trả về 503 khi được gọi, chỉ cần cờ hiệu _model_loaded là False


def load_model():
    """Tải tokenizer và model T5."""
    print (f"Attempting to load model from {model_out_path}")
    # --- Truy cập các biến global ---
    global _tokenizer, _model, _model_loaded # <-- Truy cập tất cả các biến global liên quan

    # Kiểm tra nếu model đã tải rồi và cờ hiệu thành công đã bật
    if _model is not None and _tokenizer is not None and _model_loaded:
         print("Model and Tokenizer already loaded.")
         return # Thoát sớm nếu đã tải thành công

    _model_loaded = False # <-- Đặt cờ hiệu thất bại MẶC ĐỊNH

    try:
        # --- Logic tải model ---
        # T5Generator cần đường dẫn tới model
        t5_exp = T5Generator(model_out_path)
        _tokenizer = t5_exp.tokenizer
        _model = t5_exp.model.to(_device) # Chuyển model sang thiết bị đã xác định

        # --- Đặt cờ hiệu thành công CHỈ KHI tải xong ---
        _model_loaded = True # <-- Đặt cờ hiệu thành công
        print("Model and Tokenizer loaded successfully.")

    except FileNotFoundError as e:
        print(f"Error loading model files: {e}. Ensure path {model_out_path} is correct.")
        _model_loaded = False # Đảm bảo cờ hiệu là False
        # raise # Tùy chọn raise lỗi để startup event thất bại

    except Exception as e:
        print(f"An unexpected error occurred during model loading: {e}")
        _model_loaded = False # Đảm bảo cờ hiệu là False
        # raise # Tùy chọn raise lỗi để startup event thất bại


# Hàm thực hiện inference cho một câu review đơn lẻ
# Giữ nguyên hàm này, nó sẽ sử dụng global _tokenizer và _model
def absa_inference_single(text: str, bos_instruction: str, delim_instruction: str, eos_instruction: str):
    """
    Thực hiện ABSA inference cho một câu review đơn lẻ.
    Trả về tuple (raw_output_string, list of (aspect_str, polarity_str)).
    """
    global _tokenizer, _model # <-- Truy cập biến global

    # Kiểm tra nếu model chưa tải thành công (dùng cờ hiệu _model_loaded)
    global _model_loaded # <-- Truy cập cờ hiệu
    if not _model_loaded:
         print("Error: Model not loaded for inference.")
         # Raise lỗi HTTPException để API trả về 503 nếu endpoint được gọi trước khi model tải
         raise HTTPException(status_code=503, detail="Model is not loaded for inference.") # Service Unavailable

    # Kiểm tra _tokenizer và _model cũng là cách tốt
    if _tokenizer is None or _model is None:
         print("Error: Tokenizer or Model instance is None despite _model_loaded being True.")
         raise HTTPException(status_code=503, detail="Model instances are None.") # Service Unavailable

    try:
        # --- Logic inference sử dụng _tokenizer và _model ---
        prompt = f"{bos_instruction}{text}{delim_instruction}"
        inputs = _tokenizer(prompt, return_tensors='pt', truncation=True, max_length=512)
        inputs = {k: v.to(_model.device) for k, v in inputs.items()} # Chuyển inputs sang thiết bị

        # Sử dụng no_grad() để tiết kiệm bộ nhớ và tăng tốc inference
        with torch.no_grad():
            outputs = _model.generate(
                **inputs,
                max_length=128,
                num_beams=4,
                early_stopping=True,
                use_cache=True
            )
        decoded = _tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
        # print("Decoded: ", decoded) # Tắt log này nếu quá nhiều output

        # Phân tích output format "aspect1:polarity1, aspect2:polarity2, ..."
        results = [] # list of (aspect_str, polarity_str)
        for segment in decoded.split(','):
            segment = segment.strip() # Xóa khoảng trắng ở đầu/cuối segment
            if ':' in segment:
                parts = segment.split(':', 1)
                if len(parts) == 2: # Đảm bảo split thành 2 phần
                     asp, pol = parts
                     results.append((asp.strip(), pol.strip()))
                # Có thể thêm logic xử lý các segment không có ':' nếu cần
        return decoded, results # Trả về raw output và danh sách (aspect, polarity)

    except Exception as e:
        print(f"Error during ABSA inference for text: '{text[:50]}...': {e}")
        # Xử lý lỗi inference: Có thể trả về kết quả rỗng hoặc thông báo lỗi
        # Trả về kết quả rỗng cho review lỗi là cách tốt cho batch processing
        return f"Error during inference: {e}", [] # Trả về thông báo lỗi raw output và danh sách rỗng


# Endpoint chính nhận batch review từ Celery task
# Sử dụng endpoint /analyze_reviews để khớp với config.py nếu bạn chưa sửa config.py
# Nếu bạn đã sửa config.py để gọi /predict, hãy dùng "/predict" ở đây
@app.post("/analyze_reviews", response_model=ApiBatchPredictionResponse, tags=["absa"], response_model_exclude_none=True)
# Endpoint giờ nhận list CeleryReviewItem
async def analyze_reviews_batch(reviews_list: List[CeleryReviewItem]) -> ApiBatchPredictionResponse:
    """
    Nhận một danh sách reviews (batch) và trả về kết quả ABSA cho từng review.
    """
    # --- Kiểm tra cờ hiệu model đã tải thành công chưa ---
    global _model_loaded # <-- Truy cập cờ hiệu
    if not _model_loaded:
         print("Error: API endpoint received request but model is not loaded (check startup logs).")
         # Trả về lỗi 503 nếu model chưa tải được
         raise HTTPException(status_code=503, detail="ABSA model failed to load during startup.") # Service Unavailable


    print(f"Received batch request with {len(reviews_list)} reviews for analysis.")
    batch_results: List[ApiReviewPrediction] = [] # Danh sách kết quả cho batch

    # --- Logic xử lý batch reviews ---
    # Duyệt qua danh sách reviews và xử lý TỪNG review
    for review_item in reviews_list:
         # Đảm bảo review_item là instance của CeleryReviewItem và không rỗng
         if not isinstance(review_item, CeleryReviewItem) or not review_item.review_id or not review_item.text:
             print(f"Skipping invalid review item in batch: {review_item}")
             continue # Bỏ qua item không hợp lệ

         text = review_item.text.strip()
         review_id = review_item.review_id

         # Xử lý review rỗng sau khi strip()
         if not text:
             print(f"Skipping empty review after strip for ID: {review_id}")
             # Có thể thêm ApiReviewPrediction rỗng vào batch_results nếu muốn hiển thị review ID này
             # batch_results.append(ApiReviewPrediction(review_id=review_id, aspects=[]))
             continue # Bỏ qua review rỗng

         # Gọi hàm inference cho TỪNG review item
         # absa_inference_single trả về (raw_output, list of (aspect_str, polarity_str))
         raw_out, pairs = absa_inference_single(text, bos, delim, eos) # <-- Gọi hàm inference đơn lẻ

         # Chuyển đổi kết quả (aspect_str, polarity_str) sang format ApiAspectResultItem
         # và thu thập vào danh sách cho review hiện tại
         aspect_results_for_review: List[ApiAspectResultItem] = []
         # Duyệt qua các cặp (aspect, polarity) từ inference
         for asp_str, pol_str in pairs:
              if not asp_str or not pol_str: # Bỏ qua nếu aspect hoặc polarity rỗng
                  print(f"Skipping invalid aspect/polarity pair for review ID {review_id}: ('{asp_str}', '{pol_str}')")
                  continue

              # Mapping polarity_str sang sentiment_str ('Positive', 'Negative', 'Neutral')
              sentiment_mapped = "Neutral" # Default
              pol_str_lower = pol_str.lower()
              if 'pos' in pol_str_lower:
                  sentiment_mapped = "Positive"
              elif 'neg' in pol_str_lower:
                  sentiment_mapped = "Negative"
              # Các giá trị polarity khác sẽ map thành Neutral

              # Confidence: Model inference_single không trả về confidence. Gửi None.
              confidence_score = None # Sử dụng None

              # Thêm kết quả khía cạnh vào danh sách cho review hiện tại
              aspect_results_for_review.append(
                  ApiAspectResultItem(
                      aspect=asp_str.strip(), # Đảm bảo aspect không có khoảng trắng thừa
                      sentiment=sentiment_mapped,
                      confidence=confidence_score
                  )
              )


         # Thêm kết quả của review này (bao gồm review_id và danh sách khía cạnh)
         # vào danh sách kết quả batch TỔNG THỂ
         batch_results.append(
             ApiReviewPrediction(
                 review_id=review_id, # Sử dụng review_id từ input
                 aspects=aspect_results_for_review # Danh sách khía cạnh cho review này
             )
         )
    # --- Kết thúc vòng lặp xử lý batch ---

    # Trả về phản hồi batch
    # Format: {"results": [ApiReviewPrediction, ApiReviewPrediction, ...]}
    print(f"Finished processing batch. Returning {len(batch_results)} review results.")
    return ApiBatchPredictionResponse(results=batch_results)


# Endpoint root (Giữ nguyên)
@app.get("/", include_in_schema=False)
def root():
    return {"message": "InstructABSA API is running."}

# Main entry point để chạy server (Giữ nguyên)
if __name__ == "__main__":
    import uvicorn
    # Đảm bảo tên module và app instance là đúng
    uvicorn.run("absa_server:app", host="0.0.0.0", port=8000) # <-- Đảm bảo tên module là absa_server