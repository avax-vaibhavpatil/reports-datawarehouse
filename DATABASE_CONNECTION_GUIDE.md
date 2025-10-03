# Database Connection Feature Guide

## Overview

The database connection feature allows you to connect directly to your source database instead of uploading Excel/CSV files. This eliminates the issues with file format problems, heavy joins, and data loss that you were experiencing.

## Features

### ✅ **What's New**
- **Direct Database Connection**: Connect to PostgreSQL, MySQL, SQL Server, or Oracle
- **Table Discovery**: Automatically discover all tables and their structure
- **Real-time Data**: Always work with current data from your database
- **Native SQL Performance**: All join types work correctly on the source database
- **No File Upload Issues**: Eliminates Excel/CSV format problems
- **Better Scalability**: Can handle much larger datasets efficiently

### 🔧 **Supported Databases**
- PostgreSQL (port 5432)
- MySQL (port 3306)
- SQL Server (port 1433)
- Oracle (port 1521)

## How to Use

### Step 1: Access Database Connection
1. Start the application
2. Click on "Database" in the navigation menu
3. You'll see the Database Connection interface

### Step 2: Configure Connection
1. **Select Database Type**: Choose from PostgreSQL, MySQL, SQL Server, or Oracle
2. **Enter Connection Details**:
   - Host: Your database server address
   - Port: Database port (defaults are provided)
   - Database Name: Name of your database
   - Username: Database username
   - Password: Database password
   - Connection Name: Optional name to save the connection
3. **Test Connection**: Click "Test Connection" to verify your settings
4. **Save Connection**: Click "Save & Continue" to save for future use

### Step 3: Discover Tables
1. After successful connection, click "Discover Tables"
2. The system will scan your database and show all available tables
3. Each table shows:
   - Table name
   - Number of rows
   - Column information
   - Foreign key relationships

### Step 4: Select Tables
1. Browse through the discovered tables
2. Click on tables you want to work with
3. Selected tables will be highlighted
4. Click "Continue to Query Builder" when done

### Step 5: Build Queries
1. Use the SQL Query Builder with your selected tables
2. All join types (INNER, LEFT, RIGHT, FULL OUTER) work correctly
3. Execute queries directly on your source database
4. Export results to CSV

## Benefits Over File Upload

### ❌ **Old Problems (File Upload)**
- Excel format issues and warnings
- Heavy joins causing performance problems
- Data loss during import
- Manual column mapping required
- Limited to uploaded file data

### ✅ **New Solutions (Database Connection)**
- No file format issues
- Native database performance for joins
- No data loss - direct access to source
- Automatic table and column discovery
- Always current data

## Technical Details

### Backend Components
- `DatabaseConnectionService`: Manages database connections
- `database_connection_routes.py`: API endpoints for connection management
- Enhanced `SQLQueryService`: Supports both file and database modes

### Frontend Components
- `DatabaseConnectionComponent`: Main connection interface
- `database-connection.service.ts`: Frontend service for API calls
- Updated navigation and routing

### Security
- Passwords are not stored permanently
- Connections are tested before saving
- Secure connection strings are used

## API Endpoints

### Connection Management
- `POST /api/database-connection/test` - Test database connection
- `POST /api/database-connection/save` - Save connection
- `GET /api/database-connection/connections` - Get saved connections
- `DELETE /api/database-connection/connections/{id}` - Delete connection

### Table Discovery
- `POST /api/database-connection/discover-tables` - Discover tables
- `GET /api/database-connection/supported-databases` - Get supported DB types

### Query Execution
- `POST /api/database-connection/execute-query` - Execute SQL query
- `POST /api/sql-query/database-tables` - Get tables for query builder
- `POST /api/sql-query/database-generate` - Generate and execute query

## Installation

### Backend Dependencies
The following packages have been added to `requirements.txt`:
```
pymysql==1.1.0      # MySQL support
pyodbc==5.0.1       # SQL Server support
cx-oracle==8.3.0    # Oracle support
```

### Install Dependencies
```bash
cd reports-datawarehouse
pip install -r requirements.txt
```

### Start the Application
```bash
# Backend
python -m uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm start
```

## Usage Examples

### Example 1: PostgreSQL Connection
```
Database Type: PostgreSQL
Host: localhost
Port: 5432
Database: my_database
Username: postgres
Password: your_password
```

### Example 2: MySQL Connection
```
Database Type: MySQL
Host: 192.168.1.100
Port: 3306
Database: sales_data
Username: admin
Password: your_password
```

## Troubleshooting

### Connection Issues
- Verify database server is running
- Check firewall settings
- Ensure correct port and credentials
- Test connection before saving

### Table Discovery Issues
- Ensure user has SELECT permissions
- Check if database contains tables
- Verify connection is still active

### Query Execution Issues
- Check SQL syntax
- Verify table and column names
- Ensure user has appropriate permissions

## Migration from File Upload

If you have existing file-based workflows:

1. **Keep File Upload**: The file upload feature still works for existing workflows
2. **Add Database Connection**: Use database connection for new projects
3. **Gradual Migration**: Move from files to database connections over time
4. **Hybrid Approach**: Use both methods as needed

## Next Steps

1. **Test the Feature**: Try connecting to a test database
2. **Explore Tables**: Discover your database structure
3. **Build Queries**: Create queries using the query builder
4. **Export Results**: Save query results to CSV
5. **Save Connections**: Store frequently used connections

The database connection feature provides a much more robust and efficient way to work with your data, eliminating the issues you were experiencing with file uploads and heavy joins.