# Reports Data Warehouse - Complete Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [File Upload and Processing](#file-upload-and-processing)
4. [Data Joining and Relationships](#data-joining-and-relationships)
5. [Frontend Components](#frontend-components)
6. [Backend Services](#backend-services)
7. [API Endpoints](#api-endpoints)
8. [Configuration](#configuration)
9. [Installation and Setup](#installation-and-setup)
10. [Usage Guide](#usage-guide)
11. [Troubleshooting](#troubleshooting)
12. [Future Features](#future-features)

---

## Project Overview

**Reports Data Warehouse** is a full-stack application designed for data integration, analysis, and reporting. It allows users to upload Excel/CSV files, create relationships between tables, and generate combined datasets for analysis.

### Key Features
- ✅ **Multi-format File Support**: Excel (.xlsx, .xls) and CSV files
- ✅ **Column Selection**: Interactive column selection from uploaded files
- ✅ **Relationship Management**: Create relationships between tables
- ✅ **Data Joining**: Join multiple tables using composite keys
- ✅ **Custom Table Naming**: Name your combined tables
- ✅ **Real-time Data Display**: View joined data with scrollable tables
- ✅ **Sample Size Control**: Configure data sampling for performance

### Technology Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Angular 20 + Material UI
- **Data Processing**: Pandas
- **Database**: DuckDB (configured but not active)
- **File Storage**: Local filesystem

---

## Architecture

### System Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Data Layer    │
│   (Angular)     │◄──►│   (FastAPI)     │◄──►│   (Files)       │
│                 │    │                 │    │                 │
│ • File Upload   │    │ • File Routes   │    │ • data/uploads/ │
│ • Column Select │    │ • File Service  │    │ • CSV/Excel     │
│ • Data Display  │    │ • Column Service│    │ • Metadata      │
│ • Relationships │    │ • Join Logic    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Directory Structure

```
reports-datawarehouse/
├── app/                          # Backend application
│   ├── __init__.py
│   ├── main.py                   # FastAPI app entry point
│   ├── config.py                 # Configuration constants
│   ├── routes/                   # API route handlers
│   │   ├── file_routes.py        # File upload/management
│   │   ├── column_mapping_routes.py # Column selection
│   │   └── relationship_routes.py   # Relationship management
│   └── services/                 # Business logic
│       ├── file_service.py       # File processing
│       └── column_mapping_service.py # Column management
├── frontend/                     # Angular application
│   ├── src/app/
│   │   ├── components/
│   │   │   ├── file-upload/      # File upload component
│   │   │   └── column-selection/ # Main data management
│   │   └── services/             # Frontend services
│   └── package.json
├── data/uploads/                 # Uploaded files storage
└── requirements.txt              # Python dependencies
```

---

## File Upload and Processing

### Upload Flow

1. **Frontend Upload**
   ```typescript
   // User selects files
   <input type="file" multiple accept=".xlsx,.xls,.csv" />
   
   // Upload to backend
   uploadFiles(files: FileList) {
     const formData = new FormData();
     for (let i = 0; i < files.length; i++) {
       formData.append('files', files[i]);
     }
     this.fileService.uploadFiles(formData).subscribe(...);
   }
   ```

2. **Backend Processing**
   ```python
   @router.post("/upload")
   async def upload_files(files: List[UploadFile] = File(...)):
       for file in files:
           # Validate file type
           if not file_service.is_valid_file(file.filename):
               continue
           
           # Read content
           content = await file.read()
           
           # Process (save + extract columns)
           result = file_service.process_upload(content, file.filename)
   ```

3. **File Service Processing**
   ```python
   def process_upload(self, file_content: bytes, filename: str):
       # 1. Validate file extension
       if not self.is_valid_file(filename):
           return None
       
       # 2. Save to disk
       file_path = self.save_file(file_content, filename)
       
       # 3. Extract column headers
       columns = self.extract_columns(file_path)
       
       # 4. Generate table name
       table_name = self.get_table_name(filename)
       
       return {
           "filename": filename,
           "table_name": table_name,
           "columns": columns,
           "file_path": file_path
       }
   ```

### Supported File Types

- **Excel Files**: `.xlsx`, `.xls`
- **CSV Files**: `.csv`
- **Smart Detection**: Excel files that are actually CSV get auto-detected

### Column Extraction

```python
def extract_columns(self, file_path: str) -> List[str]:
    if file_path.endswith(('.xlsx', '.xls')):
        try:
            df = pd.read_excel(file_path, nrows=0)  # Only headers
        except Exception as e:
            # Fallback to CSV if Excel fails
            if "Excel file format cannot be determined" in str(e):
                df = pd.read_csv(file_path, nrows=0)
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path, nrows=0)
    
    return df.columns.tolist()
```

---

## Data Joining and Relationships

### Relationship Types

1. **Simple Relationships**: One-to-One, One-to-Many, Many-to-One
2. **Composite Relationships**: Multiple column joins

### Composite Key Joins

```python
def get_joined_data(self, files: List[str], column_pairs: List[Dict], 
                   selected_columns: List[str], sample_size: int = 100):
    # Read data from files
    dataframes = {}
    for file in files:
        df = self.read_file_data(file, sample_size)
        dataframes[file] = df
    
    # Perform joins
    result_df = None
    for file in files[1:]:
        if result_df is None:
            result_df = dataframes[files[0]]
        
        # Create join conditions
        join_conditions = []
        for pair in column_pairs:
            if pair['table1'] == files[0] and pair['table2'] == file:
                join_conditions.append(
                    (result_df[pair['column1']] == dataframes[file][pair['column2']])
                )
        
        # Perform join
        if join_conditions:
            combined_condition = join_conditions[0]
            for condition in join_conditions[1:]:
                combined_condition = combined_condition & condition
            
            result_df = result_df[combined_condition].merge(
                dataframes[file], 
                left_on=[pair['column1'] for pair in column_pairs],
                right_on=[pair['column2'] for pair in column_pairs],
                how='inner'
            )
    
    # Filter to selected columns
    if selected_columns:
        result_df = result_df[selected_columns]
    
    return result_df
```

### Join Strategy

1. **Full Composite Key Join**: Try all specified conditions
2. **Fallback Strategy**: If no results, try with fewer conditions
3. **Flexible Matching**: Handle different data types and formats

---

## Frontend Components

### File Upload Component

**Location**: `frontend/src/app/components/file-upload/file-upload.component.ts`

**Features**:
- Drag & drop file upload
- Multiple file selection
- Progress indicators
- Error handling
- File validation

**Key Methods**:
```typescript
onUpload() {
  // Handle file upload
}

onFileSelected(event: any) {
  // Handle file selection
}

uploadFiles(files: FileList) {
  // Upload files to backend
}
```

### Column Selection Component

**Location**: `frontend/src/app/components/column-selection/column-selection.component.ts`

**Features**:
- Interactive column selection
- Relationship creation
- Data display
- Custom table naming
- Scrollable data tables

**Key Properties**:
```typescript
export class ColumnSelectionComponent {
  filesMetadata: any[] = [];
  selectedColumnsSummary: SelectedColumnsSummary | null = null;
  combinedTableStructure: CombinedTableStructure | null = null;
  customTableName = 'combined_table';
  compositeRelationships: any[] = [];
  actualDataTableData: any[] = [];
  // ... more properties
}
```

**Key Methods**:
```typescript
loadFilesMetadata() {
  // Load available files
}

selectColumn(file: string, column: string) {
  // Select/deselect columns
}

createCompositeRelationship() {
  // Create multi-column relationships
}

displayActualData() {
  // Display joined data
}

fetchJoinedData() {
  // Fetch data with relationships
}
```

---

## Backend Services

### File Service

**Location**: `app/services/file_service.py`

**Key Methods**:

```python
class FileService:
    def is_valid_file(self, filename: str) -> bool:
        """Validate file extension"""
    
    def save_file(self, file_content: bytes, filename: str) -> str:
        """Save file to disk"""
    
    def extract_columns(self, file_path: str) -> List[str]:
        """Extract column headers"""
    
    def process_upload(self, file_content: bytes, filename: str) -> Optional[Dict]:
        """Complete upload processing"""
    
    def read_file_data(self, filename: str, sample_size: int = 100) -> pd.DataFrame:
        """Read actual data from file"""
    
    def get_joined_data(self, files: List[str], column_pairs: List[Dict], 
                       selected_columns: List[str], sample_size: int = 100) -> pd.DataFrame:
        """Join multiple tables"""
```

### Column Mapping Service

**Location**: `app/services/column_mapping_service.py`

**Key Methods**:

```python
class ColumnMappingService:
    def get_selected_columns_summary(self) -> SelectedColumnsSummary:
        """Get summary of selected columns"""
    
    def create_composite_relationship(self, relationship: CompositeRelationshipRequest) -> bool:
        """Create composite relationship"""
    
    def get_combined_table_structure(self) -> CombinedTableStructure:
        """Get combined table structure"""
```

---

## API Endpoints

### File Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/files/upload` | Upload multiple files |
| GET | `/api/files/metadata` | Get all files metadata |
| GET | `/api/files/data/{filename}` | Get file data |
| POST | `/api/files/data/multiple` | Get multiple files data |
| POST | `/api/files/data/joined` | Get joined data |

### Column Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/columns/select` | Select/deselect columns |
| GET | `/api/columns/summary` | Get selected columns summary |
| POST | `/api/columns/create-composite-relationship` | Create composite relationship |

### Example API Calls

```bash
# Upload files
curl -X POST "http://localhost:8000/api/files/upload" \
  -F "files=@file1.xlsx" \
  -F "files=@file2.csv"

# Get metadata
curl "http://localhost:8000/api/files/metadata"

# Get joined data
curl -X POST "http://localhost:8000/api/files/data/joined" \
  -H "Content-Type: application/json" \
  -d '{
    "files": ["file1.xlsx", "file2.csv"],
    "column_pairs": [
      {"table1": "file1.xlsx", "column1": "id", "table2": "file2.csv", "column2": "user_id"}
    ],
    "selected_columns": ["id", "name", "email"],
    "sample_size": 100
  }'
```

---

## Configuration

### Backend Configuration

**File**: `app/config.py`

```python
from pathlib import Path

# File upload settings
UPLOAD_DIR = Path("data/uploads")
ALLOWED_EXTENSIONS = ['.xlsx', '.xls', '.csv']

# Sample size settings
DEFAULT_SAMPLE_SIZE = 100
MAX_SAMPLE_SIZE = 1000
```

### Frontend Configuration

**File**: `frontend/angular.json`

```json
{
  "projects": {
    "reports-datawarehouse": {
      "architect": {
        "serve": {
          "options": {
            "port": 4200
          }
        }
      }
    }
  }
}
```

---

## Installation and Setup

### Prerequisites

- Python 3.8+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
# Clone repository
git clone <repository-url>
cd reports-datawarehouse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

### Quick Start

```bash
# Use provided scripts
./start_all.sh        # Start both backend and frontend
./start_backend.sh    # Start only backend
./start_frontend.sh   # Start only frontend
```

---

## Usage Guide

### Step 1: Upload Files

1. Navigate to the file upload page
2. Select Excel or CSV files
3. Click "Upload Files"
4. Wait for processing to complete

### Step 2: Select Columns

1. Go to the column selection page
2. Choose files from the dropdown
3. Select desired columns
4. Click "Add to Selection"

### Step 3: Create Relationships

1. In the "Composite Key Relationships" section
2. Select source and target tables
3. Choose matching columns
4. Click "Create Relationship"

### Step 4: View Data

1. Set a custom table name (optional)
2. Click "Display Actual Data"
3. View the joined data in the scrollable table
4. Adjust sample size if needed

### Step 5: Export (Future Feature)

- Export to Excel
- Export to CSV
- Save as SQL queries

---

## Troubleshooting

### Common Issues

#### 1. File Upload Fails

**Problem**: Files not uploading
**Solution**: 
- Check file format (must be .xlsx, .xls, or .csv)
- Verify file size (not too large)
- Check backend logs for errors

#### 2. No Data After Join

**Problem**: Join operation returns no results
**Solution**:
- Verify column names match exactly
- Check data types (string vs number)
- Try with smaller sample size
- Check for null values in join columns

#### 3. Frontend Not Loading

**Problem**: Angular app not starting
**Solution**:
- Run `npm install` to install dependencies
- Check Node.js version (18+)
- Clear browser cache

#### 4. Backend Errors

**Problem**: FastAPI server errors
**Solution**:
- Activate virtual environment
- Install all requirements
- Check Python version (3.8+)
- Review error logs

### Debug Mode

Enable debug logging:

```python
# In app/main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Log Files

- Backend logs: Console output
- Frontend logs: Browser developer tools
- File processing logs: Check `data/uploads/` directory

---

## Future Features

### Planned Features

1. **Custom Table Builder**
   - UI ready, logic pending
   - Drag-and-drop table creation
   - Custom column definitions

2. **DuckDB Integration**
   - Configured but not active
   - In-process analytical database
   - Advanced SQL queries

3. **File Deletion**
   - UI ready, backend pending
   - Delete uploaded files
   - Clean up relationships

4. **Advanced Analytics**
   - Data visualization
   - Charts and graphs
   - Statistical analysis

5. **Export Features**
   - Export to multiple formats
   - Scheduled exports
   - Email reports

6. **User Management**
   - Authentication
   - User roles
   - Access control

7. **Database Integration**
   - Connect to external databases
   - Real-time data sync
   - Data warehouse features

---

## API Reference

### Data Models

#### FileMetadata
```typescript
interface FileMetadata {
  filename: string;
  columns: string[];
  size: number;
  table_name: string;
}
```

#### SelectedColumnsSummary
```typescript
interface SelectedColumnsSummary {
  total_columns: number;
  files: Array<{
    filename: string;
    selected_columns: string[];
  }>;
}
```

#### CombinedTableStructure
```typescript
interface CombinedTableStructure {
  table_name: string;
  source_tables: string[];
  column_count: number;
  columns: string[];
}
```

#### CompositeRelationshipRequest
```typescript
interface CompositeRelationshipRequest {
  table1: string;
  table2: string;
  column_pairs: Array<{
    column1: string;
    column2: string;
  }>;
  description: string;
}
```

### Error Responses

```json
{
  "detail": "Error message",
  "status_code": 400,
  "timestamp": "2025-01-02T10:30:00Z"
}
```

---

## Performance Considerations

### Sample Size Management

- **Default**: 100 rows per file
- **Maximum**: 1000 rows per file
- **Join Results**: Limited to 1000 rows
- **Configurable**: Via UI controls

### Memory Usage

- Files are read in chunks
- DataFrames are limited by sample size
- Garbage collection after processing

### File Size Limits

- **Recommended**: < 10MB per file
- **Maximum**: 50MB per file
- **Large Files**: Use sample size to limit data

---

## Security Considerations

### File Upload Security

- File type validation
- File size limits
- Path traversal protection
- Malicious file detection (future)

### Data Privacy

- Files stored locally
- No external data transmission
- User controls data access

### Future Security Features

- User authentication
- Role-based access
- Data encryption
- Audit logging

---

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

### Code Style

- **Python**: Follow PEP 8
- **TypeScript**: Use Angular style guide
- **Documentation**: Update this file for new features

### Testing

- Backend: Add unit tests
- Frontend: Add component tests
- Integration: Test full workflows

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## Support

For support and questions:

1. Check this documentation
2. Review error logs
3. Check GitHub issues
4. Contact development team

---

## Changelog

### Version 1.0.0 (Current)

- ✅ File upload and processing
- ✅ Column selection
- ✅ Relationship management
- ✅ Data joining
- ✅ Custom table naming
- ✅ Scrollable data display
- ✅ Sample size control

### Version 1.1.0 (Planned)

- 🔄 Custom table builder
- 🔄 DuckDB integration
- 🔄 File deletion
- 🔄 Advanced analytics

---

*Last Updated: January 2, 2025*
*Documentation Version: 1.0.0*