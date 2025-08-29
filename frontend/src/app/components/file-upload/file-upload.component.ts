import { Component, OnInit, ViewChild, ElementRef } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatInputModule } from '@angular/material/input';
import { MatFormFieldModule } from '@angular/material/form-field';
// MatDividerModule removed as it's not needed

import { FileService, FileMetadata, UploadResponse } from '../../services/file.service';

@Component({
  selector: 'app-file-upload',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatChipsModule,
    MatProgressBarModule,
    MatSnackBarModule,
    MatInputModule,
    MatFormFieldModule
  ],
  template: `
    <div class="file-upload-container">
      <!-- File Upload Section -->
      <mat-card class="upload-card">
        <mat-card-header>
          <mat-card-title>
            <mat-icon>cloud_upload</mat-icon>
            Import Excel Files
          </mat-card-title>
          <mat-card-subtitle>
            Upload multiple Excel (.xlsx, .xls) or CSV files to analyze their structure
          </mat-card-subtitle>
        </mat-card-header>
        
        <mat-card-content>
          <!-- Drag & Drop Area -->
          <div 
            class="file-upload-area"
            [class.drag-over]="isDragOver"
            (dragover)="onDragOver($event)"
            (dragleave)="onDragLeave($event)"
            (drop)="onDrop($event)"
            (click)="fileInput.click()"
          >
            <mat-icon class="upload-icon">cloud_upload</mat-icon>
            <h3>Drop files here or click to browse</h3>
            <p>Supports .xlsx, .xls, and .csv files</p>
            <p class="file-limit">Maximum file size: 100MB</p>
          </div>
          
          <!-- Hidden file input -->
          <input
            #fileInput
            type="file"
            multiple
            accept=".xlsx,.xls,.csv"
            (change)="onFileSelected($event)"
            style="display: none;"
          />
          
          <!-- Selected Files Preview -->
          <div *ngIf="selectedFiles.length > 0" class="selected-files">
            <h4>Selected Files ({{ selectedFiles.length }})</h4>
            <div class="file-list">
              <div 
                *ngFor="let file of selectedFiles; let i = index" 
                class="file-item"
              >
                <div class="file-info">
                  <span class="file-icon">{{ getFileIcon(file.name) }}</span>
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-size">{{ formatFileSize(file.size) }}</span>
                </div>
                <button 
                  mat-icon-button 
                  color="warn" 
                  (click)="removeFile(i)"
                  class="remove-btn"
                >
                  <mat-icon>close</mat-icon>
                </button>
              </div>
            </div>
            
            <div class="upload-actions">
              <button 
                mat-raised-button 
                color="primary" 
                (click)="uploadFiles()"
                [disabled]="isUploading || selectedFiles.length === 0"
                class="upload-btn"
              >
                <mat-icon>upload</mat-icon>
                Upload {{ selectedFiles.length }} File{{ selectedFiles.length !== 1 ? 's' : '' }}
              </button>
              
              <button 
                mat-button 
                (click)="clearSelection()"
                [disabled]="isUploading"
              >
                Clear Selection
              </button>
            </div>
          </div>
          
          <!-- Upload Progress -->
          <div *ngIf="isUploading" class="upload-progress">
            <mat-progress-bar 
              mode="indeterminate" 
              color="primary"
            ></mat-progress-bar>
            <p>Processing files...</p>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Custom Table Builder Section -->
      <mat-card class="custom-table-card">
        <mat-card-header>
          <mat-card-title>
            <mat-icon>table_chart</mat-icon>
            Custom Table Builder
          </mat-card-title>
          <mat-card-subtitle>
            Define custom columns for creating new tables
          </mat-card-subtitle>
        </mat-card-header>
        
        <mat-card-content>
          <form [formGroup]="customTableForm" class="custom-table-form">
            <mat-form-field appearance="outline" class="full-width">
              <mat-label>Column Names (comma-separated)</mat-label>
              <input 
                matInput 
                formControlName="columns"
                placeholder="e.g., customer_id, customer_name, region, amount"
              >
              <mat-hint>Enter column names separated by commas</mat-hint>
            </mat-form-field>
            
            <div class="form-actions">
              <button 
                mat-raised-button 
                color="accent"
                (click)="createCustomTable()"
                [disabled]="!customTableForm.valid"
              >
                <mat-icon>add</mat-icon>
                Create Custom Table
              </button>
            </div>
          </form>
        </mat-card-content>
      </mat-card>

      <!-- Files Metadata Table -->
      <mat-card class="metadata-card" *ngIf="filesMetadata.length > 0">
        <mat-card-header>
          <mat-card-title>
            <mat-icon>analytics</mat-icon>
            Uploaded Files & Columns
          </mat-card-title>
          <mat-card-subtitle>
            {{ filesMetadata.length }} file{{ filesMetadata.length !== 1 ? 's' : '' }} processed
          </mat-card-subtitle>
        </mat-card-header>
        
        <mat-card-content>
          <div class="table-container">
            <table mat-table [dataSource]="filesMetadata" class="custom-table">
              <!-- Filename Column -->
              <ng-container matColumnDef="filename">
                <th mat-header-cell *matHeaderCellDef>File Name</th>
                <td mat-cell *matCellDef="let file">
                  <div class="filename-cell">
                    <span class="file-icon">{{ getFileIcon(file.filename) }}</span>
                    <span class="filename">{{ file.filename }}</span>
                  </div>
                </td>
              </ng-container>

              <!-- Columns Column -->
              <ng-container matColumnDef="columns">
                <th mat-header-cell *matHeaderCellDef>Columns</th>
                <td mat-cell *matCellDef="let file">
                  <div class="columns-container">
                    <mat-chip 
                      *ngFor="let column of file.columns" 
                      class="column-chip"
                      color="primary"
                      variant="outlined"
                    >
                      {{ column }}
                    </mat-chip>
                  </div>
                </td>
              </ng-container>

              <!-- Actions Column -->
              <ng-container matColumnDef="actions">
                <th mat-header-cell *matHeaderCellDef>Actions</th>
                <td mat-cell *matCellDef="let file">
                  <button 
                    mat-icon-button 
                    color="primary"
                    matTooltip="View file details"
                    (click)="viewFileDetails(file)"
                  >
                    <mat-icon>visibility</mat-icon>
                  </button>
                  <button 
                    mat-icon-button 
                    color="warn"
                    matTooltip="Remove file"
                    (click)="removeFileFromList(file)"
                  >
                    <mat-icon>delete</mat-icon>
                  </button>
                </td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
            </table>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Empty State -->
      <mat-card *ngIf="filesMetadata.length === 0 && !isUploading" class="empty-state">
        <mat-card-content class="empty-content">
          <mat-icon class="empty-icon">folder_open</mat-icon>
          <h3>No files uploaded yet</h3>
          <p>Upload your first Excel file to see its column structure</p>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .file-upload-container {
      max-width: 1200px;
      margin: 0 auto;
    }

    .upload-card, .custom-table-card, .metadata-card, .empty-state {
      margin-bottom: 24px;
    }

    .file-upload-area {
      border: 2px dashed #ccc;
      border-radius: 12px;
      padding: 60px 40px;
      text-align: center;
      transition: all 0.3s ease;
      background: #fafafa;
      cursor: pointer;
      
      &:hover {
        border-color: #3f51b5;
        background: #f0f4ff;
        transform: translateY(-2px);
      }
      
      &.drag-over {
        border-color: #3f51b5;
        background: #e3f2fd;
        transform: scale(1.02);
      }
    }

    .upload-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: #3f51b5;
      margin-bottom: 16px;
    }

    .file-limit {
      color: #666;
      font-size: 0.9rem;
      margin-top: 8px;
    }

    .selected-files {
      margin-top: 24px;
    }

    .file-list {
      margin: 16px 0;
    }

    .file-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 12px 16px;
      background: white;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      margin-bottom: 8px;
      transition: all 0.2s ease;
      
      &:hover {
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
      }
    }

    .file-info {
      display: flex;
      align-items: center;
      gap: 12px;
    }

    .file-icon {
      font-size: 20px;
    }

    .file-name {
      font-weight: 500;
      color: #333;
    }

    .file-size {
      color: #666;
      font-size: 0.9rem;
    }

    .upload-actions {
      display: flex;
      gap: 16px;
      align-items: center;
      margin-top: 16px;
    }

    .upload-btn {
      min-width: 200px;
    }

    .upload-progress {
      margin-top: 24px;
      text-align: center;
    }

    .custom-table-form {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .full-width {
      width: 100%;
    }

    .form-actions {
      display: flex;
      justify-content: flex-end;
    }

    .table-container {
      overflow-x: auto;
    }

    .custom-table {
      width: 100%;
    }

    .filename-cell {
      display: flex;
      align-items: center;
      gap: 8px;
    }

    .file-icon {
      font-size: 18px;
    }

    .filename {
      font-weight: 500;
    }

    .columns-container {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
    }

    .column-chip {
      font-size: 12px;
      height: 24px;
    }

    .empty-content {
      text-align: center;
      padding: 60px 20px;
    }

    .empty-icon {
      font-size: 64px;
      width: 64px;
      height: 64px;
      color: #ccc;
      margin-bottom: 16px;
    }

    .empty-content h3 {
      color: #666;
      margin: 16px 0 8px 0;
    }

    .empty-content p {
      color: #999;
      margin: 0;
    }

    @media (max-width: 768px) {
      .file-upload-area {
        padding: 40px 20px;
      }
      
      .upload-actions {
        flex-direction: column;
        align-items: stretch;
      }
      
      .upload-btn {
        min-width: auto;
      }
    }
  `]
})
export class FileUploadComponent implements OnInit {
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  selectedFiles: File[] = [];
  filesMetadata: FileMetadata[] = [];
  isUploading = false;
  isDragOver = false;
  displayedColumns: string[] = ['filename', 'columns', 'actions'];
  
  customTableForm: FormGroup;

  constructor(
    private fileService: FileService,
    private formBuilder: FormBuilder,
    private snackBar: MatSnackBar
  ) {
    this.customTableForm = this.formBuilder.group({
      columns: ['', []]
    });
  }

  ngOnInit(): void {
    this.loadFilesMetadata();
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = true;
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    this.isDragOver = false;
    
    const files = event.dataTransfer?.files;
    if (files) {
      this.addFiles(Array.from(files));
    }
  }

  onFileSelected(event: any): void {
    const files = event.target.files;
    if (files) {
      this.addFiles(Array.from(files));
    }
  }

  addFiles(files: File[]): void {
    const validFiles = files.filter(file => this.fileService.isValidFile(file));
    
    if (validFiles.length !== files.length) {
      this.showNotification('Some files were skipped (invalid format)', 'warning');
    }
    
    this.selectedFiles.push(...validFiles);
  }

  removeFile(index: number): void {
    this.selectedFiles.splice(index, 1);
  }

  clearSelection(): void {
    this.selectedFiles = [];
  }

  uploadFiles(): void {
    if (this.selectedFiles.length === 0) return;

    this.isUploading = true;
    
    this.fileService.uploadFiles(this.selectedFiles).subscribe({
      next: (response: UploadResponse) => {
        this.isUploading = false;
        
        if (response.total_uploaded > 0) {
          this.showNotification(
            `Successfully uploaded ${response.total_uploaded} file(s)`, 
            'success'
          );
          
          // Clear selection and reload metadata
          this.selectedFiles = [];
          this.loadFilesMetadata();
        }
        
        if (response.errors.length > 0) {
          this.showNotification(
            `Upload completed with ${response.errors.length} error(s)`, 
            'warning'
          );
        }
      },
      error: (error) => {
        this.isUploading = false;
        this.showNotification('Upload failed. Please try again.', 'error');
        console.error('Upload error:', error);
      }
    });
  }

  loadFilesMetadata(): void {
    this.fileService.getFilesMetadata().subscribe({
      next: (response) => {
        this.filesMetadata = response.files;
      },
      error: (error) => {
        console.error('Error loading metadata:', error);
        this.showNotification('Failed to load file metadata', 'error');
      }
    });
  }

  createCustomTable(): void {
    if (this.customTableForm.valid) {
      const columns = this.customTableForm.get('columns')?.value;
      this.showNotification(`Custom table with columns: ${columns}`, 'success');
      // TODO: Implement custom table creation logic
    }
  }

  viewFileDetails(file: FileMetadata): void {
    this.showNotification(`Viewing details for ${file.filename}`, 'info');
    // TODO: Implement file details view
  }

  removeFileFromList(file: FileMetadata): void {
    this.showNotification(`Remove functionality for ${file.filename}`, 'info');
    // TODO: Implement file removal from backend
  }

  getFileIcon(filename: string): string {
    return this.fileService.getFileIcon(filename);
  }

  formatFileSize(bytes: number): string {
    return this.fileService.formatFileSize(bytes);
  }

  private showNotification(message: string, type: 'success' | 'error' | 'warning' | 'info'): void {
    this.snackBar.open(message, 'Close', {
      duration: 4000,
      horizontalPosition: 'center',
      verticalPosition: 'bottom',
      panelClass: `snackbar-${type}`
    });
  }
} 