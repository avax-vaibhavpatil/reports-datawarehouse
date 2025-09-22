# 🏗️ Data Warehouse Setup Guide

This guide explains how to set up and use the data warehouse functionality in the Excel Generator application.

## 🎯 **What is the Data Warehouse Flow?**

The data warehouse flow allows you to:
1. **Upload Excel/CSV files** → Extract column metadata
2. **Build SQL queries** → Execute queries against uploaded data
3. **Generate schema previews** → Analyze data types and structure
4. **Create PostgreSQL tables** → Store query results permanently
5. **Insert data** → Bulk load results into the data warehouse

## 🚀 **Quick Setup**

### **Option 1: Automated Setup (Recommended)**
```bash
# Run the quick start script
./quick_start.sh
```

### **Option 2: Manual Setup**
```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Setup PostgreSQL database
python3 setup_database.py

# 3. Start backend
cd app && python main.py

# 4. Start frontend (in another terminal)
cd frontend && npm start
```

## 🗄️ **Database Requirements**

### **PostgreSQL Setup**
- **Version**: PostgreSQL 12+ (recommended: 14+)
- **Database**: `datawarehouse`
- **User**: `reporting_user`
- **Password**: `root` (change in setup_database.py)
- **Schemas**: `processed_data`, `raw_data`, `reports`, `temp`

### **Installation Commands**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Download from https://www.postgresql.org/download/
```

## 🔧 **Configuration**

### **Environment Variables**
Create a `.env` file in the project root:
```env
# PostgreSQL Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DATABASE=datawarehouse
POSTGRES_USER=reporting_user
POSTGRES_PASSWORD=root

# SQLite Configuration (for Excel/CSV processing)
SQLITE_DB_PATH=data/excel_data.db

# Application Configuration
APP_ENV=development
LOG_LEVEL=INFO
```

### **Database Configuration**
The application uses two databases:
- **SQLite**: For Excel/CSV file processing and query execution
- **PostgreSQL**: For data warehouse storage and persistence

## 🧪 **Testing the Setup**

### **Run Test Suite**
```bash
# Test the complete data warehouse flow
python3 test_datawarehouse_flow.py
```

### **Manual Testing Steps**
1. **Upload Files**: Go to http://localhost:4200 and upload Excel/CSV files
2. **Build Query**: Use the SQL Query Builder to create queries
3. **Execute Query**: Run queries and view results
4. **Save to Warehouse**: Click "Save to Warehouse" button
5. **Configure Schema**: Set table name and review column types
6. **Create Table**: Confirm table creation in PostgreSQL

## 🏗️ **Architecture Overview**

```
┌─────────────────┐    HTTP API    ┌─────────────────┐
│   Angular 20    │ ◄────────────► │   FastAPI       │
│   Frontend      │                │   Backend       │
│                 │                │                 │
│ • File Upload   │                │ • File Storage  │
│ • Query Builder │                │ • SQLite Query  │
│ • Schema Editor │                │ • PostgreSQL    │
└─────────────────┘                └─────────────────┘
                                              │
                                              ▼
                                    ┌─────────────────┐
                                    │   PostgreSQL    │
                                    │   Data Warehouse│
                                    │                 │
                                    │ • processed_data│
                                    │ • raw_data      │
                                    │ • reports       │
                                    │ • temp          │
                                    └─────────────────┘
```

## 📊 **Data Flow Process**

### **1. File Upload & Processing**
- Files uploaded to `data/uploads/`
- Column metadata extracted using Pandas
- Data stored in SQLite for querying

### **2. SQL Query Building**
- Visual query builder interface
- Support for multiple JOIN types
- Real-time query validation
- Sample data preview

### **3. Schema Analysis**
- Automatic data type detection
- PostgreSQL type mapping
- Column name cleaning
- User correction interface

### **4. Table Creation**
- PostgreSQL table generation
- Batch data insertion
- Progress tracking
- Error handling

### **5. Data Warehouse Storage**
- Permanent storage in PostgreSQL
- Organized by schemas
- Queryable with standard SQL
- Backup and recovery ready

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. "Save to Warehouse" Button Not Working**
- **Cause**: Missing MatDialogModule import
- **Fix**: Already fixed in the codebase
- **Verify**: Check browser console for errors

#### **2. Database Connection Failed**
- **Cause**: PostgreSQL not running or not configured
- **Fix**: 
  ```bash
  sudo systemctl start postgresql
  python3 setup_database.py
  ```

#### **3. Schema Editor Dialog Not Opening**
- **Cause**: Frontend import issues
- **Fix**: Restart frontend development server
  ```bash
  cd frontend && npm start
  ```

#### **4. Table Creation Fails**
- **Cause**: PostgreSQL permissions or connection issues
- **Fix**: Check database logs and user permissions

### **Debug Commands**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Check database connection
psql -h localhost -U reporting_user -d datawarehouse

# View application logs
tail -f app.log

# Test API endpoints
curl http://localhost:8000/api/files/health
curl http://localhost:8000/api/schema-editor/health
```

## 📈 **Performance Considerations**

### **File Size Limits**
- **Maximum file size**: 100MB per file
- **Recommended**: < 50MB for optimal performance
- **Large files**: Use batch processing

### **Query Performance**
- **Sample size**: 100 rows for preview
- **Full execution**: 1000 rows limit
- **Large datasets**: Use pagination

### **Database Performance**
- **Batch size**: 1000 rows per insert
- **Connection pooling**: Automatic
- **Indexing**: Automatic on primary keys

## 🔒 **Security Considerations**

### **Database Security**
- **User permissions**: Limited to specific schemas
- **Password**: Change default password in production
- **Network**: Restrict database access

### **File Security**
- **Upload validation**: Only Excel/CSV files
- **Path traversal**: Prevented
- **File size**: Limited to prevent DoS

## 🚀 **Production Deployment**

### **Environment Setup**
1. **Production database**: Use managed PostgreSQL service
2. **Environment variables**: Set secure passwords
3. **File storage**: Use cloud storage for large files
4. **Monitoring**: Add logging and monitoring

### **Scaling Considerations**
- **Database**: Use read replicas for queries
- **File processing**: Use background jobs
- **API**: Use load balancers
- **Storage**: Use distributed file systems

## 📚 **API Documentation**

### **Key Endpoints**
- `POST /api/files/upload` - Upload files
- `GET /api/sql-query/tables` - Get available tables
- `POST /api/sql-query/preview` - Preview query results
- `POST /api/schema-editor/preview` - Generate schema preview
- `POST /api/schema-editor/create-table` - Create PostgreSQL table

### **Interactive Documentation**
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🎉 **Success Indicators**

When everything is working correctly, you should see:
- ✅ Files upload successfully
- ✅ Queries execute and return results
- ✅ "Save to Warehouse" button opens dialog
- ✅ Schema editor shows column analysis
- ✅ Table creation completes successfully
- ✅ Data appears in PostgreSQL database

## 🆘 **Getting Help**

If you encounter issues:
1. **Check logs**: Look at console and server logs
2. **Run tests**: Use `python3 test_datawarehouse_flow.py`
3. **Verify setup**: Ensure all dependencies are installed
4. **Check database**: Verify PostgreSQL is running and accessible

---

**🎯 The data warehouse flow is now ready to use! Upload your Excel files, build queries, and save results to PostgreSQL for permanent storage and analysis.**