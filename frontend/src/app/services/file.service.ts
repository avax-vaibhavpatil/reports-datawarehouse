import { Injectable } from '@angular/core';
import { HttpClient, HttpEvent, HttpEventType } from '@angular/common/http';
import { Observable, map } from 'rxjs';

export interface FileMetadata {
  filename: string;
  columns: string[];
  table_name?: string;
  upload_time?: string;
}

export interface UploadResponse {
  files: FileMetadata[];
  total_uploaded: number;
  total_files: number;
  errors: string[];
}

export interface MetadataResponse {
  files: FileMetadata[];
  total_files: number;
}

export interface FileDataResponse {
  filename: string;
  sample_size: number;
  total_rows: number;
  data: any[];
}

export interface MultipleFilesDataRequest {
  filenames: string[];
  sample_size: number;
}

export interface MultipleFilesDataResponse {
  sample_size: number;
  files_data: { [filename: string]: any[] };
  total_files: number;
  files_with_data: number;
}

@Injectable({
  providedIn: 'root'
})
export class FileService {
  private readonly apiUrl = 'http://localhost:8000/api/files';

  constructor(private http: HttpClient) {}

  /**
   * Upload multiple files to the backend
   */
  uploadFiles(files: File[]): Observable<UploadResponse> {
    const formData = new FormData();
    
    files.forEach(file => {
      formData.append('files', file, file.name);
    });

    return this.http.post<UploadResponse>(`${this.apiUrl}/upload`, formData);
  }

  /**
   * Get metadata for all uploaded files
   */
  getFilesMetadata(): Observable<MetadataResponse> {
    return this.http.get<MetadataResponse>(`${this.apiUrl}/metadata`);
  }

  /**
   * Check if file is valid Excel/CSV
   */
  isValidFile(file: File): boolean {
    const allowedTypes = [
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // .xlsx
      'application/vnd.ms-excel', // .xls
      'text/csv', // .csv
      'application/csv'
    ];
    
    const allowedExtensions = ['.xlsx', '.xls', '.csv'];
    const fileName = file.name.toLowerCase();
    
    return allowedTypes.includes(file.type) || 
           allowedExtensions.some(ext => fileName.endsWith(ext));
  }

  /**
   * Get file size in human readable format
   */
  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  /**
   * Get file icon based on type
   */
  getFileIcon(filename: string): string {
    const ext = filename.toLowerCase().split('.').pop();
    
    switch (ext) {
      case 'xlsx':
        return '📊';
      case 'xls':
        return '📈';
      case 'csv':
        return '📋';
      default:
        return '📄';
    }
  }

  /**
   * Get actual data from a specific file
   */
  getFileData(filename: string, sampleSize: number = 100): Observable<FileDataResponse> {
    return this.http.get<FileDataResponse>(`${this.apiUrl}/data/${filename}?sample_size=${sampleSize}`);
  }

  /**
   * Get data from multiple files
   */
  getMultipleFilesData(request: MultipleFilesDataRequest): Observable<MultipleFilesDataResponse> {
    return this.http.post<MultipleFilesDataResponse>(`${this.apiUrl}/data/multiple`, request);
  }

  /**
   * Get joined data from multiple files
   */
  getJoinedData(filenames: string[], joinConditions: any[], selectedColumns: string[] = [], sampleSize: number = 100): Observable<any> {
    const request = {
      filenames: filenames,
      join_conditions: joinConditions,
      selected_columns: selectedColumns,
      sample_size: sampleSize
    };
    return this.http.post(`${this.apiUrl}/data/joined`, request);
  }
} 