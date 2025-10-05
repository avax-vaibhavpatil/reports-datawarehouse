import { Component, Inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';
import { HttpClient } from '@angular/common/http';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

// Interface for dialog input data
export interface SchemaEditorData {
  sql: string;
  totalRows: number;
  columns: string[];
  sampleData: any[];
  isDatabaseMode?: boolean;
  connectionConfig?: any;
}

// Interface for column schema
export interface ColumnSchema {
  original_name: string;
  clean_name: string;
  detected_type: string;
  suggested_pg_type: string;
  sample_values: any[];
  null_count: number;
  is_nullable: boolean;
}

// Interface for API responses
export interface SchemaPreviewResponse {
  success: boolean;
  table_name: string;
  can_create: boolean;
  name_validation: {
    is_valid: boolean;
    errors: string[];
    warnings: string[];
  };
  table_exists: {
    exists: boolean;
    message: string;
  };
  columns: ColumnSchema[];
  create_sql: string;
  total_rows: number;
}

@Component({
  selector: 'app-schema-editor-dialog',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
    MatCardModule,
    MatDividerModule,
    MatChipsModule
  ],
  templateUrl: './schema-editor-dialog.component.html',
  styleUrls: ['./schema-editor-dialog.component.css']
})
export class SchemaEditorDialogComponent implements OnInit {
  schemaForm: FormGroup;
  isLoading = false;
  isValidating = false;
  schemaPreview: SchemaPreviewResponse | null = null;
  isDatabaseMode = false;
  connectionConfig: any = null;
  availableSchemas: any[] = [];
  isLoadingSchemas = false;
  
  // PostgreSQL data type options
  postgresDataTypes = [
    'TEXT', 'VARCHAR(50)', 'VARCHAR(100)', 'VARCHAR(255)', 'VARCHAR(500)', 'VARCHAR(1000)',
    'INTEGER', 'BIGINT', 'SMALLINT', 
    'DECIMAL(10,2)', 'DECIMAL(15,2)', 'DECIMAL(18,4)',
    'DOUBLE PRECISION', 'REAL', 'BOOLEAN', 
    'DATE', 'TIMESTAMP', 'TIME'
  ];

  constructor(
    private fb: FormBuilder,
    private http: HttpClient,
    private snackBar: MatSnackBar,
    public dialogRef: MatDialogRef<SchemaEditorDialogComponent>,
    @Inject(MAT_DIALOG_DATA) public data: SchemaEditorData
  ) {
    // Initialize database mode properties
    this.isDatabaseMode = data.isDatabaseMode || false;
    this.connectionConfig = data.connectionConfig || null;
    
    // Initialize the form
    this.schemaForm = this.fb.group({
      tableName: ['', [Validators.required, Validators.pattern('^[a-zA-Z][a-zA-Z0-9_]*$')]],
      schema: ['processed_data', Validators.required]  // Default to 'processed_data' schema for warehouse
    });
  }

  ngOnInit(): void {
    // Load available schemas if in database mode
    if (this.isDatabaseMode && this.connectionConfig) {
      console.log('🔍 Database mode detected, loading schemas...', this.connectionConfig);
      this.loadAvailableSchemas();
    } else {
      console.log('📁 File mode detected, using default schemas');
    }
    
    // Set up table name validation with debouncing
    this.schemaForm.get('tableName')?.valueChanges.pipe(
      debounceTime(500),
      distinctUntilChanged()
    ).subscribe(tableName => {
      if (tableName && this.schemaForm.get('tableName')?.valid) {
        this.validateTableName(tableName);
      }
    });

    // Generate initial schema preview when component loads
    this.generateSchemaPreview();
  }

  /**
   * Validate table name and check for duplicates
   */
  validateTableName(tableName: string): void {
    if (!tableName || tableName.trim().length === 0) {
      return;
    }

    this.isValidating = true;
    const schema = this.schemaForm.get('schema')?.value || 'processed_data';

    this.http.post<any>('http://localhost:8000/api/schema-editor/validate-table-name', {
      table_name: tableName.trim(),
      db_schema: schema
    }).subscribe({
      next: (response) => {
        this.isValidating = false;
        if (response.success) {
          // Update form validation based on response
          const tableNameControl = this.schemaForm.get('tableName');
          if (!response.can_create) {
            tableNameControl?.setErrors({ 
              'duplicate': response.table_exists.exists,
              'invalid': !response.name_validation.is_valid,
              'message': response.table_exists.message || response.name_validation.errors?.join(', ')
            });
          } else {
            // Clear custom errors if table can be created
            if (tableNameControl?.hasError('duplicate') || tableNameControl?.hasError('invalid')) {
              tableNameControl?.setErrors(null);
            }
          }
          
          // Generate new schema preview with validated name
          this.generateSchemaPreview();
        }
      },
      error: (error) => {
        this.isValidating = false;
        console.error('Table validation error:', error);
        this.snackBar.open('Error validating table name', 'Close', { duration: 3000 });
      }
    });
  }

  /**
   * Generate schema preview from backend
   */
  generateSchemaPreview(): void {
    const tableName = this.schemaForm.get('tableName')?.value?.trim();
    if (!tableName) {
      return;
    }

    this.isLoading = true;
    const schema = this.schemaForm.get('schema')?.value || 'processed_data';

    const requestData = {
      query_sql: this.data.sql,
      db_schema: schema,
      user_table_name: tableName,
      limit: 100,
      is_database_mode: this.isDatabaseMode,
      connection_config: this.connectionConfig
    };

    this.http.post<SchemaPreviewResponse>('http://localhost:8000/api/schema-editor/preview', requestData)
      .subscribe({
        next: (response) => {
          this.isLoading = false;
          this.schemaPreview = response;
          
          // Ensure backend suggested types are properly mapped to frontend options
          if (response.success && response.columns) {
            response.columns.forEach(column => {
              column.suggested_pg_type = this.mapBackendTypeToFrontend(column.suggested_pg_type);
            });
          }
          
          if (!response.success) {
            this.snackBar.open('Error generating schema preview', 'Close', { duration: 3000 });
          }
        },
        error: (error) => {
          this.isLoading = false;
          console.error('Schema preview error:', error);
          this.snackBar.open('Error connecting to backend', 'Close', { duration: 3000 });
        }
      });
  }

  /**
   * Load available schemas from the connected database
   */
  loadAvailableSchemas(): void {
    if (!this.connectionConfig) {
      console.warn('No connection config available for schema detection');
      return;
    }

    console.log('🔄 Starting schema detection with config:', this.connectionConfig);
    this.isLoadingSchemas = true;
    
    const requestData = {
      connection_config: this.connectionConfig
    };

    this.http.post<any>('http://localhost:8000/api/schema-editor/detect-schemas', requestData)
      .subscribe({
        next: (response) => {
          console.log('📡 Schema detection response:', response);
          this.isLoadingSchemas = false;
          
          if (response.success && response.schemas) {
            this.availableSchemas = response.schemas;
            console.log(`✅ Successfully loaded ${this.availableSchemas.length} schemas:`, this.availableSchemas);
            
            // For warehouse, always use processed_data schema regardless of detected schemas
            // The detected schemas are from source database, but warehouse uses processed_data
            this.schemaForm.patchValue({ schema: 'processed_data' });
            console.log(`🎯 Using processed_data schema for warehouse (detected ${this.availableSchemas.length} schemas from source database)`);
          } else {
            console.error('❌ Failed to load schemas:', response.error);
            this.snackBar.open('Failed to load database schemas', 'Close', { duration: 3000 });
          }
        },
        error: (error) => {
          this.isLoadingSchemas = false;
          console.error('❌ Error loading schemas:', error);
          this.snackBar.open('Error connecting to database for schema detection', 'Close', { duration: 3000 });
        }
      });
  }

  /**
   * Map backend suggested types to frontend dropdown options
   */
  private mapBackendTypeToFrontend(backendType: string): string {
    // If the backend type is already in our dropdown, use it
    if (this.postgresDataTypes.includes(backendType)) {
      return backendType;
    }
    
    // Map common backend types to frontend options
    const typeMapping: { [key: string]: string } = {
      'TEXT': 'TEXT',
      'VARCHAR': 'VARCHAR(255)', // Default to largest VARCHAR if no length specified
      'VARCHAR(10)': 'VARCHAR(255)', // Fix: Upgrade small VARCHAR to larger size
      'VARCHAR(25)': 'VARCHAR(255)', // Fix: Upgrade small VARCHAR to larger size
      'INTEGER': 'INTEGER',
      'BIGINT': 'BIGINT',
      'SMALLINT': 'SMALLINT',
      'DOUBLE PRECISION': 'DOUBLE PRECISION',
      'REAL': 'REAL',
      'BOOLEAN': 'BOOLEAN',
      'TIMESTAMP': 'TIMESTAMP',
      'DATE': 'DATE',
      'TIME': 'TIME'
    };
    
    return typeMapping[backendType] || 'TEXT'; // Default to TEXT for unknown types
  }

  /**
   * Update column data type
   */
  updateColumnType(columnIndex: number, newType: string): void {
    if (this.schemaPreview && this.schemaPreview.columns[columnIndex]) {
      this.schemaPreview.columns[columnIndex].suggested_pg_type = newType;
      // Regenerate CREATE TABLE SQL with updated types
      this.updateCreateTableSQL();
    }
  }

  /**
   * Update the CREATE TABLE SQL based on current column types
   */
  updateCreateTableSQL(): void {
    if (!this.schemaPreview) return;

    const tableName = this.schemaForm.get('tableName')?.value?.trim();
    const schema = this.schemaForm.get('schema')?.value || 'processed_data';
    
    if (!tableName) return;

    // Build column definitions
    const columnDefs = this.schemaPreview.columns.map(col => 
      `    ${col.clean_name} ${col.suggested_pg_type}`
    ).join(',\n');

    // Generate updated CREATE TABLE statement
    this.schemaPreview.create_sql = `CREATE TABLE IF NOT EXISTS ${schema}.${tableName} (
    id BIGSERIAL PRIMARY KEY,
${columnDefs},
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);`;
  }

  /**
   * Get validation error message for table name
   */
  getTableNameError(): string {
    const control = this.schemaForm.get('tableName');
    if (control?.hasError('required')) {
      return 'Table name is required';
    }
    if (control?.hasError('pattern')) {
      return 'Table name must start with a letter and contain only letters, numbers, and underscores';
    }
    if (control?.hasError('duplicate')) {
      return control.errors?.['message'] || 'Table already exists';
    }
    if (control?.hasError('invalid')) {
      return control.errors?.['message'] || 'Invalid table name';
    }
    return '';
  }

  /**
   * Check if form is valid and table can be created
   */
  canCreateTable(): boolean {
    return this.schemaForm.valid && 
           this.schemaPreview?.can_create === true && 
           !this.isLoading && 
           !this.isValidating;
  }

  /**
   * Close dialog without saving
   */
  onCancel(): void {
    this.dialogRef.close();
  }

  /**
   * Save table to warehouse
   */
  onSave(): void {
    if (!this.canCreateTable()) {
      this.snackBar.open('Please fix validation errors before saving', 'Close', { duration: 3000 });
      return;
    }

    this.isLoading = true;

    // Prepare column corrections from user edits
    const columnCorrections: { [key: string]: string } = {};
    if (this.schemaPreview?.columns) {
      this.schemaPreview.columns.forEach(col => {
        columnCorrections[col.clean_name] = col.suggested_pg_type;
      });
    }

    const requestData = {
      query_sql: this.data.sql,
      db_schema: this.schemaForm.get('schema')?.value || 'processed_data',
      user_table_name: this.schemaForm.get('tableName')?.value,
      column_corrections: columnCorrections,
      is_database_mode: this.isDatabaseMode,
      connection_config: this.connectionConfig
    };

    this.snackBar.open(`Creating table and inserting ${this.data.totalRows.toLocaleString()} records...`, 'Close', { 
      duration: 0  // Keep open until manually closed
    });

    // Use different endpoint for database mode
    const endpoint = this.isDatabaseMode ? 
      'http://localhost:8000/api/schema-editor/create-table-database' : 
      'http://localhost:8000/api/schema-editor/create-table';

    this.http.post<any>(endpoint, requestData)
      .subscribe({
        next: (response) => {
          this.isLoading = false;
          
          if (response.success) {
            this.snackBar.dismiss(); // Close the "Creating..." message
            this.snackBar.open(
              `✅ Success! Table "${response.table_name}" created with ${response.total_rows_inserted?.toLocaleString()} records in ${response.total_time_seconds}s`, 
              'Close', 
              { duration: 8000 }
            );
            
            // Close dialog with success result
            this.dialogRef.close({
              success: true,
              tableName: response.table_name,
              schema: response.schema,
              totalRows: response.total_rows_inserted,
              totalTime: response.total_time_seconds,
              insertionStats: response
            });
          } else {
            this.snackBar.dismiss();
            this.snackBar.open(
              `❌ Failed: ${response.message || response.error}`, 
              'Close', 
              { duration: 8000 }
            );
          }
        },
        error: (error) => {
          this.isLoading = false;
          this.snackBar.dismiss();
          
          console.error('Table creation error:', error);
          const errorMessage = error.error?.detail || error.message || 'Unknown error occurred';
          this.snackBar.open(`❌ Error: ${errorMessage}`, 'Close', { duration: 8000 });
        }
      });
  }
} 