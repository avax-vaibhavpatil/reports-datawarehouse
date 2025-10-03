# Database Credentials Setup Guide

## 🎯 **Quick Setup (Recommended)**

### Step 1: Start the Application
```bash
# Terminal 1 - Backend
cd /home/avaxpro/report2.0/reports-datawarehouse
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend  
cd /home/avaxpro/report2.0/reports-datawarehouse/frontend
npm start
```

### Step 2: Access Database Connection
1. Open browser: `http://localhost:4200`
2. Click **"Database"** in the navigation menu
3. You'll see the Database Connection interface

### Step 3: Enter Your Credentials
Fill in the connection form with your database details:

```
Database Type: [Select from dropdown]
├── PostgreSQL (port 5432)
├── MySQL (port 3306) 
├── SQL Server (port 1433)
└── Oracle (port 1521)

Host: [Your database server]
├── localhost (if database is on same machine)
├── 192.168.1.100 (if database is on network)
└── your-db-server.com (if database is remote)

Port: [Database port - defaults provided]
Database Name: [Your database name]
Username: [Your database username]
Password: [Your database password]
Connection Name: [Optional: "Production DB", "Test DB", etc.]
```

### Step 4: Test and Save
1. Click **"Test Connection"** to verify
2. If successful, click **"Save & Continue"**
3. Click **"Discover Tables"** to see your database tables

## 🔧 **Example Configurations**

### PostgreSQL Example
```
Database Type: PostgreSQL
Host: localhost
Port: 5432
Database: my_company_db
Username: postgres
Password: mypassword123
Connection Name: Company Database
```

### MySQL Example
```
Database Type: MySQL
Host: 192.168.1.50
Port: 3306
Database: sales_data
Username: admin
Password: securepass456
Connection Name: Sales Database
```

### SQL Server Example
```
Database Type: SQL Server
Host: sql-server.company.com
Port: 1433
Database: ERP_Database
Username: sa
Password: complexpassword789
Connection Name: ERP Database
```

## 📁 **File-Based Configuration (Advanced)**

If you want to pre-configure connections, edit this file:
```
/home/avaxpro/report2.0/reports-datawarehouse/data/connections.json
```

Example content:
```json
{
  "conn_1": {
    "connection_id": "conn_1",
    "db_type": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "your_database_name",
    "username": "your_username",
    "password": "***",
    "connection_name": "My Production Database"
  }
}
```

**Note:** Passwords are not stored permanently for security. You'll need to re-enter the password when using saved connections.

## 🔒 **Security Best Practices**

1. **Don't commit passwords** to version control
2. **Use environment variables** for production
3. **Test connections** before saving
4. **Use strong passwords** for database accounts
5. **Limit database user permissions** to only what's needed

## 🚨 **Troubleshooting**

### Connection Failed?
- ✅ Check if database server is running
- ✅ Verify host, port, and database name
- ✅ Confirm username and password are correct
- ✅ Check firewall settings
- ✅ Ensure database allows remote connections

### Can't See Tables?
- ✅ Verify user has SELECT permissions
- ✅ Check if database contains tables
- ✅ Ensure connection is still active

### Query Execution Failed?
- ✅ Check SQL syntax
- ✅ Verify table and column names exist
- ✅ Ensure user has appropriate permissions

## 📋 **Quick Checklist**

- [ ] Database server is running
- [ ] Network connectivity is working
- [ ] Credentials are correct
- [ ] User has necessary permissions
- [ ] Firewall allows connections
- [ ] Database contains tables
- [ ] Connection test passes

## 🎉 **Next Steps**

After successful connection:
1. **Discover Tables** - See all available tables
2. **Select Tables** - Choose tables to work with
3. **Build Queries** - Use the SQL Query Builder
4. **Execute Queries** - Run queries on your database
5. **Export Results** - Save results to CSV

The database connection feature eliminates all the file upload issues you were experiencing and provides direct access to your source database with proper join performance!