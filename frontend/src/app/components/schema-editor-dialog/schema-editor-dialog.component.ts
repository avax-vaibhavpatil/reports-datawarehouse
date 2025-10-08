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
import { MatProgressBarModule } from '@angular/material/progress-bar';
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
  limit?: number; // Optional limit from SQL query builder
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
    MatProgressBarModule,
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
  
  // Two-step process state
  tableCreated = false;
  isCreatingTable = false;
  isInsertingData = false;
  insertionProgress = 0;
  insertionMessage = '';
  createdTableInfo: any = null;
  
  // Progress tracking variables
  insertionStats = {
    rowsInserted: 0,
    totalRows: 0,
    percentage: 0,
    currentChunk: 0,
    totalChunks: 0
  };
  
  // PostgreSQL data type options
  postgresDataTypes = [
    'TEXT', 
    'VARCHAR(2)', 'VARCHAR(3)', 'VARCHAR(10)', 'VARCHAR(15)', 'VARCHAR(25)', 'VARCHAR(30)', 'VARCHAR(50)', 'VARCHAR(100)', 'VARCHAR(255)', 'VARCHAR(500)', 'VARCHAR(1000)', 'VARCHAR(2000)',
    'CHAR(1)', 'CHAR(2)', 'CHAR(3)', 'CHAR(10)',
    'INTEGER', 'BIGINT', 'SMALLINT', 
    'DECIMAL(10,2)', 'DECIMAL(13,2)', 'DECIMAL(15,2)', 'DECIMAL(18,4)',
    'NUMERIC(10,2)', 'NUMERIC(13,2)', 'NUMERIC(15,2)',
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
      const column = this.schemaPreview.columns[columnIndex];
      const originalType = column.suggested_pg_type;
      
      // Check if user is changing from a specific database type to generic TEXT
      if (this.isChangingToGenericType(originalType, newType)) {
        const confirmed = confirm(
          `⚠️ Warning: You're changing "${column.original_name}" from "${originalType}" to "${newType}".\n\n` +
          `This will lose the specific database schema information from your source database.\n\n` +
          `Are you sure you want to continue?`
        );
        
        if (!confirmed) {
          // Revert the selection
          return;
        }
      }
      
      column.suggested_pg_type = newType;
      // Regenerate CREATE TABLE SQL with updated types
      this.updateCreateTableSQL();
    }
  }

  /**
   * Check if user is changing from a specific database type to a generic type
   */
  private isChangingToGenericType(originalType: string, newType: string): boolean {
    // List of generic types that lose specificity
    const genericTypes = ['TEXT', 'VARCHAR', 'CHAR'];
    
    // Check if original type is specific (has length/precision) and new type is generic
    const originalIsSpecific = originalType.includes('(') && originalType.includes(')');
    const newIsGeneric = genericTypes.some(gt => newType.startsWith(gt));
    
    return originalIsSpecific && newIsGeneric;
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
   * Step 1: Create table only (no data insertion)
   */
  createTableOnly(): void {
    if (!this.canCreateTable()) {
      this.snackBar.open('Please fix validation errors before creating table', 'Close', { duration: 3000 });
      return;
    }

    this.isCreatingTable = true;

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

    this.snackBar.open('Creating table with correct schema...', 'Close', { 
      duration: 0  // Keep open until manually closed
    });

    this.http.post<any>('http://localhost:8000/api/schema-editor/create-table-only', requestData)
      .subscribe({
        next: (response) => {
          this.isCreatingTable = false;
          
          if (response.success) {
            this.snackBar.dismiss(); // Close the "Creating..." message
            this.snackBar.open(
              `✅ Table "${response.table_name}" created successfully with correct schema!`, 
              'Close', 
              { duration: 8000 }
            );
            
            // Update state for step 2
            this.tableCreated = true;
            this.createdTableInfo = response;
            
            // Disable table creation form
            this.schemaForm.get('tableName')?.disable();
            this.schemaForm.get('schema')?.disable();
            
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
          this.isCreatingTable = false;
          this.snackBar.dismiss();
          
          console.error('Table creation error:', error);
          const errorMessage = error.error?.detail || error.message || 'Unknown error occurred';
          this.snackBar.open(`❌ Error: ${errorMessage}`, 'Close', { duration: 8000 });
        }
      });
  }

  /**
   * Step 2: Insert data into existing table with real-time progress
   */
  insertData(): void {
    if (!this.tableCreated || !this.createdTableInfo) {
      this.snackBar.open('Please create table first', 'Close', { duration: 3000 });
      return;
    }

    this.isInsertingData = true;
    this.insertionMessage = 'Starting data insertion...';
    this.insertionProgress = 0;
    this.insertionStats = {
      rowsInserted: 0,
      totalRows: 0,
      percentage: 0,
      currentChunk: 0,
      totalChunks: 0
    };

    const requestData = {
      query_sql: this.data.sql,
      db_schema: this.schemaForm.get('schema')?.value || 'processed_data',
      user_table_name: this.schemaForm.get('tableName')?.value,
      limit: this.data.limit || null, // Use limit from SQL query builder, or null for all data
      is_database_mode: this.isDatabaseMode,
      connection_config: this.connectionConfig
    };

    // Use fetch API for Server-Sent Events with POST data
    fetch('http://localhost:8000/api/schema-editor/insert-data-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
      },
      body: JSON.stringify(requestData)
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('No response body reader available');
      }
      
      let buffer = '';
      
      const readStream = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log('📡 Stream reading completed');
            return;
          }
          
          // Decode the chunk and add to buffer
          buffer += decoder.decode(value, { stream: true });
          console.log('📡 Received chunk, buffer length:', buffer.length);
          
          // Process complete lines from buffer
          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer
          
          for (const line of lines) {
            if (line.trim() === '') continue; // Skip empty lines
            
            if (line.startsWith('data: ')) {
              try {
                const jsonData = line.substring(6).trim();
                if (jsonData) {
                  console.log('📡 Parsing JSON:', jsonData);
                  const data = JSON.parse(jsonData);
                  this.handleProgressUpdate(data);
                }
              } catch (error) {
                console.error('Error parsing progress data:', error, 'Line:', line);
              }
            }
          }
          
          readStream();
        }).catch(error => {
          console.error('Error reading stream:', error);
          this.isInsertingData = false;
          this.insertionMessage = 'Data insertion failed';
          this.snackBar.open(`❌ Error: ${error.message}`, 'Close', { duration: 5000 });
        });
      };
      
      readStream();
    }).catch(error => {
      console.error('Error during data insertion:', error);
      this.handleInsertionError(error);
    });
  }

  /**
   * Test SSE connection (for debugging)
   */
  testSSEConnection(): void {
    console.log('🧪 Testing SSE connection...');
    
    fetch('http://localhost:8000/api/schema-editor/test-sse', {
      method: 'GET',
      headers: {
        'Accept': 'text/event-stream',
        'Cache-Control': 'no-cache'
      }
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      
      if (!reader) {
        throw new Error('No response body reader available');
      }
      
      let buffer = '';
      
      const readStream = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            console.log('🧪 SSE test completed');
            return;
          }
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            if (line.trim() === '') continue;
            
            if (line.startsWith('data: ')) {
              try {
                const jsonData = line.substring(6).trim();
                if (jsonData) {
                  console.log('🧪 SSE test data:', jsonData);
                  const data = JSON.parse(jsonData);
                  console.log('🧪 Parsed SSE data:', data);
                }
              } catch (error) {
                console.error('🧪 Error parsing SSE test data:', error);
              }
            }
          }
          
          readStream();
        }).catch(error => {
          console.error('🧪 SSE test error:', error);
        });
      };
      
      readStream();
    }).catch(error => {
      console.error('🧪 SSE connection test failed:', error);
    });
  }

  /**
   * Handle insertion errors with better user feedback
   */
  private handleInsertionError(error: any): void {
    this.isInsertingData = false;
    this.insertionMessage = 'Data insertion failed';
    this.insertionProgress = 0;
    
    let errorMessage = 'Unknown error occurred';
    
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
      errorMessage = 'Connection failed. Please check if the server is running.';
    } else if (error.message.includes('timeout')) {
      errorMessage = 'Request timed out. The operation may still be running.';
    } else if (error.message.includes('HTTP error')) {
      errorMessage = `Server error: ${error.message}`;
    } else {
      errorMessage = error.message || error.toString();
    }
    
    this.snackBar.open(`❌ Error: ${errorMessage}`, 'Close', { duration: 8000 });
  }

  /**
   * Handle progress updates from Server-Sent Events
   */
  private handleProgressUpdate(data: any): void {
    console.log('📊 Progress update received:', data);
    
    switch (data.type) {
      case 'start':
        console.log('🚀 Starting data insertion');
        this.insertionMessage = data.message;
        this.insertionProgress = 0;
        this.insertionStats = {
          rowsInserted: 0,
          totalRows: data.total_rows || 0,
          percentage: 0,
          currentChunk: 0,
          totalChunks: data.total_chunks || 0
        };
        break;
        
      case 'progress':
        console.log(`📈 Progress: ${data.percentage}% (${data.rows_inserted}/${data.total_rows} rows)`);
        this.insertionProgress = data.progress || data.percentage || 0;
        this.insertionMessage = data.message || `Processing chunk ${data.chunk_index}/${data.total_chunks}`;
        this.insertionStats = {
          rowsInserted: data.rows_inserted || 0,
          totalRows: data.total_rows || 0,
          percentage: data.percentage || data.progress || 0,
          currentChunk: data.chunk_index || 0,
          totalChunks: data.total_chunks || 0
        };
        
        // Force change detection for real-time updates
        setTimeout(() => {
          // Trigger change detection
        }, 0);
        break;
        
      case 'complete':
        console.log('✅ Data insertion completed');
        this.isInsertingData = false;
        this.insertionProgress = 100;
        this.insertionMessage = data.message || 'Data insertion completed successfully!';
        
        // Update final stats
        this.insertionStats = {
          rowsInserted: data.inserted_rows || this.insertionStats.rowsInserted,
          totalRows: data.inserted_rows || this.insertionStats.totalRows,
          percentage: 100,
          currentChunk: this.insertionStats.totalChunks,
          totalChunks: this.insertionStats.totalChunks
        };
        
        this.snackBar.open(
          `✅ Success! Data inserted successfully into table '${this.schemaForm.get('tableName')?.value}'`, 
          'Close', 
          { duration: 5000 }
        );
        
        // Close dialog with success result
        this.dialogRef.close({
          success: true,
          tableName: this.schemaForm.get('tableName')?.value,
          schema: this.schemaForm.get('schema')?.value || 'processed_data',
          message: 'Data insertion completed successfully!',
          insertionStats: {
            insertedRows: data.inserted_rows,
            totalTime: data.total_time,
            rowsPerSecond: data.rows_per_second
          }
        });
        break;
        
      case 'error':
        console.log('❌ Data insertion error:', data.message);
        this.isInsertingData = false;
        this.insertionMessage = 'Data insertion failed';
        this.insertionProgress = 0;
        this.snackBar.open(`❌ Error: ${data.message}`, 'Close', { duration: 5000 });
        break;
        
      default:
        console.log('❓ Unknown progress update type:', data.type);
        break;
    }
  }

  /**
   * Save table to warehouse (legacy method - now calls createTableOnly)
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