
import pandas as pd
import numpy as np
import os

def generate_mock_data(data_dir="../data"):
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    cols = {
        "inventory_stock": ["Plant", "Storage_Location", "Material_Number", "Batch_Number", "Available_Stock", "Quality_Stock", "Blocked_Stock", "Expiry_Date", "Stock_Value"],
        "vendor_master": ["Vendor_Code", "Vendor_Name", "Vendor_Category", "Lead_Time_Days", "Contact_Email", "Payment_Terms", "Country", "Vendor_Performance_Score"],
        "pr_data": ["PR_Creation_Date", "Material_Number", "Material_Description", "Material_Group", "Requested_Quantity", "Unit_of_Measure", "Required_Delivery_Date", "Plant", "Storage_Location", "Requestor", "PR_Status"],
        "po_transaction": ["PO_Number", "PO_Creation_Date", "PR_Reference", "Vendor_Code", "Material_Number", "Ordered_Quantity", "Net_Price", "Delivery_Date", "PO_Status", "Confirmation_Status", "Goods_Receipt_Status", "Invoice_Status"],
        "copa_margin_synthetic": ["Material_Number", "Contribution_Margin", "Gross_Margin_Percent", "Profit_per_Customer", "Profit_per_Product", "Profit_per_Batch", "Profit_per_Plant"],
        "copa_cost_variance": ["Material_Number", "Planned_Material_Cost", "Actual_Material_Cost", "Packaging_Cost", "Labor_Cost", "Quality_Cost", "Manufacturing_Overhead", "Freight_Cost", "Cost_Variance", "Production_Variance", "Purchase_Price_Variance_PPV"],
        "copa_revenue": ["Material_Number", "Gross_Revenue", "Contract_Manufacturing_Fee", "Discounts_Rebates", "Freight_Revenue", "Net_Revenue"],
        "copa_characteristics": ["Customer", "Customer_Group", "Product_Material", "Material_Number", "Material_Description", "Product_Category", "Dosage_Form", "Formula_Version", "Batch_Number", "Plant", "Sales_Organization", "Distribution_Channel", "Region_Country"]
    }

    for table, columns in cols.items():
        data = []
        for i in range(100): # Small sample for testing
            row = {}
            for col in columns:
                if "Date" in col:
                    row[col] = "2024-01-01"
                elif "Number" in col or "Code" in col or "Price" in col or "Value" in col or "Quantity" in col or "Cost" in col or "Revenue" in col or "Profit" in col or "Margin" in col or "Score" in col or "Variance" in col:
                    row[col] = np.random.randint(10, 1000)
                else:
                    row[col] = f"Sample_{col}_{i}"
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_csv(os.path.join(data_dir, f"{table}.csv"), index=False)
        print(f"Generated {table}.csv")

if __name__ == "__main__":
    generate_mock_data()
