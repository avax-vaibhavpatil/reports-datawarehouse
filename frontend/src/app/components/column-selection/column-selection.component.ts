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

      <!-- Composite Key Relationships Section -->
      <mat-card class="composite-relationships-card">
        <mat-card-header>
          <mat-card-title>🔗 Create Composite Key Relationships</mat-card-title>
          <mat-card-subtitle>
            Create relationships using multiple columns (like your SQL example with 3 columns)
          </mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <div class="composite-form">
            <div class="form-row">
              <div class="form-group">
                <label>Table 1:</label>
                <select [(ngModel)]="compositeRelationship.table1" (change)="onCompositeTable1Change()">
                  <option value="">Select First Table</option>
                  <option *ngFor="let file of filesMetadata" [value]="file.filename">
                    {{ file.filename }}
                  </option>
                </select>
              </div>
              
              <div class="form-group">
                <label>Table 2:</label>
                <select [(ngModel)]="compositeRelationship.table2" (change)="onCompositeTable2Change()">
                  <option value="">Select Second Table</option>
                  <option *ngFor="let file of filesMetadata" [value]="file.filename">
                    {{ file.filename }}
                  </option>
                </select>
              </div>
            </div>
            
            <!-- Column Pairs -->
            <div class="column-pairs-section" *ngIf="compositeRelationship.table1 && compositeRelationship.table2">
              <h4>Column Pairs (Add at least 2 pairs):</h4>
              <div class="column-pair" *ngFor="let pair of compositeRelationship.columnPairs; let i = index">
                <div class="pair-row">
                  <div class="column-selector">
                    <label>{{ compositeRelationship.table1 }} Column:</label>
                    <select [(ngModel)]="pair.table1_col" (change)="updateCompositeDescription()">
                      <option value="">Select Column</option>
                      <option *ngFor="let column of getCompositeTable1Columns()" [value]="column">
                        {{ column }}
                      </option>
                    </select>
                  </div>
                  
                  <span class="equals-sign">=</span>
                  
                  <div class="column-selector">
                    <label>{{ compositeRelationship.table2 }} Column:</label>
                    <select [(ngModel)]="pair.table2_col" (change)="updateCompositeDescription()">
                      <option value="">Select Column</option>
                      <option *ngFor="let column of getCompositeTable2Columns()" [value]="column">
                        {{ column }}
                      </option>
                    </select>
                  </div>
                  
                  <button mat-icon-button color="warn" (click)="removeColumnPair(i)" class="remove-pair-btn">
                    <mat-icon>remove_circle</mat-icon>
                  </button>
                </div>
              </div>
              
              <button mat-stroked-button (click)="addColumnPair()" class="add-pair-btn">
                <mat-icon>add</mat-icon>
                Add Column Pair
              </button>
            </div>
            
            <!-- Description -->
            <div class="form-group" *ngIf="compositeRelationship.columnPairs.length > 0">
              <label>Description:</label>
              <input type="text" [(ngModel)]="compositeRelationship.description" 
                     placeholder="e.g., Composite join on voucher_no, siscon_code, and branch_code"
                     readonly>
            </div>
            
            <div class="form-actions">
              <button 
                mat-raised-button 
                color="accent" 
                (click)="createCompositeRelationship()"
                [disabled]="!isCompositeRelationshipValid()"
                class="create-composite-btn">
                <mat-icon>🔗</mat-icon>
                Create Composite Relationship
              </button>
            </div>
          </div>
          
          <!-- Composite Relationships List -->
          <div class="composite-relationships-list" *ngIf="compositeRelationships.length > 0">
            <h4>Composite Relationships Created:</h4>
            <div class="composite-relationship-item" *ngFor="let rel of compositeRelationships; let i = index">
              <div class="composite-relationship-content">
                <span class="relationship-tables">{{ rel.table1 }} ↔ {{ rel.table2 }}</span>
                <span class="relationship-count">({{ rel.mapping_count }} columns)</span>
              </div>
              <div class="relationship-description">{{ rel.description }}</div>
              <div class="column-pairs-display">
                <div class="pair-display" *ngFor="let pair of rel.column_pairs">
                  <span class="pair-text">{{ rel.table1 }}.{{ pair.table1_col }} = {{ rel.table2 }}.{{ pair.table2_col }}</span>
                </div>
              </div>
              <div class="relationship-actions">
                <button mat-icon-button color="warn" (click)="deleteCompositeRelationship(rel.id)" class="delete-btn">
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
          <!-- Custom Table Name Input -->
          <div class="custom-table-name-section" style="margin-bottom: 20px;">
            <mat-form-field appearance="outline" class="table-name-field">
              <mat-label>Custom Table Name</mat-label>
              <input 
                matInput 
                [(ngModel)]="customTableName" 
                (ngModelChange)="onTableNameChange()"
                placeholder="Enter table name"
                maxlength="50">
              <mat-hint>Give your combined table a custom name</mat-hint>
            </mat-form-field>
          </div>
          
          <div class="table-info">
            <p><strong>Table Name:</strong> {{ customTableName || combinedTableStructure.table_name }}</p>
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
          <mat-card-title>📊 Data from "{{ customTableName || 'Combined Table' }}"</mat-card-title>
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
              <span class="scroll-hint">📜 Scroll to see more data</span>
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
              <h4>Data Summary for "{{ customTableName || 'Combined Table' }}":</h4>
              <div class="summary-grid">
                <div class="summary-item">
                  <span class="summary-label">Table Name:</span>
                  <span class="summary-value">{{ customTableName || 'combined_table' }}</span>
                </div>
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
      overflow: auto;
      margin-top: 20px;
      max-height: 500px;
      border: 1px solid #ddd;
      border-radius: 4px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .table-container::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }

    .table-container::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 4px;
    }

    .table-container::-webkit-scrollbar-thumb {
      background: #888;
      border-radius: 4px;
    }

    .table-container::-webkit-scrollbar-thumb:hover {
      background: #555;
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

    .actual-data-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 600px;
    }

    .actual-data-table th,
    .actual-data-table td {
      padding: 8px 12px;
      text-align: left;
      border-bottom: 1px solid #ddd;
      white-space: nowrap;
    }

    .actual-data-table th {
      background: #f5f5f5;
      font-weight: 600;
      color: #333;
      position: sticky;
      top: 0;
      z-index: 10;
    }

    .actual-data-table tr:hover {
      background: #f9f9f9;
    }

    .data-cell {
      display: inline-block;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .data-cell.null-value {
      color: #999;
      font-style: italic;
    }

    .table-info-bar {
      display: flex;
      flex-wrap: wrap;
      gap: 15px;
      padding: 10px 15px;
      background: #f8f9fa;
      border: 1px solid #e9ecef;
      border-radius: 4px;
      margin-bottom: 10px;
    }

    .table-info-bar span {
      font-size: 14px;
    }

    .scroll-hint {
      color: #666;
      font-style: italic;
      margin-left: auto;
    }

    .custom-table-name-section {
      background: #f8f9fa;
      padding: 15px;
      border-radius: 8px;
      border: 1px solid #e9ecef;
    }

    .table-name-field {
      width: 100%;
      max-width: 400px;
    }

    .table-name-field .mat-form-field-wrapper {
      padding-bottom: 0;
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

    /* Composite Relationship Styles */
    .composite-relationships-card {
      margin-top: 20px;
    }

    .composite-form {
      padding: 20px 0;
    }

    .column-pairs-section {
      margin-top: 20px;
      padding: 20px;
      background: #f8f9fa;
      border-radius: 8px;
      border: 1px solid #e9ecef;
    }

    .column-pairs-section h4 {
      margin-bottom: 15px;
      color: #333;
    }

    .column-pair {
      margin-bottom: 15px;
      padding: 15px;
      background: white;
      border-radius: 6px;
      border: 1px solid #dee2e6;
    }

    .pair-row {
      display: flex;
      align-items: center;
      gap: 15px;
      flex-wrap: wrap;
    }

    .column-selector {
      flex: 1;
      min-width: 200px;
    }

    .column-selector label {
      display: block;
      margin-bottom: 5px;
      font-weight: 500;
      color: #555;
      font-size: 14px;
    }

    .column-selector select {
      width: 100%;
      padding: 8px 12px;
      border: 1px solid #ddd;
      border-radius: 4px;
      font-size: 14px;
    }

    .equals-sign {
      font-size: 18px;
      font-weight: bold;
      color: #666;
      margin: 0 10px;
    }

    .remove-pair-btn {
      color: #dc3545;
      margin-left: 10px;
    }

    .add-pair-btn {
      margin-top: 15px;
      border: 2px dashed #007bff;
      color: #007bff;
      background: transparent;
    }

    .add-pair-btn:hover {
      background: #e3f2fd;
    }

    .create-composite-btn {
      margin-top: 20px;
      padding: 12px 24px;
      font-size: 16px;
    }

    .composite-relationships-list {
      margin-top: 30px;
      padding-top: 20px;
      border-top: 1px solid #eee;
    }

    .composite-relationships-list h4 {
      margin-bottom: 15px;
      color: #333;
    }

    .composite-relationship-item {
      background: #f0f8ff;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 15px;
      border-left: 4px solid #007bff;
    }

    .composite-relationship-content {
      display: flex;
      align-items: center;
      gap: 15px;
      margin-bottom: 10px;
      font-weight: 600;
    }

    .relationship-tables {
      background: #e3f2fd;
      padding: 6px 12px;
      border-radius: 4px;
      font-family: monospace;
      font-size: 14px;
    }

    .relationship-count {
      background: #f0f0f0;
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 12px;
      color: #666;
    }

    .column-pairs-display {
      margin: 10px 0;
    }

    .pair-display {
      margin: 5px 0;
      padding: 8px 12px;
      background: white;
      border-radius: 4px;
      border: 1px solid #e9ecef;
    }

    .pair-text {
      font-family: monospace;
      font-size: 13px;
      color: #495057;
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
  
  // Composite relationship properties
  compositeRelationship = {
    table1: '',
    table2: '',
    columnPairs: [] as any[],
    description: ''
  };
  
  compositeRelationships: any[] = [];
  
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
  
  // Custom table name
  customTableName = 'combined_table';

  constructor(
    private columnMappingService: ColumnMappingService,
    private fileService: FileService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    // Ensure compositeRelationships is initialized
    if (!this.compositeRelationships) {
      this.compositeRelationships = [];
    }
    
    this.loadFilesMetadata();
    this.refreshData();
  }

  onTableNameChange(): void {
    // Update the combined table structure with the new name
    if (this.combinedTableStructure) {
      this.combinedTableStructure.table_name = this.customTableName;
    }
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

  // Composite relationship methods
  onCompositeTable1Change(): void {
    this.compositeRelationship.columnPairs = [];
    this.compositeRelationship.description = '';
  }

  onCompositeTable2Change(): void {
    this.compositeRelationship.columnPairs = [];
    this.compositeRelationship.description = '';
  }

  getCompositeTable1Columns(): string[] {
    if (!this.compositeRelationship.table1) return [];
    const file = this.filesMetadata.find(f => f.filename === this.compositeRelationship.table1);
    return file ? file.columns || [] : [];
  }

  getCompositeTable2Columns(): string[] {
    if (!this.compositeRelationship.table2) return [];
    const file = this.filesMetadata.find(f => f.filename === this.compositeRelationship.table2);
    return file ? file.columns || [] : [];
  }

  addColumnPair(): void {
    this.compositeRelationship.columnPairs.push({
      table1_col: '',
      table2_col: ''
    });
  }

  removeColumnPair(index: number): void {
    this.compositeRelationship.columnPairs.splice(index, 1);
    this.updateCompositeDescription();
  }

  updateCompositeDescription(): void {
    const validPairs = this.compositeRelationship.columnPairs.filter(pair => 
      pair.table1_col && pair.table2_col
    );
    
    if (validPairs.length > 0) {
      const pairDescriptions = validPairs.map(pair => 
        `${this.compositeRelationship.table1}.${pair.table1_col} = ${this.compositeRelationship.table2}.${pair.table2_col}`
      );
      this.compositeRelationship.description = `Composite join: ${pairDescriptions.join(' AND ')}`;
    } else {
      this.compositeRelationship.description = '';
    }
  }

  isCompositeRelationshipValid(): boolean {
    return !!(
      this.compositeRelationship.table1 &&
      this.compositeRelationship.table2 &&
      this.compositeRelationship.table1 !== this.compositeRelationship.table2 &&
      this.compositeRelationship.columnPairs.length >= 2 &&
      this.compositeRelationship.columnPairs.every(pair => pair.table1_col && pair.table2_col)
    );
  }

  createCompositeRelationship(): void {
    if (!this.isCompositeRelationshipValid()) return;

    const columnPairs = this.compositeRelationship.columnPairs.map(pair => ({
      table1_col: pair.table1_col,
      table2_col: pair.table2_col
    }));

    this.columnMappingService.createCompositeRelationship(
      this.compositeRelationship.table1,
      this.compositeRelationship.table2,
      columnPairs
    ).subscribe({
      next: (response) => {
        // Add to local array for display
        const newRelationship = {
          id: `composite_${Date.now()}`,
          table1: this.compositeRelationship.table1,
          table2: this.compositeRelationship.table2,
          column_pairs: columnPairs,
          mapping_count: columnPairs.length,
          description: this.compositeRelationship.description,
          type: 'composite_relationship'
        };

        this.compositeRelationships.push(newRelationship);
        
        // Reset form
        this.compositeRelationship = {
          table1: '',
          table2: '',
          columnPairs: [],
          description: ''
        };

        this.snackBar.open('Composite relationship created successfully!', 'Close', { duration: 3000 });
        this.refreshData();
      },
      error: (error) => {
        console.error('Error creating composite relationship:', error);
        this.snackBar.open('Error creating composite relationship', 'Close', { duration: 3000 });
      }
    });
  }

  deleteCompositeRelationship(relationshipId: string): void {
    this.compositeRelationships = this.compositeRelationships.filter(r => r.id !== relationshipId);
    this.snackBar.open('Composite relationship deleted!', 'Close', { duration: 2000 });
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
    
    // Get the list of files that have selected columns
    const filesWithColumns = this.getFilesWithSelectedColumns();
    console.log('Files with selected columns:', filesWithColumns);
    console.log('Composite relationships:', this.compositeRelationships);
    
    this.fetchActualDataFromFiles(filesWithColumns);
  }

  getFilesWithSelectedColumns(): string[] {
    if (!this.selectedColumnsSummary || !this.selectedColumnsSummary.tables) {
      return [];
    }
    
    return this.selectedColumnsSummary.tables
      .filter(table => table.selected_columns.length > 0)
      .map(table => table.table_name);
  }

  getSelectedColumnsList(): string[] {
    if (!this.selectedColumnsSummary || !this.selectedColumnsSummary.tables) {
      return [];
    }
    
    const selectedColumns: string[] = [];
    this.selectedColumnsSummary.tables.forEach(table => {
      table.selected_columns.forEach(col => {
        // col is already a string (column name), not an object
        selectedColumns.push(col);
      });
    });
    
    return selectedColumns;
  }

  fetchActualDataFromFiles(filesWithColumns: string[]): void {
    if (!filesWithColumns || filesWithColumns.length === 0) {
      this.isLoadingData = false;
      return;
    }

    // Check if we have composite relationships that should be used for joining
    if (this.compositeRelationships && 
        Array.isArray(this.compositeRelationships) && 
        this.compositeRelationships.length > 0 && 
        filesWithColumns.length >= 2) {
      // Use joined data if we have composite relationships
      console.log('Using joined data approach');
      this.fetchJoinedData(filesWithColumns);
    } else {
      // Use regular multiple files data
      console.log('Using regular data approach');
      this.fetchRegularData(filesWithColumns);
    }
  }

  fetchJoinedData(filesWithColumns: string[]): void {
    // Check if composite relationships exist
    if (!this.compositeRelationships || this.compositeRelationships.length === 0) {
      console.warn('No composite relationships found, falling back to regular data');
      this.fetchRegularData(filesWithColumns);
      return;
    }

    // Convert composite relationships to join conditions
    console.log('Raw composite relationships:', this.compositeRelationships);
    
    const joinConditions = this.compositeRelationships.map(rel => {
      console.log('Processing relationship:', rel);
      const columnPairs = rel.column_pairs || rel.columnPairs; // Handle both formats
      if (!columnPairs || !Array.isArray(columnPairs)) {
        console.warn('Invalid column pairs in relationship:', rel);
        return [];
      }
      const conditions = columnPairs.map((pair: any) => ({
        table1: rel.table1,
        column1: pair.table1_col,
        table2: rel.table2,
        column2: pair.table2_col
      }));
      
      // Filter out voucher_no join if it exists, as it's too strict
      const filteredConditions = conditions.filter(cond => 
        !cond.column1.includes('voucher_no') && !cond.column2.includes('voucher_no')
      );
      
      console.log('Filtered out voucher_no conditions:', filteredConditions);
      return filteredConditions;
    }).flat();

    console.log('Final join conditions:', joinConditions);

    // Get selected columns for filtering
    const selectedColumns = this.getSelectedColumnsList();
    console.log('Selected columns for filtering:', selectedColumns);
    
    // Limit to 20 rows to prevent loading issues
    this.fileService.getJoinedData(filesWithColumns, joinConditions, selectedColumns, 20).subscribe({
      next: (response) => {
        console.log('Joined data received:', response);
        if (response.total_rows === 0) {
          console.warn('No data from join, falling back to regular data');
          this.fetchRegularData(filesWithColumns);
          return;
        }
        this.processJoinedDataFromBackend(response);
        this.isLoadingData = false;
      },
      error: (error) => {
        console.error('Error fetching joined data:', error);
        console.warn('Join failed, falling back to regular data');
        this.fetchRegularData(filesWithColumns);
      }
    });
  }

  fetchRegularData(filesWithColumns: string[]): void {
    // Call the backend API to get real data
    const request = {
      filenames: filesWithColumns,
      sample_size: 20 // Get 20 rows from each file
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

  processJoinedDataFromBackend(response: any): void {
    this.actualDataTableData = [];
    this.actualDataTableColumns = [];

    // Use the joined data directly
    if (response.joined_data && response.joined_data.length > 0) {
      this.actualDataTableData = response.joined_data;
      this.actualDataTableColumns = response.columns || [];
      
      console.log('Processed joined data:', this.actualDataTableData);
      console.log('Joined columns:', this.actualDataTableColumns);
      console.log('Join conditions used:', response.join_conditions);
    } else {
      console.log('No joined data received');
    }
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