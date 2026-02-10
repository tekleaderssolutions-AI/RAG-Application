"""
SAP CO-PA Master Schema Definition v2
Consolidated schema with fuzzy matching rules and semantic mappings
"""

# ==========================================
# TABLE SCHEMAS
# ==========================================
TABLE_SCHEMAS = {
    "copa_analytical_fact": {
        "description": "Unified SAP CO-PA Profitability Analysis Master Table containing Revenue, Margin, Costs, and Characteristics.",
        "file_name": "sap_copa_master.csv",
        
        "columns": {
            # ===== IDENTIFICATION =====
            "Material Number": {
                "description": "Unique material/product identifier (primary key)",
                "data_type": "VARCHAR",
                "sample_values": ["MAT001", "MAT002", "MAT003"],
                "fuzzy_keywords": ["material", "product", "mat", "item"],
                "special_rule": "ALWAYS return with 'Product (Material)' and 'Material Description'"
            },
            "Product (Material)": {
                "description": "Product/material name",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["product", "material", "item name"],
                "special_rule": "ALWAYS return with 'Material Number' and 'Material Description'"
            },
            "Material Description": {
                "description": "Full text description of the material/product",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["description", "product description", "material description"],
                "special_rule": "ALWAYS return with 'Material Number' and 'Product (Material)'"
            },
            
            # ===== CHARACTERISTICS (DIMENSIONS) =====
            "Plant": {
                "description": "Manufacturing plant identifier",
                "data_type": "VARCHAR",
                "sample_values": ["PL01", "PL02", "PL03", "PL04", "PL05"],
                "fuzzy_keywords": ["plant", "factory", "facility"],
                "normalization": {
                    "plant 1": "PL01", "plant_1": "PL01", "plant-1": "PL01", "p1": "PL01",
                    "plant 2": "PL02", "plant_2": "PL02", "plant-2": "PL02", "p2": "PL02",
                    "plant 3": "PL03", "plant_3": "PL03", "plant-3": "PL03", "p3": "PL03",
                    "plant 4": "PL04", "plant_4": "PL04", "plant-4": "PL04", "p4": "PL04",
                    "plant 5": "PL05", "plant_5": "PL05", "plant-5": "PL05", "p5": "PL05"
                }
            },
            "Region / Country": {
                "description": "Geographic location/market",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["region", "country", "geography", "location", "market"]
            },
            "Customer": {
                "description": "Customer identifier/name",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["customer", "client", "buyer"]
            },
            "Customer Group": {
                "description": "Customer classification/segment",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["customer group", "customer segment", "customer type"]
            },
            "Product Category": {
                "description": "Business segment/product line",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["category", "product category", "segment", "line"]
            },
            "Dosage Form": {
                "description": "Physical form of product (Tablet, Powder, Liquid, etc.)",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["dosage", "form", "dosage form"]
            },
            "Formula Version": {
                "description": "Production recipe/formula version",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["formula", "version", "recipe", "formula version"]
            },
            "Batch Number": {
                "description": "Production batch identifier",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["batch", "batch number", "lot", "lot number"]
            },
            "Sales Organization": {
                "description": "Responsible sales organization unit",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["sales org", "sales organization", "sales unit"]
            },
            "Distribution Channel": {
                "description": "Sales/distribution channel",
                "data_type": "VARCHAR",
                "fuzzy_keywords": ["distribution", "channel", "distribution channel"]
            },
            
            # ===== REVENUE DATA =====
            "Gross Revenue": {
                "description": "Total revenue before any deductions",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["gross revenue", "gross sales"],
                "aggregation_default": "SUM"
            },
            "Net Revenue": {
                "description": "Final revenue after all deductions and discounts",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["net revenue", "revenue", "net sales", "sales"],
                "aggregation_default": "SUM",
                "special_rule": "Default 'revenue' (unqualified) maps here"
            },
            "Discounts / Rebates": {
                "description": "Total discounts and rebates applied",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["discount", "discounts", "rebate", "rebates"],
                "aggregation_default": "SUM"
            },
            "Contract Manufacturing Fee": {
                "description": "Fees paid for external/contract manufacturing",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["contract fee", "manufacturing fee", "contract manufacturing"],
                "aggregation_default": "SUM"
            },
            "Freight Revenue": {
                "description": "Revenue from shipping/freight charges",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["freight revenue"],
                "aggregation_default": "SUM",
                "ambiguous_with": "Freight Cost"
            },
            
            # ===== PROFIT & MARGIN DATA =====
            "Contribution Margin": {
                "description": "Net margin after variable costs",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["contribution", "margin", "contribution margin"],
                "aggregation_default": "SUM",
                "special_rule": "Default 'margin' (unqualified) maps here"
            },
            "Gross Margin %": {
                "description": "Profitability percentage",
                "data_type": "DECIMAL(5,2)",
                "fuzzy_keywords": ["gross margin", "margin percent", "margin percentage"],
                "aggregation_default": "AVG"
            },
            "Profit per Customer": {
                "description": "Profit attributed to specific customer groups",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["profit customer", "customer profit"],
                "aggregation_default": "SUM",
                "ambiguous_with": ["Profit per Product", "Profit per Batch", "Profit per Plant"]
            },
            "Profit per Product": {
                "description": "Profit attributed to specific products",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["profit product", "product profit"],
                "aggregation_default": "SUM",
                "ambiguous_with": ["Profit per Customer", "Profit per Batch", "Profit per Plant"]
            },
            "Profit per Batch": {
                "description": "Profit from specific production batches",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["profit batch", "batch profit"],
                "aggregation_default": "SUM",
                "ambiguous_with": ["Profit per Customer", "Profit per Product", "Profit per Plant"]
            },
            "Profit per Plant": {
                "description": "Profit generated at plant/facility level",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["profit plant", "plant profit"],
                "aggregation_default": "SUM",
                "ambiguous_with": ["Profit per Customer", "Profit per Product", "Profit per Batch"]
            },
            
            # ===== COSTS =====
            "Planned Material Cost": {
                "description": "Target/budgeted material cost",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["planned cost", "planned material cost", "budgeted cost"],
                "aggregation_default": "SUM"
            },
            "Actual Material Cost": {
                "description": "Actual material cost incurred",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["actual cost", "material cost", "actual material cost"],
                "aggregation_default": "SUM",
                "special_rule": "Default 'material cost' (unqualified) maps here"
            },
            "Packaging Cost": {
                "description": "Cost of packaging materials",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["packaging", "packaging cost", "packing"],
                "aggregation_default": "SUM"
            },
            "Labor Cost": {
                "description": "Direct labor/manpower costs",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["labor", "labor cost", "manpower", "workforce"],
                "aggregation_default": "SUM"
            },
            "Quality Cost": {
                "description": "Quality inspection and control costs",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["quality", "quality cost", "inspection"],
                "aggregation_default": "SUM"
            },
            "Manufacturing Overhead": {
                "description": "Indirect manufacturing costs (utilities, rent, etc.)",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["overhead", "manufacturing overhead", "indirect cost"],
                "aggregation_default": "SUM"
            },
            "Freight Cost": {
                "description": "Shipping and logistics costs",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["freight cost"],
                "aggregation_default": "SUM",
                "ambiguous_with": "Freight Revenue"
            },
            
            # ===== VARIANCES =====
            "Cost Variance": {
                "description": "Total cost variance (Actual - Planned)",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["cost variance"],
                "aggregation_default": "SUM",
                "ambiguous_with": ["Production Variance", "Purchase Price Variance (PPV)"]
            },
            "Production Variance": {
                "description": "Production efficiency variance",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["production variance"],
                "aggregation_default": "SUM",
                "ambiguous_with": ["Cost Variance", "Purchase Price Variance (PPV)"]
            },
            "Purchase Price Variance (PPV)": {
                "description": "Difference between purchase order price and standard cost",
                "data_type": "DECIMAL(15,2)",
                "fuzzy_keywords": ["ppv", "purchase price variance", "purchase variance"],
                "aggregation_default": "SUM",
                "ambiguous_with": ["Cost Variance", "Production Variance"]
            }
        }
    }
}

# ==========================================
# FUZZY MATCHING CONFIGURATION
# ==========================================
FUZZY_MATCHING_RULES = {
    "multi_column_triggers": {
        "material": ["Material Number", "Product (Material)", "Material Description"],
        "product": ["Material Number", "Product (Material)", "Material Description"],
    },
    
    "ambiguous_keywords": {
        "freight": ["Freight Cost", "Freight Revenue"],
        "variance": ["Cost Variance", "Production Variance", "Purchase Price Variance (PPV)"],
        "profit": ["Profit per Customer", "Profit per Product", "Profit per Batch", "Profit per Plant"],
    },
    
    "unqualified_defaults": {
        "margin": "Contribution Margin",
        "revenue": "Net Revenue",
        "cost": "Actual Material Cost"
    }
}

# ==========================================
# PLANT NORMALIZATION MAPPING
# ==========================================
PLANT_NORMALIZATION = {
    "plant 1": "PL01", "plant_1": "PL01", "plant-1": "PL01", "pl01": "PL01", "p1": "PL01",
    "plant 2": "PL02", "plant_2": "PL02", "plant-2": "PL02", "pl02": "PL02", "p2": "PL02",
    "plant 3": "PL03", "plant_3": "PL03", "plant-3": "PL03", "pl03": "PL03", "p3": "PL03",
    "plant 4": "PL04", "plant_4": "PL04", "plant-4": "PL04", "pl04": "PL04", "p4": "PL04",
    "plant 5": "PL05", "plant_5": "PL05", "plant-5": "PL05", "pl05": "PL05", "p5": "PL05",
}

# ==========================================
# AGGREGATION RULES
# ==========================================
AGGREGATION_MAPPING = {
    "average": "AVG",
    "mean": "AVG",
    "avg": "AVG",
    
    "total": "SUM",
    "sum": "SUM",
    "add": "SUM",
    
    "minimum": "MIN",
    "min": "MIN",
    "lowest": "MIN",
    "smallest": "MIN",
    
    "maximum": "MAX",
    "max": "MAX",
    "highest": "MAX",
    "largest": "MAX",
    
    "count": "COUNT",
    "number": "COUNT",
    "how many": "COUNT",
}

# ==========================================
# VALIDATION RULES
# ==========================================
VALIDATION_RULES = {
    "max_records": 50000,      # ← Changed from 10000
    "default_limit": 5000,      # Default query limit
    "api_max_limit": 10000,     # Recommended for performance
    "min_query_length": 3,
    "max_query_length": 500,
}

# ==========================================
# BUSINESS RULES
# ==========================================
BUSINESS_RULES = {
    "verification_keywords": ["verify", "check", "confirm", "validate", "is it true"],
    "explanation_max_lines": 5,
    "deterministic_caching": True,
    "fuzzy_matching_enabled": True,
}

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def get_column_info(column_name: str) -> dict:
    """Get detailed information about a specific column."""
    schema = TABLE_SCHEMAS["copa_analytical_fact"]
    return schema["columns"].get(column_name, {})

def get_all_columns() -> list:
    """Get list of all column names."""
    schema = TABLE_SCHEMAS["copa_analytical_fact"]
    return list(schema["columns"].keys())

def get_fuzzy_keywords(column_name: str) -> list:
    """Get fuzzy matching keywords for a column."""
    info = get_column_info(column_name)
    return info.get("fuzzy_keywords", [])

def is_ambiguous_keyword(keyword: str) -> bool:
    """Check if a keyword is ambiguous."""
    return keyword.lower() in FUZZY_MATCHING_RULES["ambiguous_keywords"]

def get_normalization_for_plant(plant_input: str) -> str:
    """Get normalized plant code."""
    return PLANT_NORMALIZATION.get(plant_input.lower(), plant_input)

# ==========================================
# SCHEMA METADATA
# ==========================================
SCHEMA_METADATA = {
    "version": "2.0.0",
    "last_updated": "2025-02-09",
    "total_columns": len(TABLE_SCHEMAS["copa_analytical_fact"]["columns"]),
    "features": [
        "fuzzy_column_matching",
        "plant_normalization",
        "multi_column_material_response",
        "ambiguity_detection",
        "verification_support",
        "deterministic_caching"
    ]
}

if __name__ == "__main__":
    # Print schema summary
    print("="*70)
    print("SAP CO-PA MASTER SCHEMA v2")
    print("="*70)
    print(f"\nTotal Columns: {SCHEMA_METADATA['total_columns']}")
    print(f"Version: {SCHEMA_METADATA['version']}")
    print(f"Last Updated: {SCHEMA_METADATA['last_updated']}")
    print(f"\nFeatures:")
    for feature in SCHEMA_METADATA['features']:
        print(f"  ✓ {feature}")
    print("\n" + "="*70)
