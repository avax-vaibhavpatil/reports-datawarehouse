#!/usr/bin/env python3
"""
Sample Excel File Generator
Creates sample Excel files for testing the Excel Generator application
"""

import pandas as pd
import os
from pathlib import Path

def create_sample_files():
    """Create sample Excel files for testing"""
    
    # Create sample data directory
    sample_dir = Path("sample_data")
    sample_dir.mkdir(exist_ok=True)
    
    # Sample 1: Customers data
    customers_data = {
        'customer_id': [1001, 1002, 1003, 1004, 1005],
        'customer_name': ['John Doe', 'Jane Smith', 'Bob Johnson', 'Alice Brown', 'Charlie Wilson'],
        'email': ['john@example.com', 'jane@example.com', 'bob@example.com', 'alice@example.com', 'charlie@example.com'],
        'region': ['North', 'South', 'East', 'West', 'Central'],
        'registration_date': ['2024-01-15', '2024-01-20', '2024-02-01', '2024-02-10', '2024-02-15']
    }
    
    customers_df = pd.DataFrame(customers_data)
    customers_df.to_excel(sample_dir / "customers.xlsx", index=False)
    print("✅ Created customers.xlsx")
    
    # Sample 2: Orders data
    orders_data = {
        'order_id': [2001, 2002, 2003, 2004, 2005, 2006],
        'customer_id': [1001, 1002, 1001, 1003, 1004, 1005],
        'product_name': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones', 'Webcam'],
        'quantity': [1, 2, 1, 1, 1, 1],
        'unit_price': [999.99, 29.99, 79.99, 299.99, 89.99, 59.99],
        'order_date': ['2024-01-20', '2024-01-25', '2024-02-05', '2024-02-12', '2024-02-18', '2024-02-20']
    }
    
    orders_df = pd.DataFrame(orders_data)
    orders_df.to_excel(sample_dir / "orders.xlsx", index=False)
    print("✅ Created orders.xlsx")
    
    # Sample 3: Products data
    products_data = {
        'product_id': [3001, 3002, 3003, 3004, 3005, 3006],
        'product_name': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones', 'Webcam'],
        'category': ['Electronics', 'Accessories', 'Accessories', 'Electronics', 'Accessories', 'Accessories'],
        'brand': ['TechCorp', 'AccessPro', 'KeyMaster', 'DisplayTech', 'SoundMax', 'VisionCam'],
        'stock_quantity': [50, 200, 150, 30, 100, 75],
        'price': [999.99, 29.99, 79.99, 299.99, 89.99, 59.99]
    }
    
    products_df = pd.DataFrame(products_data)
    products_df.to_excel(sample_dir / "products.xlsx", index=False)
    print("✅ Created products.xlsx")
    
    # Sample 4: Sales data
    sales_data = {
        'sale_id': [4001, 4002, 4003, 4004, 4005],
        'product_id': [3001, 3002, 3003, 3004, 3005],
        'quantity_sold': [2, 5, 3, 1, 4],
        'sale_date': ['2024-01-25', '2024-01-30', '2024-02-05', '2024-02-10', '2024-02-15'],
        'salesperson': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'region': ['North', 'South', 'East', 'West', 'Central']
    }
    
    sales_df = pd.DataFrame(sales_data)
    sales_df.to_excel(sample_dir / "sales.xlsx", index=False)
    print("✅ Created sales.xlsx")
    
    # Sample 5: Employees data
    employees_data = {
        'employee_id': [5001, 5002, 5003, 5004, 5005],
        'first_name': ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve'],
        'last_name': ['Johnson', 'Smith', 'Brown', 'Wilson', 'Davis'],
        'department': ['Sales', 'Marketing', 'IT', 'HR', 'Finance'],
        'hire_date': ['2023-01-15', '2023-03-20', '2023-06-01', '2023-08-10', '2023-11-15'],
        'salary': [55000, 52000, 65000, 48000, 60000]
    }
    
    employees_df = pd.DataFrame(employees_data)
    employees_df.to_excel(sample_dir / "employees.xlsx", index=False)
    print("✅ Created employees.xlsx")
    
    print(f"\n🎉 Created {len([f for f in sample_dir.glob('*.xlsx')])} sample Excel files in {sample_dir}/")
    print("📁 Files created:")
    for file in sample_dir.glob('*.xlsx'):
        print(f"   - {file.name}")

if __name__ == "__main__":
    create_sample_files() 