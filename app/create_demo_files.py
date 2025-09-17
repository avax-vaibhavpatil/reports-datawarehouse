import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_demo_files():
    """Create demo Excel files with related data for testing relationships"""
    
    # Create data directory if it doesn't exist
    data_dir = Path("data/uploads")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info("Creating demo Excel files with related data...")
    
    # 1. CUSTOMERS FILE - Will have customer_id, name, email, region
    customers_data = {
        'customer_id': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010],
        'name': ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Wilson', 'Tom Brown', 
                 'Emma Taylor', 'David Miller', 'Anna Garcia', 'Chris Lee', 'Maria Rodriguez'],
        'email': ['john@email.com', 'sarah@email.com', 'mike@email.com', 'lisa@email.com', 'tom@email.com',
                  'emma@email.com', 'david@email.com', 'anna@email.com', 'chris@email.com', 'maria@email.com'],
        'region': ['North', 'South', 'East', 'West', 'North', 'South', 'East', 'West', 'North', 'South']
    }
    
    customers_df = pd.DataFrame(customers_data)
    customers_file = data_dir / "customers.xlsx"
    customers_df.to_excel(customers_file, index=False)
    logger.info(f"Created {customers_file} with {len(customers_df)} customers")
    
    # 2. ORDERS FILE - Will have order_id, customer_id (RELATED to customers), amount, date
    orders_data = {
        'order_id': [2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012],
        'customer_id': [1001, 1002, 1001, 1003, 1004, 1002, 1005, 1006, 1003, 1007, 1008, 1009],  # Related to customers
        'amount': [150.00, 89.99, 299.99, 45.50, 199.99, 75.25, 120.00, 89.99, 250.00, 175.50, 95.00, 300.00],
        'date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19', '2024-01-20',
                 '2024-01-21', '2024-01-22', '2024-01-23', '2024-01-24', '2024-01-25', '2024-01-26']
    }
    
    orders_df = pd.DataFrame(orders_data)
    orders_file = data_dir / "orders.xlsx"
    orders_df.to_excel(orders_file, index=False)
    logger.info(f"Created {orders_file} with {len(orders_df)} orders")
    
    # 3. PRODUCTS FILE - Will have product_id, name, price, category
    products_data = {
        'product_id': [3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008, 3009, 3010],
        'name': ['Laptop', 'Mouse', 'Keyboard', 'Monitor', 'Headphones', 'Webcam', 'Speaker', 'Microphone', 'Tablet', 'Phone'],
        'price': [999.99, 29.99, 79.99, 299.99, 89.99, 49.99, 129.99, 59.99, 599.99, 799.99],
        'category': ['Electronics', 'Accessories', 'Accessories', 'Electronics', 'Accessories', 'Accessories', 'Accessories', 'Accessories', 'Electronics', 'Electronics']
    }
    
    products_df = pd.DataFrame(products_data)
    products_file = data_dir / "products.xlsx"
    products_df.to_excel(products_file, index=False)
    logger.info(f"Created {products_file} with {len(products_df)} products")
    
    # 4. EMPLOYEES FILE - Will have employee_id, name (SAME NAME as customers), department, salary
    employees_data = {
        'employee_id': [4001, 4002, 4003, 4004, 4005],
        'name': ['John Smith', 'Sarah Johnson', 'Mike Davis', 'Lisa Wilson', 'Tom Brown'],  # SAME NAMES as customers
        'department': ['Sales', 'Marketing', 'IT', 'HR', 'Finance'],
        'salary': [50000, 55000, 65000, 48000, 60000]
    }
    
    employees_df = pd.DataFrame(employees_data)
    employees_file = data_dir / "employees.xlsx"
    employees_df.to_excel(employees_file, index=False)
    logger.info(f"Created {employees_file} with {len(employees_df)} employees")
    
    # 5. SALES FILE - Will have sale_id, customer_id (RELATED to customers), product_id (RELATED to products), quantity
    sales_data = {
        'sale_id': [5001, 5002, 5003, 5004, 5005, 5006, 5007, 5008],
        'customer_id': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008],  # Related to customers
        'product_id': [3001, 3002, 3003, 3004, 3005, 3006, 3007, 3008],  # Related to products
        'quantity': [1, 2, 1, 1, 3, 1, 2, 1],
        'sale_date': ['2024-01-15', '2024-01-16', '2024-01-17', '2024-01-18', '2024-01-19', '2024-01-20', '2024-01-21', '2024-01-22']
    }
    
    sales_df = pd.DataFrame(sales_data)
    sales_file = data_dir / "sales.xlsx"
    sales_df.to_excel(sales_file, index=False)
    logger.info(f"Created {sales_file} with {len(sales_df)} sales")
    
    logger.info("✅ Demo files created successfully!")
    logger.info("📁 Files created in data/uploads/ directory:")
    logger.info(f"   - {customers_file.name}")
    logger.info(f"   - {orders_file.name}")
    logger.info(f"   - {products_file.name}")
    logger.info(f"   - {employees_file.name}")
    logger.info(f"   - {sales_file.name}")
    
    logger.info("\n🔗 Expected Relationships:")
    logger.info("   - customers.customer_id ↔ orders.customer_id (STRONG - same values + same type)")
    logger.info("   - customers.customer_id ↔ sales.customer_id (STRONG - same values + same type)")
    logger.info("   - products.product_id ↔ sales.product_id (STRONG - same values + same type)")
    logger.info("   - customers.name ↔ employees.name (MEDIUM - same names + same type, but different values)")
    logger.info("   - customers.customer_id ↔ products.product_id (WEAK - same type but no value overlap)")
    
    return [
        str(customers_file),
        str(orders_file),
        str(products_file),
        str(employees_file),
        str(sales_file)
    ]

if __name__ == "__main__":
    create_demo_files() 