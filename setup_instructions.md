# Setup & Run Instructions

## 1. Backend Setup
1. Open a terminal in the `backend` folder.
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. **Important**: Place your 8 CSV files in the `data/` folder. Ensure names match:
   - `inventory_stock.csv`
   - `vendor_master.csv`
   - `pr_data.csv`
   - `po_transaction.csv`
   - `copa_margin_synthetic.csv`
   - `copa_cost_variance.csv`
   - `copa_revenue.csv`
   - `copa_characteristics.csv`
5. Ensure **Ollama** is running with the model:
   ```bash
   ollama run qwen2.5:7b
   ```
6. Start the backend:
   ```bash
   python main.py
   ```

## 2. Frontend Setup
1. Open a terminal in the `frontend` folder.
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the dev server:
   ```bash
   npm run dev
   ```
4. Open the displayed URL (usually `http://localhost:3000`).

## 3. High Performance Tips
- **Memory**: With 400,000 rows, DuckDB is very efficient. If your system has at least 8GB RAM, it will be instantaneous.
- **Model Choice**: If `qwen2.5:7b` is slow, try `qwen2.5:3b`. For the highest accuracy, use `llama3.1:8b`.
- **SQL Accuracy**: The system uses the column names and descriptions provided in `backend/schema.py`. Ensure your CSV headers match these column names.
