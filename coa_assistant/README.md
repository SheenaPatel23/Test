# 🧾 Chart of Accounts Assistant

An interactive Streamlit assistant for matching invoice descriptions to the appropriate Chart of Accounts.

## 🚀 Features
- Upload your own Chart of Accounts CSV
- Query using natural language (e.g., "invoice for legal consulting")
- Semantic matching using sentence-transformers and FAISS
- Optional reasoning using llama3 (via `llama-cpp-python`)
- Admin feedback logging (helpful / not helpful)

## 🛠️ Getting Started

```bash
pip install -r requirements.txt
streamlit run app.py
```

### llama3 Model
Download a llama3 model (e.g., `llama-3-8b-instruct.Q4_K_M.gguf`) and place it in a `models/` directory.

