# RAG Chatbot for SAP MM & CO-PA Data

## Architecture Overview
For numerical SAP data, a standard Vector-based RAG is **not recommended**. Instead, we will use a **Text-to-SQL (NL2SQL)** approach. 

### Why NL2SQL?
1. **Accuracy**: Vector search is "fuzzy". If you ask for "Total Stock Value", a vector DB might return similar rows but won't sum them. SQL will calculate it exactly.
2. **Speed**: DuckDB can query 400,000 rows across 8 tables in milliseconds.
3. **Complex Intent**: It handles joins between tables (e.g., joining `inventory_stock` with `copa_revenue`) better than embeddings.

## Pre-requisites
1. **Python 3.10+**: For the backend logic.
2. **Node.js & npm/yarn**: For the premium frontend.
3. **Ollama**: To run the local LLM (Qwen-2.5 or Llama-3.1).
4. **DuckDB**: For high-performance analytical queries on your CSV files.
5. **FastAPI**: To bridge the LLM and the Frontend.

## Recommended Model
- **Primary Choice**: `qwen2.5:7b` or `llama3.1:8b` (via Ollama).
- **Lightweight Choice**: `qwen2.5:3b` (if hardware is limited).
- **Reasoning**: Generating valid SQL across 8 tables requires a model with strong logical reasoning.

## Next Steps
1. **Data Setup**: Place your 8 CSV files in a `data/` directory.
2. **Backend implementation**:
   - Schema mapping (Tell the LLM about your tables).
   - SQL Generation logic.
   - Result summarization.
3. **Frontend implementation**:
   - Modern Chat UI.
   - Data visualization (Charts for numerical insights).
