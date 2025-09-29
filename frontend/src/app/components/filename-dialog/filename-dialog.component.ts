import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { FormsModule } from '@angular/forms';

export interface FilenameDialogData {
  defaultFilename: string;
  useBackendExport?: boolean;
  queryConfig?: any;
}

@Component({
  selector: 'app-filename-dialog',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    FormsModule
  ],
  template: `
    <h2 mat-dialog-title>Export to CSV</h2>
    <mat-dialog-content>
      <p>Enter a filename for your CSV export:</p>
      <mat-form-field appearance="outline" class="full-width">
        <mat-label>Filename</mat-label>
        <input 
          matInput 
          [(ngModel)]="filename" 
          placeholder="Enter filename"
          (keyup.enter)="onExport()"
        >
        <mat-hint>.csv extension will be added automatically</mat-hint>
      </mat-form-field>
      
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="onCancel()">Cancel</button>
      <button mat-raised-button color="primary" (click)="onExport()" [disabled]="!filename.trim()">
        Export
      </button>
    </mat-dialog-actions>
  `,
  styles: [`
    .full-width {
      width: 100%;
    }
    
    mat-dialog-content {
      min-width: 300px;
    }
    
    mat-dialog-actions {
      padding: 16px 0;
    }
  `]
})
export class FilenameDialogComponent {
  filename: string = '';

  constructor(
    public dialogRef: MatDialogRef<FilenameDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: FilenameDialogData
  ) {
    // Remove .csv extension from default filename for user input
    this.filename = this.data.defaultFilename.replace('.csv', '');
  }

  onCancel(): void {
    this.dialogRef.close(null);
  }

  onExport(): void {
    if (this.filename.trim()) {
      // Ensure .csv extension
      const finalFilename = this.filename.trim().endsWith('.csv') 
        ? this.filename.trim() 
        : this.filename.trim() + '.csv';
      
      // Always use backend export with query config
      this.dialogRef.close({
        filename: finalFilename,
        queryConfig: this.data.queryConfig
      });
    }
  }
}