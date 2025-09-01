import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatDividerModule } from '@angular/material/divider';
import { MatSelectModule } from '@angular/material/select';
import { MatInputModule } from '@angular/material/input';
import { MatProgressBarModule } from '@angular/material/progress-bar';

import { ColumnMappingService, SelectedColumnsSummary, ColumnMappingSummary, CombinedTableStructure } from '../../services/column-mapping.service';
import { FileService } from '../../services/file.service';

@Component({
  selector: 'app-column-selection',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatCheckboxModule,
    MatSnackBarModule,
    MatDividerModule,
    MatSelectModule,
    MatInputModule,
    MatProgressBarModule
  ],
  template: `
    <div class="column-selection-container">
      <!-- Header -->
      <mat-card class="header-card">
        <mat-card-header>
          <mat-card-title>
            🎯 Column Selection & Mapping
          </mat-card-title>
          <mat-card-subtitle>
            Select columns from different tables to create relationships and build a combined table
          </mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div class="summary-stats" *ngIf="selectedColumnsSummary">
            <div class="stat-item">
              <span class="stat-number">{{ selectedColumnsSummary.total_tables || 0 }}</span>
              <span class="stat-label">Tables</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ selectedColumnsSummary.total_columns || 0 }}</span>
              <span class="stat-label">Columns</span>
            </div>
            <div class="stat-item">
              <span class="stat-number">{{ columnMappingsSummary?.total_mappings || 0 }}</span>
              <span class="stat-label">Relationships</span>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Column Selection Section -->
      <mat-card class="selection-card" *ngIf="filesMetadata.length > 0">
        <mat-card-header>
          <mat-card-title>Select Columns from Tables</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="table-selection" *ngFor="let file of filesMetadata">
            <div class="table-header">
              <h3>{{ file.filename }}</h3>
              <span class="table-info">{{ (file.columns || []).length }} columns</span>
            </div>
            
            <div class="columns-grid">
              <div class="column-item" *ngFor="let column of file.columns || []">
                <mat-checkbox 
                  [checked]="isColumnSelected(file.filename, column)"
                  (change)="onColumnSelectionChange(file.filename, column, $event.checked)">
                  <span class="column-name">{{ column }}</span>
                  <span class="column-notation">{{ file.filename }}.{{ column }}</span>
                </mat-checkbox>
              </div>
            </div>
            
            <mat-divider></mat-divider>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Column Mappings Section -->
      <mat-card class="mappings-card" *ngIf="columnMappingsSummary && columnMappingsSummary.total_mappings > 0">
        <mat-card-header>
          <mat-card-title>🔗 Detected Column Relationships</mat-card-title>
          <mat-card-subtitle>
            Automatically detected relationships between selected columns
          </mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div class="mappings-list">
            <div class="mapping-item" *ngFor="let mapping of columnMappingsSummary.mappings || []; let i = index">
              <div class="mapping-content">
                <span class="mapping-from">{{ mapping.from_table }}.{{ mapping.from_column }}</span>
                <span class="mapping-arrow">=</span>
                <span class="mapping-to">{{ mapping.to_table }}.{{ mapping.to_column }}</span>
              </div>
              <div class="mapping-description">{{ mapping.description }}</div>
              <div class="mapping-actions">
                <button 
                  mat-icon-button 
                  color="warn" 
                  (click)="deleteDetectedRelationship(i)"
                  matTooltip="Delete this relationship"
                  class="delete-btn">
                  <mat-icon>delete</mat-icon>
                </button>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Manual Relationship Creation -->
      <mat-card class="manual-relationship-card">
        <mat-card-header>
          <mat-card-title>🔧 Manual Relationship Creation</mat-card-title>
          <mat-card-subtitle>
            Create custom relationships between columns from different tables
          </mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div class="manual-relationship-form">
            <div class="form-row">
              <div class="form-group">
                <label>Source Table & Column:</label>
                <div class="table-column-selector">
                  <select [(ngModel)]="manualRelationship.sourceTable" (change)="onSourceTableChange()">
                    <option value="">Select Table</option>
                    <option *ngFor="let file of filesMetadata" [value]="file.filename">
                      {{ file.filename }}
                    </option>
                  </select>
                  <select [(ngModel)]="manualRelationship.sourceColumn" [disabled]="!manualRelationship.sourceTable">
                    <option value="">Select Column</option>
                    <option *ngFor="let column of getSourceColumns()" [value]="column">
                      {{ column }}
                    </option>
                  </select>
                </div>
              </div>
              
              <div class="form-group">
                <label>Target Table & Column:</label>
                <div class="table-column-selector">
                  <select [(ngModel)]="manualRelationship.targetTable" (change)="onTargetTableChange()">
                    <option value="">Select Table</option>
                    <option *ngFor="let file of filesMetadata" [value]="file.filename">
                      {{ file.filename }}
                    </option>
                  </select>
                  <select [(ngModel)]="manualRelationship.targetColumn" [disabled]="!manualRelationship.targetTable">
                    <option value="">Select Column</option>
                    <option *ngFor="let column of getTargetColumns()" [value]="column">
                      {{ column }}
                    </option>
                  </select>
                </div>
              </div>
            </div>
            
            <div class="form-row">
              <div class="form-group">
                <label>Relationship Type:</label>
                <select [(ngModel)]="manualRelationship.relationshipType">
                  <option value="one_to_one">One-to-One</option>
                  <option value="one_to_many">One-to-Many</option>
                  <option value="many_to_one">Many-to-One</option>
                  <option value="many_to_many">Many-to-Many</option>
                </select>
              </div>
              
              <div class="form-group">
                <label>Description:</label>
                <input type="text" [(ngModel)]="manualRelationship.description" 
                       placeholder="e.g., Customer ID relationship between orders and customers">
              </div>
            </div>
            
            <div class="form-actions">
              <button 
                mat-raised-button 
                color="primary" 
                (click)="createManualRelationship()"
                [disabled]="!isManualRelationshipValid()"
                class="create-btn">
                <mat-icon>🔗</mat-icon>
                Create Relationship
              </button>
            </div>
          </div>
          
          <!-- Manual Relationships List -->
          <div class="manual-relationships-list" *ngIf="manualRelationships.length > 0">
            <h4>Manual Relationships Created:</h4>
            <div class="relationship-item" *ngFor="let rel of manualRelationships; let i = index">
              <div class="relationship-content">
                <span class="relationship-from">{{ rel.source_table }}.{{ rel.source_column }}</span>
                <span class="relationship-arrow">→</span>
                <span class="relationship-to">{{ rel.target_table }}.{{ rel.target_column }}</span>
                <span class="relationship-type">({{ rel.relationship_type }})</span>
              </div>
              <div class="relationship-description">{{ rel.description }}</div>
              <div class="relationship-actions">
                <button mat-icon-button color="warn" (click)="deleteManualRelationship(rel.id)" class="delete-btn">
                  <mat-icon>delete</mat-icon>
                </button>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Combined Table Structure -->
      <mat-card class="combined-table-card" *ngIf="combinedTableStructure">
        <mat-card-header>
          <mat-card-title>📊 New Combined Table Structure</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="table-info">
            <p><strong>Table Name:</strong> {{ combinedTableStructure.table_name }}</p>
            <p><strong>Source Tables:</strong> {{ combinedTableStructure.source_tables?.join(', ') || 'None' }}</p>
            <p><strong>Total Columns:</strong> {{ combinedTableStructure.column_count }}</p>
          </div>
          
          <div class="columns-display">
            <h4>Selected Columns:</h4>
            <div class="columns-grid-display">
              <mat-chip *ngFor="let column of combinedTableStructure.columns || []" class="column-chip">
                {{ column }}
              </mat-chip>
            </div>
          </div>
          
          <!-- Display Buttons -->
          <div class="display-actions" style="margin-top: 20px; text-align: center;">
            <button 
              mat-raised-button 
              color="accent" 
              (click)="displayCreatedColumnsTable()"
              [disabled]="!combinedTableStructure || combinedTableStructure.column_count === 0"
              class="display-btn">
              <mat-icon>📋</mat-icon>
              Display Created Columns Table
            </button>
            
            <button 
              mat-raised-button 
              color="primary" 
              (click)="displayActualData()"
              [disabled]="!combinedTableStructure || combinedTableStructure.column_count === 0"
              class="data-btn">
              <mat-icon>📊</mat-icon>
              Display Actual Data
            </button>
            
            <button 
              mat-raised-button 
              color="warn" 
              (click)="testSingleFileData()"
              class="test-btn">
              <mat-icon>🧪</mat-icon>
              Test Single File
            </button>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Created Columns Table Display -->
      <mat-card class="created-columns-table-card" *ngIf="showCreatedColumnsTable && createdColumnsTableData.length > 0">
        <mat-card-header>
          <mat-card-title>📋 Created Columns Table View</mat-card-title>
          <mat-card-subtitle>
            Detailed view of all selected columns with their source table information
          </mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div class="table-container">
            <table mat-table [dataSource]="createdColumnsTableData" class="created-columns-table">
              <!-- Table Name Column -->
              <ng-container matColumnDef="table_name">
                <th mat-header-cell *matHeaderCellDef>Table Name</th>
                <td mat-cell *matCellDef="let element">{{ element.table_name }}</td>
              </ng-container>

              <!-- Column Name Column -->
              <ng-container matColumnDef="column_name">
                <th mat-header-cell *matHeaderCellDef>Column Name</th>
                <td mat-cell *matCellDef="let element">{{ element.column_name }}</td>
              </ng-container>

              <!-- Full Path Column -->
              <ng-container matColumnDef="full_path">
                <th mat-header-cell *matHeaderCellDef>Full Path</th>
                <td mat-cell *matCellDef="let element">{{ element.full_path }}</td>
              </ng-container>

              <!-- Data Type Column -->
              <ng-container matColumnDef="data_type">
                <th mat-header-cell *matHeaderCellDef>Data Type</th>
                <td mat-cell *matCellDef="let element">{{ element.data_type || 'Unknown' }}</td>
              </ng-container>

              <!-- Actions Column -->
              <ng-container matColumnDef="actions">
                <th mat-header-cell *matHeaderCellDef>Actions</th>
                <td mat-cell *matCellDef="let element">
                  <button 
                    mat-icon-button 
                    color="warn" 
                    (click)="removeColumnFromTable(element)"
                    matTooltip="Remove this column"
                    class="remove-btn">
                    <mat-icon>remove_circle</mat-icon>
                  </button>
                </td>
              </ng-container>

              <tr mat-header-row *matHeaderRowDef="createdColumnsTableColumns"></tr>
              <tr mat-row *matRowDef="let row; columns: createdColumnsTableColumns;"></tr>
            </table>
          </div>
          
          <!-- Table Summary -->
          <div class="table-summary" style="margin-top: 20px; padding: 15px; background: #f5f5f5; border-radius: 4px;">
            <h4>Table Summary:</h4>
            <div class="summary-grid">
              <div class="summary-item">
                <span class="summary-label">Total Columns:</span>
                <span class="summary-value">{{ createdColumnsTableData.length }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Source Tables:</span>
                <span class="summary-value">{{ getUniqueSourceTables().length }}</span>
              </div>
              <div class="summary-item">
                <span class="summary-label">Primary Key Candidates:</span>
                <span class="summary-value">{{ getPrimaryKeyCandidates().length }}</span>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Actual Data Table Display -->
      <mat-card class="actual-data-table-card" *ngIf="showActualDataTable">
        <mat-card-header>
          <mat-card-title>📊 Actual Data from Selected Columns</mat-card-title>
          <mat-card-subtitle>
            Real data values from your selected columns across all tables
          </mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <!-- Loading State -->
          <div class="loading-state" *ngIf="isLoadingData">
            <mat-progress-bar mode="indeterminate"></mat-progress-bar>
            <p style="text-align: center; margin-top: 10px;">Loading actual data from files...</p>
          </div>
          
          <!-- Data Table -->
          <div class="data-table-container" *ngIf="!isLoadingData && actualDataTableData.length > 0">
            <div class="table-info-bar">
              <span><strong>Total Rows:</strong> {{ actualDataTableData.length }}</span>
              <span><strong>Total Columns:</strong> {{ actualDataTableColumns.length }}</span>
              <span><strong>Source Tables:</strong> {{ getUniqueSourceTablesFromData().length }}</span>
            </div>
            
            <div class="table-container">
              <table mat-table [dataSource]="actualDataTableData" class="actual-data-table">
                <!-- Dynamic columns based on selected columns -->
                <ng-container *ngFor="let column of actualDataTableColumns" [matColumnDef]="column">
                  <th mat-header-cell *matHeaderCellDef>{{ column }}</th>
                  <td mat-cell *matCellDef="let element">
                    <span class="data-cell" [class.null-value]="!element[column]">
                      {{ element[column] || 'N/A' }}
                    </span>
                  </td>
                </ng-container>

                <tr mat-header-row *matHeaderRowDef="actualDataTableColumns"></tr>
                <tr mat-row *matRowDef="let row; columns: actualDataTableColumns;"></tr>
              </table>
            </div>
            
            <!-- Data Summary -->
            <div class="data-summary" style="margin-top: 20px; padding: 15px; background: #f0f8ff; border-radius: 4px;">
              <h4>Data Summary:</h4>
              <div class="summary-grid">
                <div class="summary-item">
                  <span class="summary-label">Data Rows:</span>
                  <span class="summary-value">{{ actualDataTableData.length }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">Unique Values:</span>
                  <span class="summary-value">{{ getUniqueValuesCount() }}</span>
                </div>
                <div class="summary-item">
                  <span class="summary-label">Null Values:</span>
                  <span class="summary-value">{{ getNullValuesCount() }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- No Data Message -->
          <div class="no-data-message" *ngIf="!isLoadingData && actualDataTableData.length === 0">
            <mat-icon>📭</mat-icon>
            <h3>No Data Available</h3>
            <p>Select some columns first and then click "Display Actual Data" to see the real data.</p>
          </div>
        </mat-card-content>
      </mat-card>

      <!-- Action Buttons -->
      <mat-card class="actions-card">
        <mat-card-content>
          <button 
            mat-raised-button 
            color="primary" 
            (click)="refreshData()"
            class="action-btn">
            <mat-icon>🔄</mat-icon>
            Refresh Data
          </button>
          
          <button 
            mat-raised-button 
            color="warn" 
            (click)="clearAllSelections()"
            class="action-btn">
            <mat-icon>🗑️</mat-icon>
            Clear All
          </button>
        </mat-card-content>
      </mat-card>

      <!-- No Data Message -->
      <mat-card class="no-data-card" *ngIf="filesMetadata.length === 0">
        <mat-card-content>
          <div class="no-data">
            <mat-icon>📁</mat-icon>
            <h3>No Files Available</h3>
            <p>Upload some Excel/CSV files first to start selecting columns.</p>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .column-selection-container {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }

    .header-card {
      margin-bottom: 20px;
    }

    .summary-stats {
      display: flex;
      gap: 20px;
      margin-top: 20px;
      flex-wrap: wrap;
    }

    .stat-item {
      text-align: center;
      padding: 15px;
      border-radius: 8px;
      background: #f5f5f5;
      min-width: 100px;
    }

    .stat-number {
      display: block;
      font-size: 24px;
      font-weight: bold;
      color: #333;
    }

    .stat-label {
      display: block;
      font-size: 12px;
      color: #666;
      text-transform: uppercase;
      margin-top: 5px;
    }

    .selection-card, .mappings-card, .combined-table-card, .actions-card {
      margin-bottom: 20px;
    }

    .table-selection {
      margin-bottom: 30px;
    }

    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 15px;
    }

    .table-header h3 {
      margin: 0;
      color: #333;
    }

    .table-info {
      background: #e3f2fd;
      padding: 5px 10px;
      border-radius: 15px;
      font-size: 12px;
      color: #1976d2;
    }

    .columns-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
      gap: 10px;
      margin-bottom: 20px;
    }

    .column-item {
      padding: 10px;
      border: 1px solid #e0e0e0;
      border-radius: 6px;
      background: #fafafa;
    }

    .column-name {
      font-weight: bold;
      color: #333;
      margin-right: 10px;
    }

    .column-notation {
      font-size: 11px;
      color: #666;
      font-family: 'Courier New', monospace;
    }

    .mappings-list {
      display: flex;
      flex-direction: column;
      gap: 15px;
    }

    .mapping-item {
      padding: 15px;
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      background: #f8f9fa;
    }

    .mapping-content {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
    }

    .mapping-from, .mapping-to {
      background: #e3f2fd;
      padding: 5px 10px;
      border-radius: 4px;
      font-family: 'Courier New', monospace;
      font-weight: bold;
    }

    .mapping-arrow {
      font-size: 18px;
      color: #666;
      font-weight: bold;
    }

    .mapping-description {
      font-size: 12px;
      color: #666;
      font-style: italic;
      margin-bottom: 10px;
    }

    .mapping-actions {
      text-align: right;
      margin-top: 10px;
    }

    .mapping-actions .delete-btn {
      color: #f44336;
    }

    .table-info p {
      margin: 8px 0;
      color: #333;
    }

    .columns-display h4 {
      margin: 20px 0 10px 0;
      color: #333;
    }

    .columns-grid-display {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .column-chip {
      background: #4caf50 !important;
      color: white !important;
    }

    .actions-card {
      text-align: center;
    }

    .action-btn {
      margin: 0 10px;
    }

    /* Manual Relationship Styles */
    .manual-relationship-card {
      margin-bottom: 20px;
    }

    .manual-relationship-form {
      margin-top: 20px;
    }

    .form-row {
      display: flex;
      gap: 20px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .form-group {
      flex: 1;
      min-width: 250px;
    }

    .form-group label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      color: #333;
    }

    .table-column-selector {
      display: flex;
      gap: 10px;
    }

    .table-column-selector select {
      flex: 1;
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      background: white;
      font-size: 14px;
    }

    .form-group input {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
    }

    /* Created Columns Table Styles */
    .created-columns-table-card {
      margin-bottom: 20px;
    }

    .display-actions {
      margin-top: 20px;
      text-align: center;
    }

    .display-btn {
      background: #ff9800 !important;
      color: white !important;
    }

    .table-container {
      overflow-x: auto;
      margin-top: 20px;
    }

    .created-columns-table {
      width: 100%;
      border-collapse: collapse;
    }

    .created-columns-table th,
    .created-columns-table td {
      padding: 12px 8px;
      text-align: left;
      border-bottom: 1px solid #ddd;
    }

    .created-columns-table th {
      background: #f5f5f5;
      font-weight: 600;
      color: #333;
    }

    .created-columns-table tr:hover {
      background: #f9f9f9;
    }

    .remove-btn {
      color: #f44336;
    }

    .table-summary {
      margin-top: 20px;
      padding: 15px;
      background: #f5f5f5;
      border-radius: 4px;
    }

    .table-summary h4 {
      margin: 0 0 15px 0;
      color: #333;
    }

    .summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
    }

    .summary-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px;
      background: white;
      border-radius: 4px;
      border: 1px solid #ddd;
    }

    .summary-label {
      font-weight: 500;
      color: #666;
    }

    .summary-value {
      font-weight: 600;
      color: #333;
      background: #e3f2fd;
      padding: 4px 8px;
      border-radius: 4px;
    }

    /* Actual Data Table Styles */
    .actual-data-table-card {
      margin-bottom: 20px;
    }

    .data-btn {
      background: #2196f3 !important;
      color: white !important;
      margin-left: 10px;
    }

    .test-btn {
      background: #ff5722 !important;
      color: white !important;
      margin-left: 10px;
    }

    .loading-state {
      padding: 20px;
      text-align: center;
    }

    .table-info-bar {
      display: flex;
      justify-content: space-around;
      padding: 15px;
      background: #e8f5e8;
      border-radius: 4px;
      margin-bottom: 20px;
      flex-wrap: wrap;
      gap: 15px;
    }

    .table-info-bar span {
      font-weight: 500;
      color: #2e7d32;
    }

    .actual-data-table {
      width: 100%;
      border-collapse: collapse;
    }

    .actual-data-table th,
    .actual-data-table td {
      padding: 10px 8px;
      text-align: left;
      border-bottom: 1px solid #ddd;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .actual-data-table th {
      background: #f0f8ff;
      font-weight: 600;
      color: #1976d2;
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .actual-data-table tr:hover {
      background: #f5f5f5;
    }

    .data-cell {
      display: block;
      max-width: 180px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .data-cell.null-value {
      color: #999;
      font-style: italic;
    }

    .data-summary {
      margin-top: 20px;
      padding: 15px;
      background: #f0f8ff;
      border-radius: 4px;
    }

    .no-data-message {
      text-align: center;
      padding: 40px 20px;
      color: #666;
    }

    .no-data-message mat-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: #ccc;
      margin-bottom: 20px;
    }

    .no-data-message h3 {
      margin: 0 0 10px 0;
      color: #333;
    }

    .form-actions {
      text-align: center;
      margin-top: 20px;
    }

    .create-btn {
      padding: 10px 24px;
      font-size: 16px;
    }

    .manual-relationships-list {
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }

    .manual-relationships-list h4 {
      margin-bottom: 15px;
      color: #333;
    }

    .relationship-item {
      background: #f8f9fa;
      padding: 15px;
      border-radius: 8px;
      margin-bottom: 10px;
      border-left: 4px solid #2196f3;
    }

    .relationship-content {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;
      font-weight: 500;
    }

    .relationship-from, .relationship-to {
      background: #e3f2fd;
      padding: 4px 8px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 14px;
    }

    .relationship-arrow {
      color: #666;
      font-size: 18px;
    }

    .relationship-type {
      background: #f0f0f0;
      padding: 2px 6px;
      border-radius: 4px;
      font-size: 12px;
      color: #666;
    }

    .relationship-description {
      color: #666;
      font-size: 14px;
      margin-bottom: 10px;
    }

    .relationship-actions {
      text-align: right;
    }

    .delete-btn {
      color: #f44336;
    }

    .no-data-card {
      text-align: center;
      padding: 40px;
    }

    .no-data mat-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      color: #ccc;
      margin-bottom: 20px;
    }

    .no-data h3 {
      color: #666;
      margin-bottom: 10px;
    }

    .no-data p {
      color: #888;
      margin-bottom: 10px;
    }
  `]
})
export class ColumnSelectionComponent implements OnInit {
  filesMetadata: any[] = [];
  selectedColumnsSummary: SelectedColumnsSummary | null = null;
  columnMappingsSummary: ColumnMappingSummary | null = null;
  combinedTableStructure: CombinedTableStructure | null = null;
  
  // Manual relationship properties
  manualRelationship = {
    sourceTable: '',
    sourceColumn: '',
    targetTable: '',
    targetColumn: '',
    relationshipType: 'one_to_one',
    description: ''
  };
  
  manualRelationships: any[] = [];
  
  // Track deleted detected relationships
  deletedDetectedRelationships: Set<string> = new Set();
  
  // Created columns table display properties
  showCreatedColumnsTable = false;
  createdColumnsTableData: any[] = [];
  createdColumnsTableColumns = ['table_name', 'column_name', 'full_path', 'data_type', 'actions'];
  
  // Actual data display properties
  showActualDataTable = false;
  actualDataTableData: any[] = [];
  actualDataTableColumns: string[] = [];
  isLoadingData = false;

  constructor(
    private columnMappingService: ColumnMappingService,
    private fileService: FileService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadFilesMetadata();
    this.refreshData();
  }

  loadFilesMetadata(): void {
    this.fileService.getFilesMetadata().subscribe({
      next: (response) => {
        this.filesMetadata = response.files;
      },
      error: (error) => {
        console.error('Error loading files metadata:', error);
        this.snackBar.open('Error loading files metadata', 'Close', { duration: 3000 });
      }
    });
  }

  refreshData(): void {
    // Get selected columns
    this.columnMappingService.getSelectedColumns().subscribe({
      next: (summary) => {
        this.selectedColumnsSummary = summary;
      },
      error: (error) => {
        console.error('Error getting selected columns:', error);
      }
    });

    // Get column mappings
    this.columnMappingService.getColumnMappings().subscribe({
      next: (mappings) => {
        // Filter out deleted relationships
        if (mappings.mappings) {
          mappings.mappings = mappings.mappings.filter(mapping => {
            const relationshipKey = `${mapping.from_table}.${mapping.from_column}=${mapping.to_table}.${mapping.to_column}`;
            return !this.deletedDetectedRelationships.has(relationshipKey);
          });
          
          // Update total count
          mappings.total_mappings = mappings.mappings.length;
        }
        
        this.columnMappingsSummary = mappings;
      },
      error: (error) => {
        console.error('Error getting column mappings:', error);
      }
    });

    // Get combined table structure
    this.columnMappingService.getCombinedTableStructure().subscribe({
      next: (structure) => {
        this.combinedTableStructure = structure;
      },
      error: (error) => {
        console.error('Error getting combined table structure:', error);
      }
    });
  }

  onColumnSelectionChange(tableName: string, columnName: string, isSelected: boolean): void {
    if (isSelected) {
      this.columnMappingService.selectColumns(tableName, [columnName]).subscribe({
        next: (response) => {
          this.snackBar.open(response.message, 'Close', { duration: 2000 });
          this.refreshData();
        },
        error: (error) => {
          console.error('Error selecting column:', error);
          this.snackBar.open('Error selecting column', 'Close', { duration: 3000 });
        }
      });
    } else {
      this.columnMappingService.deselectColumns(tableName, [columnName]).subscribe({
        next: (response) => {
          this.snackBar.open(response.message, 'Close', { duration: 2000 });
          this.refreshData();
        },
        error: (error) => {
          console.error('Error deselecting column:', error);
          this.snackBar.open('Error deselecting column', 'Close', { duration: 3000 });
        }
      });
    }
  }

  isColumnSelected(tableName: string, columnName: string): boolean {
    if (!this.selectedColumnsSummary) return false;
    
    const table = this.selectedColumnsSummary.tables.find(t => t.table_name === tableName);
    return table ? table.selected_columns.includes(columnName) : false;
  }

  clearAllSelections(): void {
    this.columnMappingService.clearAllSelections().subscribe({
      next: (response) => {
        this.snackBar.open(response.message, 'Close', { duration: 2000 });
        this.refreshData();
      },
      error: (error) => {
        console.error('Error clearing selections:', error);
        this.snackBar.open('Error clearing selections', 'Close', { duration: 3000 });
      }
    });
  }

  // Manual relationship methods
  onSourceTableChange(): void {
    this.manualRelationship.sourceColumn = '';
  }

  onTargetTableChange(): void {
    this.manualRelationship.targetColumn = '';
  }

  getSourceColumns(): string[] {
    if (!this.manualRelationship.sourceTable) return [];
    const file = this.filesMetadata.find(f => f.filename === this.manualRelationship.sourceTable);
    return file ? file.columns || [] : [];
  }

  getTargetColumns(): string[] {
    if (!this.manualRelationship.targetTable) return [];
    const file = this.filesMetadata.find(f => f.filename === this.manualRelationship.targetTable);
    return file ? file.columns || [] : [];
  }

  isManualRelationshipValid(): boolean {
    return !!(
      this.manualRelationship.sourceTable &&
      this.manualRelationship.sourceColumn &&
      this.manualRelationship.targetTable &&
      this.manualRelationship.targetColumn &&
      this.manualRelationship.description &&
      this.manualRelationship.sourceTable !== this.manualRelationship.targetTable
    );
  }

  createManualRelationship(): void {
    if (!this.isManualRelationshipValid()) return;

    const relationshipData = {
      source_table: this.manualRelationship.sourceTable,
      source_column: this.manualRelationship.sourceColumn,
      target_table: this.manualRelationship.targetTable,
      target_column: this.manualRelationship.targetColumn,
      relationship_type: this.manualRelationship.relationshipType,
      description: this.manualRelationship.description
    };

    // For now, we'll add it to the local array
    // In a real implementation, you'd call the relationship service
    const newRelationship = {
      id: `manual_${Date.now()}`,
      ...relationshipData,
      source: 'manual',
      created_at: new Date().toISOString()
    };

    this.manualRelationships.push(newRelationship);
    
    // Reset form
    this.manualRelationship = {
      sourceTable: '',
      sourceColumn: '',
      targetTable: '',
      targetColumn: '',
      relationshipType: 'one_to_one',
      description: ''
    };

    this.snackBar.open('Manual relationship created successfully!', 'Close', { duration: 3000 });
  }

  deleteManualRelationship(relationshipId: string): void {
    this.manualRelationships = this.manualRelationships.filter(r => r.id !== relationshipId);
    this.snackBar.open('Manual relationship deleted!', 'Close', { duration: 2000 });
  }

  deleteDetectedRelationship(index: number): void {
    if (this.columnMappingsSummary && this.columnMappingsSummary.mappings) {
      const relationship = this.columnMappingsSummary.mappings[index];
      
      // Create a unique key for this relationship
      const relationshipKey = `${relationship.from_table}.${relationship.from_column}=${relationship.to_table}.${relationship.to_column}`;
      
      // Add to deleted set
      this.deletedDetectedRelationships.add(relationshipKey);
      
      // Remove the relationship from the mappings array
      this.columnMappingsSummary.mappings.splice(index, 1);
      
      // Update the total count
      this.columnMappingsSummary.total_mappings = this.columnMappingsSummary.mappings.length;
      
      // Show success message
      this.snackBar.open('Detected relationship deleted!', 'Close', { duration: 2000 });
      
      // Update the combined table structure without refreshing from backend
      this.updateCombinedTableStructure();
    }
  }

  updateCombinedTableStructure(): void {
    if (this.combinedTableStructure && this.columnMappingsSummary) {
      // Update the column count based on remaining relationships
      this.combinedTableStructure.column_count = this.columnMappingsSummary.total_mappings;
      
      // You can add more logic here to update the combined structure
      // based on the remaining relationships
    }
    
    // Update the created columns table if it's currently displayed
    if (this.showCreatedColumnsTable) {
      this.buildCreatedColumnsTableData();
    }
  }

  // Created columns table methods
  displayCreatedColumnsTable(): void {
    this.showCreatedColumnsTable = true;
    this.buildCreatedColumnsTableData();
    this.snackBar.open('Created columns table displayed!', 'Close', { duration: 2000 });
  }

  buildCreatedColumnsTableData(): void {
    this.createdColumnsTableData = [];

    if (!this.selectedColumnsSummary || !this.selectedColumnsSummary.tables) return;

    this.selectedColumnsSummary.tables.forEach(table => {
      table.selected_columns.forEach(column => {
        this.createdColumnsTableData.push({
          table_name: table.table_name,
          column_name: column, // Just the column name
          full_path: `${table.table_name}.${column}`,
          data_type: this.getColumnDataType(table.table_name, column)
        });
      });
    });
  }

  getColumnDataType(tableName: string, columnName: string): string {
    // Try to get data type from the file metadata
    const file = this.filesMetadata.find(f => f.filename === tableName);
    if (file && file.column_types && file.column_types[columnName]) {
      return file.column_types[columnName];
    }
    
    // Fallback: try to infer from sample data
    return this.inferDataTypeFromSample(tableName, columnName);
  }

  inferDataTypeFromSample(tableName: string, columnName: string): string {
    // This is a placeholder - in a real implementation, you'd analyze sample data
    // For now, return common types based on column name patterns
    const columnLower = columnName.toLowerCase();
    
    if (columnLower.includes('id') || columnLower.includes('_id')) return 'INTEGER';
    if (columnLower.includes('date') || columnLower.includes('time')) return 'DATE';
    if (columnLower.includes('amount') || columnLower.includes('price') || columnLower.includes('cost')) return 'DECIMAL';
    if (columnLower.includes('name') || columnLower.includes('title') || columnLower.includes('description')) return 'VARCHAR';
    
    return 'VARCHAR'; // Default fallback
  }

  removeColumnFromTable(columnData: any): void {
    // Remove the column from the created table
    this.createdColumnsTableData = this.createdColumnsTableData.filter(
      col => !(col.table_name === columnData.table_name && col.column_name === columnData.column_name)
    );
    
    // Also deselect it from the backend
    this.columnMappingService.deselectColumns(columnData.table_name, [columnData.column_name]).subscribe({
      next: (response) => {
        this.snackBar.open(`Column ${columnData.column_name} removed from table`, 'Close', { duration: 2000 });
        this.refreshData();
      },
      error: (error) => {
        console.error('Error removing column:', error);
        this.snackBar.open('Error removing column', 'Close', { duration: 3000 });
      }
    });
  }

  getUniqueSourceTables(): string[] {
    const tables = new Set(this.createdColumnsTableData.map(col => col.table_name));
    return Array.from(tables);
  }

  getPrimaryKeyCandidates(): string[] {
    // Identify potential primary key columns
    return this.createdColumnsTableData
      .filter(col => {
        const columnLower = col.column_name.toLowerCase();
        return columnLower.includes('id') && 
               (columnLower.includes('primary') || columnLower.includes('key') || 
                col.table_name.toLowerCase().includes(col.column_name.toLowerCase().replace('_id', '')));
      })
      .map(col => col.full_path);
  }

  // Actual data display methods
  displayActualData(): void {
    this.showActualDataTable = true;
    this.isLoadingData = true;
    this.fetchActualDataFromFiles();
  }

  fetchActualDataFromFiles(): void {
    if (!this.selectedColumnsSummary || !this.selectedColumnsSummary.tables) {
      this.isLoadingData = false;
      return;
    }

    // Get the list of files that have selected columns
    const filesWithColumns = this.selectedColumnsSummary.tables
      .filter(table => table.selected_columns.length > 0)
      .map(table => table.table_name);

    if (filesWithColumns.length === 0) {
      this.isLoadingData = false;
      return;
    }

    // Call the backend API to get real data
    const request = {
      filenames: filesWithColumns,
      sample_size: 10 // Get 10 rows from each file
    };

    this.fileService.getMultipleFilesData(request).subscribe({
      next: (response) => {
        this.processRealDataFromBackend(response);
        this.isLoadingData = false;
      },
      error: (error) => {
        console.error('Error fetching real data:', error);
        this.snackBar.open('Error fetching real data from files', 'Close', { duration: 3000 });
        this.isLoadingData = false;
      }
    });
  }

  createSampleDataFromSelectedColumns(): void {
    this.actualDataTableData = [];
    this.actualDataTableColumns = [];

    if (!this.selectedColumnsSummary || !this.selectedColumnsSummary.tables) return;

    // Build column headers
    this.selectedColumnsSummary.tables.forEach(table => {
      table.selected_columns.forEach(column => {
        const columnKey = `${table.table_name}.${column}`;
        this.actualDataTableColumns.push(columnKey);
      });
    });

    // Create sample data rows (in a real app, this would come from backend)
    this.createSampleDataRows();
  }

  createSampleDataRows(): void {
    // Create 10 sample rows with realistic data
    for (let i = 1; i <= 10; i++) {
      const row: any = {};
      
      this.actualDataTableColumns.forEach(columnKey => {
        const [tableName, columnName] = columnKey.split('.');
        row[columnKey] = this.generateSampleValue(tableName, columnName, i);
      });
      
      this.actualDataTableData.push(row);
    }
  }

  generateSampleValue(tableName: string, columnName: string, rowIndex: number): any {
    const columnLower = columnName.toLowerCase();
    
    // Generate realistic sample data based on column name patterns
    if (columnLower.includes('id')) {
      return rowIndex;
    } else if (columnLower.includes('name')) {
      const names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Lisa', 'Tom', 'Emma', 'Alex', 'Maria'];
      return names[(rowIndex - 1) % names.length];
    } else if (columnLower.includes('email')) {
      const names = ['john', 'jane', 'mike', 'sarah', 'david', 'lisa', 'tom', 'emma', 'alex', 'maria'];
      return `${names[(rowIndex - 1) % names.length]}@example.com`;
    } else if (columnLower.includes('date')) {
      const dates = ['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2024-05-12'];
      return dates[(rowIndex - 1) % dates.length];
    } else if (columnLower.includes('amount') || columnLower.includes('price') || columnLower.includes('cost')) {
      return Math.floor(Math.random() * 1000) + 10;
    } else if (columnLower.includes('status')) {
      const statuses = ['Active', 'Inactive', 'Pending', 'Completed', 'Cancelled'];
      return statuses[(rowIndex - 1) % statuses.length];
    } else {
      return `Sample ${columnName} ${rowIndex}`;
    }
  }

  getUniqueSourceTablesFromData(): string[] {
    const tables = new Set<string>();
    this.actualDataTableColumns.forEach(columnKey => {
      const tableName = columnKey.split('.')[0];
      tables.add(tableName);
    });
    return Array.from(tables);
  }

  getUniqueValuesCount(): number {
    const allValues = new Set();
    this.actualDataTableData.forEach(row => {
      Object.values(row).forEach(value => {
        if (value !== null && value !== undefined && value !== 'N/A') {
          allValues.add(value);
        }
      });
    });
    return allValues.size;
  }

  /**
   * Process real data received from the backend API
   */
  processRealDataFromBackend(response: any): void {
    this.actualDataTableData = [];
    this.actualDataTableColumns = [];

    // Build column headers from selected columns (only column names, no file names)
    if (this.selectedColumnsSummary && this.selectedColumnsSummary.tables) {
      this.selectedColumnsSummary.tables.forEach(table => {
        table.selected_columns.forEach(column => {
          // Just use the column name, not the full path
          this.actualDataTableColumns.push(column);
        });
      });
    }

    // Process data from each file
    if (response.files_data) {
      Object.keys(response.files_data).forEach(filename => {
        const fileData = response.files_data[filename];
        
        // Process each row from the file
        fileData.forEach((row: any, rowIndex: number) => {
          const processedRow: any = {};
          
          // Map the selected columns to the actual data
          this.actualDataTableColumns.forEach(columnName => {
            // Check if this column exists in the current file's data
            if (row.hasOwnProperty(columnName)) {
              processedRow[columnName] = row[columnName];
            } else {
              // If column doesn't exist in this file, set to null
              processedRow[columnName] = null;
            }
          });
          
          this.actualDataTableData.push(processedRow);
        });
      });
    }

    console.log('Processed real data:', this.actualDataTableData);
    console.log('Columns:', this.actualDataTableColumns);
  }

  /**
   * Alternative method: Get data from a single file for testing
   */
  fetchSingleFileData(filename: string, sampleSize: number = 10): void {
    this.isLoadingData = true;
    
    this.fileService.getFileData(filename, sampleSize).subscribe({
      next: (response) => {
        this.processSingleFileData(response);
        this.isLoadingData = false;
      },
      error: (error) => {
        console.error('Error fetching single file data:', error);
        this.snackBar.open(`Error fetching data from ${filename}`, 'Close', { duration: 3000 });
        this.isLoadingData = false;
      }
    });
  }

  /**
   * Process data from a single file
   */
  processSingleFileData(response: any): void {
    this.actualDataTableData = [];
    this.actualDataTableColumns = [];

    // Build column headers from the file data (only column names, no file names)
    if (response.data && response.data.length > 0) {
      const firstRow = response.data[0];
      Object.keys(firstRow).forEach(columnName => {
        // Just use the column name, not the full path
        this.actualDataTableColumns.push(columnName);
      });
    }

    // Process each row
    if (response.data) {
      response.data.forEach((row: any) => {
        const processedRow: any = {};
        
        this.actualDataTableColumns.forEach(columnName => {
          processedRow[columnName] = row[columnName] || null;
        });
        
        this.actualDataTableData.push(processedRow);
      });
    }

    console.log('Processed single file data:', this.actualDataTableData);
    console.log('Columns:', this.actualDataTableColumns);
  }

  /**
   * Test method to fetch data from a single file
   */
  testSingleFileData(): void {
    // Test with your bankBookReport file
    this.fetchSingleFileData('bankBookReport(1).xls', 5);
  }

  getNullValuesCount(): number {
    let nullCount = 0;
    this.actualDataTableData.forEach(row => {
      Object.values(row).forEach(value => {
        if (value === null || value === undefined || value === 'N/A') {
          nullCount++;
        }
      });
    });
    return nullCount;
  }
} 