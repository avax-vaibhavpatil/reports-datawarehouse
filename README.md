# 📊 Excel Generator - Full Stack Project

A modern full-stack application for uploading Excel files, extracting column metadata, and building custom tables using DuckDB.

## 🚀 Tech Stack

- **Frontend**: Angular 20 + Angular Material UI
- **Backend**: FastAPI (Python 3.12+)
- **Database**: DuckDB (for Excel/CSV processing)
- **File Processing**: Excel/CSV reading with column extraction

## 🎯 Features

- **File Upload**: Drag & drop multiple Excel/CSV files
- **Column Extraction**: Automatically extract column headers from uploaded files
- **Metadata Display**: Beautiful Material UI table showing files and their columns
- **Custom Table Builder**: Define custom column structures
- **Real-time Processing**: Immediate feedback on upload status
- **Responsive Design**: Works on desktop and mobile devices

## 📁 Project Structure

```
excel_generator/
├── app/                          # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                   # FastAPI entry point
│   ├── config.py                 # Configuration constants
│   ├── routes/
│   │   └── file_routes.py        # API endpoints
│   └── services/
│       └── file_service.py       # Business logic & DuckDB integration
├── frontend/                     # Angular Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/
│   │   │   │   └── file-upload/  # Main file upload component
│   │   │   ├── services/
│   │   │   │   └── file.service.ts # API communication service
│   │   │   ├── app.component.ts  # Root component
│   │   │   ├── app.config.ts     # App configuration
│   │   │   └── app.routes.ts     # Routing
│   │   ├── styles.scss           # Global styles
│   │   ├── main.ts               # App entry point
│   │   └── index.html            # Main HTML
│   ├── package.json              # Angular dependencies
│   ├── angular.json              # Angular CLI config
│   └── tsconfig.json             # TypeScript config
├── requirements.txt               # Python dependencies
└── README.md                     # This file
```

## 🛠️ Setup Instructions

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **Angular CLI 20**

### Backend Setup (FastAPI)

1. **Navigate to project root:**
   ```bash
   cd excel_generator
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the FastAPI server:**
   ```bash
   cd app
   python main.py
   ```

   The API will be available at `http://localhost:8000`
   - API Documentation: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/api/files/health`

### Frontend Setup (Angular)

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

   The Angular app will be available at `http://localhost:4200`

## 🔧 API Endpoints

### File Upload
- **POST** `/api/files/upload` - Upload multiple Excel/CSV files
- **GET** `/api/files/metadata` - Get metadata for all uploaded files
- **GET** `/api/files/health` - Health check endpoint

### Request/Response Examples

**Upload Files:**
```bash
curl -X POST "http://localhost:8000/api/files/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "files=@sample.xlsx"
```

**Response:**
```json
{
  "files": [
    {
      "filename": "customers.xlsx",
      "columns": ["customer_id", "customer_name", "region"]
    }
  ],
  "total_uploaded": 1,
  "total_files": 1,
  "errors": []
}
```

## 🎨 UI Features

### File Upload Interface
- **Drag & Drop**: Intuitive file upload with visual feedback
- **File Validation**: Automatic validation of Excel/CSV files
- **Progress Indicators**: Real-time upload progress
- **File Preview**: See selected files before upload

### Metadata Display
- **Material Table**: Clean, responsive table layout
- **Column Chips**: Visual representation of file columns
- **File Icons**: Different icons for different file types
- **Actions**: View details and remove files

### Custom Table Builder
- **Column Input**: Comma-separated column definition
- **Form Validation**: Real-time validation feedback
- **Modern UI**: Material Design form controls

## 🔍 How It Works

1. **File Upload**: User selects or drags Excel/CSV files
2. **Backend Processing**: FastAPI receives files and processes them with DuckDB
3. **Column Extraction**: DuckDB reads file headers without loading full data
4. **Metadata Storage**: File information and columns stored in DuckDB
5. **Frontend Display**: Angular displays results in beautiful Material UI table
6. **Custom Tables**: Users can define custom column structures

## 🚀 Development

### Backend Development
- **Hot Reload**: FastAPI automatically reloads on code changes
- **Logging**: Comprehensive logging for debugging
- **Error Handling**: Graceful error handling with user-friendly messages
- **CORS**: Configured for Angular development server

### Frontend Development
- **Hot Reload**: Angular dev server with live reload
- **TypeScript**: Full type safety and IntelliSense
- **Material Design**: Consistent UI components
- **Responsive**: Mobile-first responsive design

## 🧪 Testing

### Backend Testing
```bash
cd app
python -m pytest tests/
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 📦 Production Build

### Backend
```bash
cd app
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run build
```

## 🔒 Security Features

- **File Type Validation**: Only Excel/CSV files allowed
- **File Size Limits**: Configurable maximum file size (default: 100MB)
- **CORS Configuration**: Secure cross-origin requests
- **Input Sanitization**: Safe file name handling

## 🌟 Future Enhancements

- **SQL Query Builder**: Visual SQL query construction
- **Data Joins**: Automatic join detection between files
- **Export Functionality**: Export processed data to various formats
- **User Authentication**: Multi-user support with file sharing
- **Advanced Analytics**: Data visualization and insights

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

**Backend won't start:**
- Check Python version (3.12+ required)
- Verify virtual environment is activated
- Check if port 8000 is available

**Frontend won't start:**
- Ensure Node.js 18+ is installed
- Check if port 4200 is available
- Verify all dependencies are installed

**File upload fails:**
- Check backend is running on port 8000
- Verify file format (.xlsx, .xls, .csv)
- Check file size (max 100MB)

**CORS errors:**
- Ensure backend CORS is configured for `http://localhost:4200`
- Check browser console for specific error messages

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review FastAPI logs for backend errors
- Check browser console for frontend errors
- Create an issue in the repository

---

**Happy Excel Processing! 🎉** 