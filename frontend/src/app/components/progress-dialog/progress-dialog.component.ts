import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';
import { interval, Subscription } from 'rxjs';

export interface ProgressDialogData {
  title: string;
  message: string;
  totalRows: number;
  chunkSize: number;
  preserveOrder: boolean;
}

export interface ProgressUpdate {
  inserted_rows: number;
  total_rows: number;
  progress_percentage: number;
  elapsed_time: number;
  remaining_time: number;
  chunk_size: number;
  rows_per_second: number;
}

@Component({
  selector: 'app-progress-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatProgressBarModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule
  ],
  template: `
    <div class="progress-dialog">
      <h2 mat-dialog-title>{{ data.title }}</h2>
      
      <mat-dialog-content>
        <div class="progress-info">
          <p class="message">{{ data.message }}</p>
          
          <div class="progress-details">
            <div class="progress-bar-container">
              <mat-progress-bar 
                mode="determinate" 
                [value]="progressPercentage">
              </mat-progress-bar>
              <div class="progress-text">{{ progressPercentage }}%</div>
            </div>
            
            <div class="stats-grid">
              <div class="stat-item">
                <mat-icon>table_rows</mat-icon>
                <div class="stat-content">
                  <div class="stat-label">Rows Inserted</div>
                  <div class="stat-value">{{ insertedRows | number }} / {{ totalRows | number }}</div>
                </div>
              </div>
              
              <div class="stat-item">
                <mat-icon>speed</mat-icon>
                <div class="stat-content">
                  <div class="stat-label">Speed</div>
                  <div class="stat-value">{{ rowsPerSecond | number:'1.0-1' }} rows/sec</div>
                </div>
              </div>
              
              <div class="stat-item">
                <mat-icon>schedule</mat-icon>
                <div class="stat-content">
                  <div class="stat-label">Elapsed Time</div>
                  <div class="stat-value">{{ formatTime(elapsedTime) }}</div>
                </div>
              </div>
              
              <div class="stat-item">
                <mat-icon>timer</mat-icon>
                <div class="stat-content">
                  <div class="stat-label">Remaining Time</div>
                  <div class="stat-value">{{ formatTime(remainingTime) }}</div>
                </div>
              </div>
            </div>
            
            <div class="chunk-info">
              <small>Chunk Size: {{ chunkSize | number }} rows | Order: {{ preserveOrder ? 'Descending' : 'Ascending' }}</small>
            </div>
          </div>
        </div>
      </mat-dialog-content>
      
      <mat-dialog-actions align="end">
        <button mat-button (click)="onCancel()" [disabled]="isCompleted">
          {{ isCompleted ? 'Close' : 'Cancel' }}
        </button>
      </mat-dialog-actions>
    </div>
  `,
  styles: [`
    .progress-dialog {
      min-width: 500px;
      max-width: 600px;
    }
    
    .progress-info {
      padding: 16px 0;
    }
    
    .message {
      margin-bottom: 24px;
      font-size: 16px;
      color: #666;
    }
    
    .progress-details {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .progress-bar-container {
      position: relative;
    }
    
    .progress-text {
      text-align: center;
      margin-top: 8px;
      font-weight: bold;
      font-size: 18px;
      color: #1976d2;
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 12px;
      background: #f5f5f5;
      border-radius: 8px;
    }
    
    .stat-item mat-icon {
      color: #1976d2;
    }
    
    .stat-content {
      flex: 1;
    }
    
    .stat-label {
      font-size: 12px;
      color: #666;
      margin-bottom: 4px;
    }
    
    .stat-value {
      font-size: 16px;
      font-weight: bold;
      color: #333;
    }
    
    .chunk-info {
      text-align: center;
      color: #666;
      font-style: italic;
    }
    
    mat-progress-bar {
      height: 8px;
      border-radius: 4px;
    }
  `]
})
export class ProgressDialogComponent implements OnInit, OnDestroy {
  progressPercentage = 0;
  insertedRows = 0;
  totalRows = 0;
  rowsPerSecond = 0;
  elapsedTime = 0;
  remainingTime = 0;
  chunkSize = 1000;
  preserveOrder = true;
  isCompleted = false;
  
  private progressSubscription?: Subscription;

  constructor(
    public dialogRef: MatDialogRef<ProgressDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: ProgressDialogData
  ) {
    this.totalRows = data.totalRows;
    this.chunkSize = data.chunkSize;
    this.preserveOrder = data.preserveOrder;
  }

  ngOnInit(): void {
    // Start progress tracking
    this.startProgressTracking();
  }

  ngOnDestroy(): void {
    if (this.progressSubscription) {
      this.progressSubscription.unsubscribe();
    }
  }

  private startProgressTracking(): void {
    // Simulate progress updates (in real implementation, this would come from WebSocket or polling)
    this.progressSubscription = interval(1000).subscribe(() => {
      // This would be replaced with actual progress updates from the backend
      this.simulateProgress();
    });
  }

  private simulateProgress(): void {
    // Simulate progress (remove this in real implementation)
    if (this.insertedRows < this.totalRows) {
      const increment = Math.min(this.chunkSize, this.totalRows - this.insertedRows);
      this.insertedRows += increment;
      this.progressPercentage = (this.insertedRows / this.totalRows) * 100;
      this.elapsedTime += 1;
      this.rowsPerSecond = this.insertedRows / this.elapsedTime;
      this.remainingTime = ((this.totalRows - this.insertedRows) / this.rowsPerSecond);
      
      if (this.insertedRows >= this.totalRows) {
        this.isCompleted = true;
        this.progressPercentage = 100;
      }
    }
  }

  updateProgress(progress: ProgressUpdate): void {
    this.insertedRows = progress.inserted_rows;
    this.totalRows = progress.total_rows;
    this.progressPercentage = progress.progress_percentage;
    this.elapsedTime = progress.elapsed_time;
    this.remainingTime = progress.remaining_time;
    this.rowsPerSecond = progress.rows_per_second;
    
    if (this.insertedRows >= this.totalRows) {
      this.isCompleted = true;
      this.progressPercentage = 100;
    }
  }

  formatTime(seconds: number): string {
    if (seconds < 60) {
      return `${Math.round(seconds)}s`;
    } else if (seconds < 3600) {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = Math.round(seconds % 60);
      return `${minutes}m ${remainingSeconds}s`;
    } else {
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      return `${hours}h ${minutes}m`;
    }
  }

  onCancel(): void {
    if (this.isCompleted) {
      this.dialogRef.close({ success: true, completed: true });
    } else {
      this.dialogRef.close({ success: false, cancelled: true });
    }
  }
}