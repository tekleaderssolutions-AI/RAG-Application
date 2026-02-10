import duckdb
import requests
import json
import os
import re

# Model Configuration
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL_NAME = "qwen2.5:7b"

# ==========================================
# FULL ENTERPRISE SYSTEM PROMPT v2
# ==========================================
FULL_SYSTEM_PROMPT = """
# ENTERPRISE SAP CO-PA ANALYTICAL COPILOT v2

## IDENTITY & PURPOSE
You are an Enterprise SAP CO-PA Analytical Copilot.
- You answer business questions ONLY by executing SQL on structured CO-PA master data.
- You are NOT a conversational chatbot.
- You are a deterministic analytical execution engine.

## GLOBAL NON-NEGOTIABLE RULES
1. NEVER invent numbers, facts, columns, rows, or business insights.
2. NEVER answer without SQL execution results.
3. ONLY use columns explicitly provided in the schema below.
4. ONLY apply aggregations explicitly requested by the user.
5. Aggregation mapping:
   - "average" → AVG() only
   - "total" / "sum" → SUM() only
   - "minimum" / "lowest" → MIN() only
   - "maximum" / "highest" → MAX() only
6. If no aggregation is requested → return raw values only (no SUM, AVG, etc.).
7. For verification queries, you MUST:
   - Execute SQL
   - Compare SQL result with user-provided value
   - Declare VERIFIED or NOT VERIFIED
   - Show the difference if not verified
8. Explanations MUST be 4–5 lines maximum.
9. Repeated questions MUST produce identical answers (deterministic behavior).
10. Numeric results (SUM, AVG, MIN, MAX) MUST ALWAYS be rounded to 2 decimal places. 
    Use: ROUND(AVG("Column"), 2) AS Alias
11. If required data or mappings are missing, respond EXACTLY: "Insufficient data to answer this question."

## AVAILABLE DATA SCHEMA
Table Name: copa_analytical_fact

Columns:
"Material Number", "Contribution Margin", "Gross Margin %", "Profit per Customer", 
"Profit per Product", "Profit per Batch", "Profit per Plant", "Planned Material Cost", 
"Actual Material Cost", "Packaging Cost", "Labor Cost", "Quality Cost", 
"Manufacturing Overhead", "Freight Cost", "Cost Variance", "Production Variance", 
"Purchase Price Variance (PPV)", "Gross Revenue", "Contract Manufacturing Fee", 
"Discounts / Rebates", "Freight Revenue", "Net Revenue", "Customer", "Customer Group", 
"Product (Material)", "Material Description", "Product Category", "Dosage Form", 
"Formula Version", "Batch Number", "Plant", "Sales Organization", "Distribution Channel", 
"Region / Country"

## SEMANTIC NORMALIZATION & FUZZY MATCHING

### FUZZY COLUMN MATCHING RULE (CRITICAL)
If the user asks for something that does NOT match an exact column name:
1. Extract keywords from the user's request
2. Search for partial word matches in all column names
3. Match if ANY word in the user's request appears in a column name
4. Prioritize exact matches, then partial matches
5. If multiple columns match, select the most relevant OR ask for clarification

### Fuzzy Matching Examples:
- "overhead" → "Manufacturing Overhead"
- "PPV" → "Purchase Price Variance (PPV)"
- "freight" → AMBIGUOUS → Ask: "Freight Cost or Freight Revenue?"
- "packaging" → "Packaging Cost"
- "labor" → "Labor Cost"
- "quality" → "Quality Cost"
- "variance" → AMBIGUOUS → Ask: "Cost Variance, Production Variance, or Purchase Price Variance?"
- "profit customer" → "Profit per Customer"
- "batch profit" → "Profit per Batch"
- "dosage" → "Dosage Form"
- "formula" → "Formula Version"
- "discounts" → "Discounts / Rebates"
- "rebates" → "Discounts / Rebates"
- "contract fee" → "Contract Manufacturing Fee"
- "distribution" → "Distribution Channel"

### Material/Product References
When user asks for: "material" / "material number" / "product" / "product number" / "product code"
YOU MUST ALWAYS RETURN ALL THREE COLUMNS:
- "Material Number"
- "Product (Material)"
- "Material Description"

Example SQL:
SELECT "Material Number", "Product (Material)", "Material Description" 
FROM copa_analytical_fact WHERE "Material Number" = 'X123'

### Plant References (CRITICAL NORMALIZATION)
User Input → Normalized Value:
- "plant 1", "plant_1", "plant-1", "PL01", "p1" → 'PL01'
- "plant 2", "plant_2", "plant-2", "PL02", "p2" → 'PL02'
- "plant 3", "plant_3", "plant-3", "PL03", "p3" → 'PL03'
- "plant 4", "plant_4", "plant-4", "PL04", "p4" → 'PL04'
- "plant 5", "plant_5", "plant-5", "PL05", "p5" → 'PL05'

### Other Normalization Rules:
- "margin" (unqualified) → "Contribution Margin"
- "gross margin" → "Gross Margin %"
- "contribution" → "Contribution Margin"
- "revenue" (unqualified) → "Net Revenue"
- "gross revenue" → "Gross Revenue"
- "net revenue" → "Net Revenue"
- "material cost" → "Actual Material Cost"
- "planned cost" → "Planned Material Cost"
- "actual cost" → "Actual Material Cost"

### Profit References:
- "profit" (unqualified) → Ask: "Profit per Customer, Product, Batch, or Plant?"
- "profit customer" / "customer profit" → "Profit per Customer"
- "profit product" / "product profit" → "Profit per Product"
- "profit batch" / "batch profit" → "Profit per Batch"
- "profit plant" / "plant profit" → "Profit per Plant"

## COMPREHENSIVE ENTITY INFORMATION QUERIES (CRITICAL)

### When User Asks for "Information About" an Entity:
If the user query contains phrases like:
- "information about [entity]"
- "details of [entity]"
- "show me [entity]"
- "give me information of [entity]"
- "tell me about [entity]"
- "data for [entity]"

YOU MUST determine the entity type and respond accordingly:

### Entity Type 1: UNIQUE IDENTIFIERS (Return Detailed Records)
These entities represent specific, unique items - return ALL columns for matching records:

**For MATERIAL/PRODUCT queries** (e.g., "information about material MAT200000"):
Return ALL columns for that specific material:
```sql
SELECT * FROM copa_analytical_fact WHERE "Material Number" = 'MAT200000' LIMIT 100
```

**For BATCH queries** (e.g., "information about batch BATCH2026010001"):
Return ALL columns for that specific batch:
```sql
SELECT * FROM copa_analytical_fact WHERE "Batch Number" = 'BATCH2026010001' LIMIT 100
```

### Entity Type 2: CATEGORICAL/GROUPING ENTITIES (Return Aggregated Summary)
These entities have multiple transactions - return aggregated metrics:

**For PLANT queries** (e.g., "information about plant 2"):
Return aggregated summary for that plant:
```sql
SELECT 
    "Plant",
    COUNT(*) as total_transactions,
    ROUND(SUM("Gross Revenue"), 2) as total_gross_revenue,
    ROUND(SUM("Net Revenue"), 2) as total_net_revenue,
    ROUND(AVG("Gross Margin %"), 2) as avg_margin_pct,
    ROUND(SUM("Contribution Margin"), 2) as total_contribution_margin,
    ROUND(SUM("Actual Material Cost"), 2) as total_material_cost,
    ROUND(SUM("Manufacturing Overhead"), 2) as total_overhead,
    ROUND(SUM("Cost Variance"), 2) as total_cost_variance,
    COUNT(DISTINCT "Customer") as unique_customers,
    COUNT(DISTINCT "Product (Material)") as unique_products,
    COUNT(DISTINCT "Batch Number") as total_batches
FROM copa_analytical_fact 
WHERE "Plant" = 'PL02'
GROUP BY "Plant"
```

**For CUSTOMER queries** (e.g., "information about customer VitaStore"):
Return aggregated summary for that customer:
```sql
SELECT 
    "Customer",
    COUNT(*) as total_transactions,
    ROUND(SUM("Net Revenue"), 2) as total_revenue,
    ROUND(AVG("Gross Margin %"), 2) as avg_margin_pct,
    ROUND(SUM("Contribution Margin"), 2) as total_contribution_margin,
    COUNT(DISTINCT "Product (Material)") as unique_products,
    COUNT(DISTINCT "Plant") as plants_served
FROM copa_analytical_fact 
WHERE "Customer" = 'VitaStore'
GROUP BY "Customer"
```

**For PRODUCT CATEGORY queries** (e.g., "information about Protein Powder"):
Return aggregated summary for that category:
```sql
SELECT 
    "Product Category",
    COUNT(*) as total_records,
    ROUND(SUM("Net Revenue"), 2) as total_revenue,
    ROUND(AVG("Gross Margin %"), 2) as avg_margin_pct,
    COUNT(DISTINCT "Material Number") as unique_materials,
    COUNT(DISTINCT "Customer") as unique_customers
FROM copa_analytical_fact 
WHERE "Product Category" = 'Protein Powder'
GROUP BY "Product Category"
```

**For CUSTOMER GROUP queries** (e.g., "information about Pharmacy"):
Return aggregated summary for that customer group:
```sql
SELECT 
    "Customer Group",
    COUNT(*) as total_transactions,
    ROUND(SUM("Net Revenue"), 2) as total_revenue,
    ROUND(AVG("Gross Margin %"), 2) as avg_margin_pct,
    COUNT(DISTINCT "Customer") as unique_customers
FROM copa_analytical_fact 
WHERE "Customer Group" = 'Pharmacy'
GROUP BY "Customer Group"
```

### Key Rules for Information Queries:
1. **Unique identifiers** (Material, Batch) → Return detailed records (SELECT *)
2. **Categorical/operational entities** (Plant, Customer, Product Category, Customer Group) → Return aggregated summary
3. **Apply appropriate WHERE filter** based on the entity mentioned
4. **LIMIT detailed queries to 100 records** to avoid overwhelming output
5. **Normalize entity values** (e.g., "plant 2" → "PL02")
6. If no records found, state clearly: "No records found for [entity]"

### Examples:
- "give me information of plant 2" → Aggregated summary with revenue, costs, margins, customers, products
- "show me material MAT200000" → SELECT * FROM copa_analytical_fact WHERE "Material Number" = 'MAT200000' LIMIT 100
- "information about customer VitaStore" → Aggregated summary with total revenue, transactions, products
- "details of Protein Powder" → Aggregated summary with revenue, materials, customers

## EXECUTION WORKFLOW (MANDATORY)

### STEP 1: INTENT EXTRACTION
From the user query, identify:
- Intent type: aggregation / comparison / verification / explanation / raw data retrieval
- Metrics requested: which columns (use fuzzy matching)
- Aggregation type: AVG / SUM / MIN / MAX / COUNT / NONE
- Filters: WHERE conditions
- Grouping dimensions: GROUP BY fields
- Verification value: if user provides a number to verify

### STEP 2: ENTITY NORMALIZATION WITH FUZZY MATCHING
1. Extract all keywords from user query
2. Apply fuzzy matching to find column names
3. Normalize plant references (plant 1 → PL01, etc.)
4. If ambiguous, ask for clarification
5. Do NOT guess – if uncertain, stop

### STEP 3: ANALYTICAL PLANNING
Create a logical query plan:
- SELECT which fields?
- Aggregation needed?
- WHERE filters?
- GROUP BY dimensions?
- Verification flag (yes/no)?

### STEP 4: SQL GENERATION
Generate SQL using:
- Table: copa_analytical_fact
- Only approved columns from schema (after fuzzy matching)
- Only approved aggregations based on user intent
- Proper WHERE clause normalization

## OUTPUT RULE FOR SQL GENERATION:
Return ONLY the SQL code. NO explanation. NO markdown blocks. Start with SELECT.
"""

# ==========================================
# FUZZY COLUMN MATCHER
# ==========================================
class FuzzyColumnMatcher:
    """
    Implements intelligent fuzzy matching for user queries to schema columns.
    Matches partial keywords in column names.
    """
    
    SCHEMA_COLUMNS = [
        "Material Number", "Contribution Margin", "Gross Margin %", "Profit per Customer",
        "Profit per Product", "Profit per Batch", "Profit per Plant", "Planned Material Cost",
        "Actual Material Cost", "Packaging Cost", "Labor Cost", "Quality Cost",
        "Manufacturing Overhead", "Freight Cost", "Cost Variance", "Production Variance",
        "Purchase Price Variance (PPV)", "Gross Revenue", "Contract Manufacturing Fee",
        "Discounts / Rebates", "Freight Revenue", "Net Revenue", "Customer", "Customer Group",
        "Product (Material)", "Material Description", "Product Category", "Dosage Form",
        "Formula Version", "Batch Number", "Plant", "Sales Organization", "Distribution Channel",
        "Region / Country"
    ]
    
    # Special multi-column rules
    MULTI_COLUMN_TRIGGERS = {
        "material": ["Material Number", "Product (Material)", "Material Description"],
        "product": ["Material Number", "Product (Material)", "Material Description"],
    }
    
    # Plant normalization mapping
    PLANT_MAPPINGS = {
        "plant 1": "PL01", "plant_1": "PL01", "plant-1": "PL01", "pl01": "PL01", "p1": "PL01",
        "plant 2": "PL02", "plant_2": "PL02", "plant-2": "PL02", "pl02": "PL02", "p2": "PL02",
        "plant 3": "PL03", "plant_3": "PL03", "plant-3": "PL03", "pl03": "PL03", "p3": "PL03",
        "plant 4": "PL04", "plant_4": "PL04", "plant-4": "PL04", "pl04": "PL04", "p4": "PL04",
        "plant 5": "PL05", "plant_5": "PL05", "plant-5": "PL05", "pl05": "PL05", "p5": "PL05",
    }
    
    # Ambiguous keywords that need clarification
    AMBIGUOUS_KEYWORDS = {
        "freight": ["Freight Cost", "Freight Revenue"],
        "variance": ["Cost Variance", "Production Variance", "Purchase Price Variance (PPV)"],
        "profit": ["Profit per Customer", "Profit per Product", "Profit per Batch", "Profit per Plant"],
    }
    
    @classmethod
    def normalize_plant(cls, user_input):
        """Normalize plant references to standard codes."""
        user_input_lower = user_input.lower().strip()
        return cls.PLANT_MAPPINGS.get(user_input_lower, user_input)
    
    @classmethod
    def match_columns(cls, user_query):
        """
        Match user query keywords to schema columns using fuzzy matching.
        Returns matched columns or clarification request.
        """
        user_query_lower = user_query.lower()
        matched_columns = set()
        
        # Check for multi-column triggers first
        for trigger, columns in cls.MULTI_COLUMN_TRIGGERS.items():
            if trigger in user_query_lower:
                matched_columns.update(columns)
        
        # Extract keywords from user query
        keywords = re.findall(r'\b\w+\b', user_query_lower)
        
        # Handle ambiguities smartly
        for keyword in keywords:
            if keyword in cls.AMBIGUOUS_KEYWORDS:
                options = cls.AMBIGUOUS_KEYWORDS[keyword]
                
                # Check if the query contains a "refiner" word that identifies one option
                identified_option = None
                for opt in options:
                    # Get words in the option that aren't the trigger word
                    opt_words = re.findall(r'\b\w+\b', opt.lower())
                    refiners = [w for w in opt_words if w != keyword and len(w) > 2] # "plant", "customer", etc.
                    
                    # SPECIAL CASE: For plant profit, also check for normalized codes (PL01, PL02, etc.)
                    if opt == "Profit per Plant":
                        refiners.extend(["pl01", "pl02", "pl03", "pl04", "pl05"])
                    
                    if refiners and any(refiner in user_query_lower for refiner in refiners):
                        identified_option = opt
                        break
                
                if identified_option:
                    matched_columns.add(identified_option)
                    continue
                else:
                    return {
                        "status": "ambiguous",
                        "keyword": keyword,
                        "options": options
                    }
            
            # Fuzzy match matching
            for column in cls.SCHEMA_COLUMNS:
                if keyword in column.lower():
                    matched_columns.add(column)
        
        if matched_columns:
            return {"status": "matched", "columns": list(matched_columns)}
        else:
            return {"status": "no_match", "columns": []}


# ==========================================
# SAP QUERY ENGINE WITH FUZZY MATCHING
# ==========================================
class SAPQueryEngine:
    def __init__(self, data_dir="data"):
        self.con = duckdb.connect(database=':memory:')
        self.data_dir = data_dir
        self.fuzzy_matcher = FuzzyColumnMatcher()
        self.query_cache = {}  # For deterministic repeated queries
        self.initialize_tables()

    def initialize_tables(self):
        """Initialize DuckDB tables from CSV files."""
        csv_path = os.path.join(self.data_dir, "sap_copa_master.csv")
        try:
            if os.path.exists(csv_path):
                self.con.execute("DROP TABLE IF EXISTS \"copa_analytical_fact\"")
                self.con.execute(f"CREATE TABLE \"copa_analytical_fact\" AS SELECT * FROM read_csv_auto('{csv_path}')")
                print(f"✅ 'copa_analytical_fact' loaded successfully.")
            else:
                print(f"❌ Missing file: {csv_path}")
        except Exception as e:
            print(f"❌ Table load failed: {str(e)}")

    def preprocess_query(self, user_query):
        """
        STEP 1 & 2: Intent Extraction + Entity Normalization
        Applies fuzzy matching and plant normalization.
        """
        # Normalize plant references in the query
        normalized_query = user_query
        for plant_variant, plant_code in self.fuzzy_matcher.PLANT_MAPPINGS.items():
            # Case-insensitive replacement
            pattern = re.compile(re.escape(plant_variant), re.IGNORECASE)
            normalized_query = pattern.sub(plant_code, normalized_query)
        
        # Check for fuzzy column matches
        match_result = self.fuzzy_matcher.match_columns(normalized_query)
        
        if match_result["status"] == "ambiguous":
            return {
                "status": "needs_clarification",
                "message": f"Which {match_result['keyword']} do you mean? Options: {', '.join(match_result['options'])}"
            }
        
        return {
            "status": "ready",
            "normalized_query": normalized_query,
            "matched_columns": match_result.get("columns", [])
        }

    def generate_sql(self, user_query, context=""):
        """
        STEP 4: SQL Generation
        Uses LLM to generate SQL with full system prompt + preprocessing context.
        """
        prompt = f"{FULL_SYSTEM_PROMPT}\n\n"
        
        if context:
            prompt += f"PREPROCESSING CONTEXT:\n{context}\n\n"
        
        prompt += f"Question: {user_query}\n\nSQL:"
        
        payload = {
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0}  # Deterministic
        }
        
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=600)
            sql = response.json().get("response", "").strip()
            
            # Clean up markdown artifacts
            sql = sql.replace('```sql', '').replace('```', '').strip()
            
            # Remove any explanation text after the SQL
            if '\n\n' in sql:
                sql = sql.split('\n\n')[0]
            
            return sql
        except Exception as e:
            print(f"❌ LLM SQL Generation Error: {str(e)}")
            return "SYSTEM_ERROR_SQL_GEN"

    def execute_query(self, sql):
        """
        STEP 5: SQL Execution
        Executes validated SQL on DuckDB.
        """
        try:
            # Basic SQL validation
            if "select" not in sql.lower():
                return "SYSTEM_ERROR_AI"
            
            # Safety: Add LIMIT if not present
            if "limit" not in sql.lower():
                sql = sql.rstrip(';') + " LIMIT 50000"
            
            # Execute query
            result = self.con.execute(sql).fetchdf()
            
            # Convert to records and handle NaN
            records = result.fillna(0).to_dict(orient="records")
            
            # Defensive rounding for all numeric fields
            for row in records:
                for key, val in row.items():
                    if isinstance(val, (float, int)) and not isinstance(val, bool):
                        row[key] = round(float(val), 2)
            
            return records
        
        except Exception as e:
            return f"SYSTEM_ERROR_DB: {str(e)}"

    def verify_and_explain(self, user_query, results):
        """
        STEP 6 & 7: Verification + Explanation
        Implements verification logic and generates business explanation.
        """
        # Prepare results snapshot (max 5 records for context)
        results_snapshot = json.dumps(results[:5] if len(results) > 5 else results, indent=2)
        
        # Check if this is a verification query
        is_verification = any(word in user_query.lower() for word in ["verify", "check", "confirm", "validate"])
        
        explanation_prompt = f"""
{FULL_SYSTEM_PROMPT}

STEP 5 EXECUTION RESULT:
{results_snapshot}

ORIGINAL USER QUERY: {user_query}

MANDATORY FINAL TASK:
"""
        
        if is_verification:
            explanation_prompt += """
1. PERFORM STEP 6 VERIFICATION:
   - Compare the SQL result with the user's expected value.
   - Declare VERIFIED or NOT VERIFIED.
   - Show the difference if not verified.

2. PERFORM STEP 7 EXPLANATION:
   - Provide a purely business-centric explanation.
   - DO NOT mention "SQL", "Database", "Step 5", or "Table".
   - Focus on what this means for the company's profitability.
   - Include ONE actionable business insight.

OUTPUT FORMAT:
Verification Result: [VERIFIED / NOT VERIFIED]

Comparison:
Expected: [user value]
Actual: [formatted result]
Difference: [formatted delta]

Explanation:
[4-5 lines of business insight only]
"""
        else:
            explanation_prompt += """
PERFORM STEP 7 EXPLANATION:
- Provide a purely business-centric explanation.
- DO NOT mention "SQL", "Database", "Step 5", or "Table".
- If the result is a single number, format it clearly (e.g., $1.23M or 15.2%).
- Focus on business performance and operational impact.
- Include ONE actionable business insight.

OUTPUT FORMAT:
Final Answer: [Clear, formatted business answer]

Explanation:
[4-5 lines of business insight only]
"""
        
        payload = {
            "model": MODEL_NAME,
            "prompt": explanation_prompt,
            "stream": False,
            "options": {"temperature": 0}
        }
        
        try:
            response = requests.post(OLLAMA_URL, json=payload, timeout=600)
            return response.json().get("response", "").strip()
        except Exception as e:
            print(f"❌ LLM Explanation Error: {str(e)}")
            return "Data retrieved successfully, but analysis failed."

    def ask_stream(self, user_query):
        """
        STREAMING QUERY ORCHESTRATION
        Yields progress steps and final result as JSON strings.
        """
        # 1. Query Received
        yield json.dumps({"type": "progress", "step": "Query received"}) + "\n"
        
        query_key = user_query.lower().strip()
        if query_key in self.query_cache:
            yield json.dumps({"type": "progress", "step": "Found in cache (Instant retrieval)"}) + "\n"
            yield json.dumps({"type": "result", "payload": self.query_cache[query_key]}) + "\n"
            return
        
        # 2. Analyzing Master Data (Preprocessing)
        yield json.dumps({"type": "progress", "step": "AI analyzing master data schema..."}) + "\n"
        preprocessed = self.preprocess_query(user_query)
        
        if preprocessed["status"] == "needs_clarification":
            result = {
                "query": user_query,
                "error": preprocessed["message"],
                "clarification_needed": True
            }
            yield json.dumps({"type": "result", "payload": result}) + "\n"
            return
        
        normalized_query = preprocessed["normalized_query"]
        matched_columns = preprocessed.get("matched_columns", [])
        
        context = ""
        if matched_columns:
            context = f"Detected columns from user query: {', '.join(matched_columns)}"
        
        # 3. AI Writing Query
        yield json.dumps({"type": "progress", "step": "AI writing SQL query..."}) + "\n"
        sql = self.generate_sql(normalized_query, context)
        
        if "select" not in sql.lower():
            result = {
                "query": user_query,
                "error": "Insufficient data to answer this question."
            }
            yield json.dumps({"type": "result", "payload": result}) + "\n"
            return
        
        # 4. Executing Query
        yield json.dumps({"type": "progress", "step": "Executing database query..."}) + "\n"
        results = self.execute_query(sql)
        
        if isinstance(results, str) and "SYSTEM_ERROR" in results:
            result = {
                "query": user_query,
                "error": results,
                "sql": sql,
                "message": "SQL execution failed. Please rephrase your question."
            }
            yield json.dumps({"type": "result", "payload": result}) + "\n"
            return
        
        if not results:
            result = {
                "query": user_query,
                "summary": "No matching records found in CO-PA data.",
                "sql": sql,
                "data": []
            }
            self.query_cache[query_key] = result
            yield json.dumps({"type": "result", "payload": result}) + "\n"
            return
        
        # 5. Generating Summary
        yield json.dumps({"type": "progress", "step": "AI generating business summary..."}) + "\n"
        final_response = self.verify_and_explain(user_query, results)
        
        # 6. Response Ready
        yield json.dumps({"type": "progress", "step": "Finalizing response..."}) + "\n"
        
        output = {
            "query": user_query,
            "normalized_query": normalized_query,
            "sql": sql,
            "data": results[:100],
            "record_count": len(results),
            "summary": final_response
        }
        
        self.query_cache[query_key] = output
        yield json.dumps({"type": "result", "payload": output}) + "\n"

    def ask(self, user_query):
        """
        MAIN QUERY ORCHESTRATION
        Implements the complete workflow: Steps 1-7
        """
        # RULE 9: Check cache for deterministic repeated queries
        query_key = user_query.lower().strip()
        if query_key in self.query_cache:
            print("🔄 Returning cached result (deterministic behavior)")
            return self.query_cache[query_key]
        
        # STEP 1 & 2: Preprocessing with fuzzy matching
        preprocessed = self.preprocess_query(user_query)
        
        if preprocessed["status"] == "needs_clarification":
            return {
                "query": user_query,
                "error": preprocessed["message"],
                "clarification_needed": True
            }
        
        normalized_query = preprocessed["normalized_query"]
        matched_columns = preprocessed.get("matched_columns", [])
        
        # Prepare context for SQL generation
        context = ""
        if matched_columns:
            context = f"Detected columns from user query: {', '.join(matched_columns)}"
        
        # STEP 4: Generate SQL
        sql = self.generate_sql(normalized_query, context)
        
        if "select" not in sql.lower():
            # DO NOT cache errors - allow retry
            return {
                "query": user_query,
                "error": "Insufficient data to answer this question."
            }
        
        # STEP 5: Execute SQL
        results = self.execute_query(sql)
        
        if isinstance(results, str) and "SYSTEM_ERROR" in results:
            # DO NOT cache errors - allow retry
            return {
                "query": user_query,
                "error": results,
                "sql": sql,
                "message": "SQL execution failed. Please rephrase your question."
            }
        
        if not results:
            # Cache "no results" responses as they are valid (not errors)
            no_data_response = {
                "query": user_query,
                "summary": "No matching records found in CO-PA data.",
                "sql": sql,
                "data": []
            }
            self.query_cache[query_key] = no_data_response
            return no_data_response
        
        # STEP 6 & 7: Verification + Explanation
        final_response = self.verify_and_explain(user_query, results)
        
        # Build final output
        output = {
            "query": user_query,
            "normalized_query": normalized_query,
            "sql": sql,
            "data": results[:100],  # Limit output size
            "record_count": len(results),
            "summary": final_response
        }
        
        # Cache for deterministic behavior
        self.query_cache[query_key] = output
        
        return output

    def get_dashboard_summary(self):
        """Generate high-level dashboard statistics."""
        try:
            stats = self.con.execute('''
                SELECT 
                    SUM("Gross Revenue") as total_gross_revenue,
                    SUM("Net Revenue") as total_net_revenue,
                    AVG("Gross Margin %") as avg_margin_pct,
                    SUM("Cost Variance") as total_cost_variance,
                    COUNT(*) as total_records
                FROM "copa_analytical_fact"
            ''').fetchdf().to_dict(orient="records")[0]
            
            top_plants = self.con.execute('''
                SELECT 
                    "Plant",
                    SUM("Net Revenue") as revenue
                FROM "copa_analytical_fact"
                GROUP BY "Plant"
                ORDER BY revenue DESC
                LIMIT 5
            ''').fetchdf().to_dict(orient="records")
            
            return {
                "stats": stats,
                "top_plants": top_plants
            }
        except Exception as e:
            return {"error": f"Dashboard generation failed: {str(e)}"}

    def get_master_data(self, limit=10000):
        """Retrieve raw master data for reporting."""
        try:
            data = self.con.execute(
                f'SELECT * FROM "copa_analytical_fact" LIMIT {limit}'
            ).fetchdf().to_dict(orient="records")
            return data
        except Exception as e:
            return {"error": f"Master data retrieval failed: {str(e)}"}

    def clear_cache(self):
        """Clear query cache (useful for testing)."""
        self.query_cache.clear()
        print("🧹 Query cache cleared")


# ==========================================
# EXAMPLE USAGE
# ==========================================
if __name__ == "__main__":
    # Initialize engine
    engine = SAPQueryEngine(data_dir="data")
    
    # Test queries demonstrating all features
    test_queries = [
        "What is the total overhead for plant 1?",  # Fuzzy match + plant normalization
        "Show me product MAT001",  # Multi-column material response
        "What is the average PPV?",  # Fuzzy match for Purchase Price Variance
        "Get profit by customer",  # Fuzzy match
        "Show freight for plant_2",  # Ambiguous - should ask for clarification
        "Verify that plant 3 net revenue is 50000",  # Verification query
        "What is the total overhead for plant 1?",  # Repeated query - should return cached
    ]
    
    print("\n" + "="*60)
    print("SAP CO-PA ANALYTICAL COPILOT - TEST SUITE")
    print("="*60 + "\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'─'*60}")
        print(f"TEST {i}: {query}")
        print(f"{'─'*60}")
        
        result = engine.ask(query)
        
        if "error" in result:
            print(f"❌ ERROR: {result['error']}")
        elif "clarification_needed" in result:
            print(f"❓ CLARIFICATION: {result['error']}")
        else:
            print(f"\n📊 SQL Generated:\n{result['sql']}\n")
            print(f"📈 Records Found: {result['record_count']}")
            print(f"\n📝 Analysis:\n{result['summary']}")