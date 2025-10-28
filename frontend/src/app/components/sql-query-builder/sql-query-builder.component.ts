import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, FormArray, Validators, ReactiveFormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatStepperModule } from '@angular/material/stepper';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatSortModule } from '@angular/material/sort';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { ActivatedRoute, Router } from '@angular/router';
import { HttpClient } from '@angular/common/http';
import { SQLQueryService, TableInfo, JoinType, SQLQueryRequest, SQLQueryResponse } from '../../services/sql-query.service';
import { SchemaEditorDialogComponent, SchemaEditorData } from '../schema-editor-dialog/schema-editor-dialog.component';
import { ColumnMatchingService, ColumnRelationship } from '../../services/column-matching.service';
import { FilenameDialogComponent, FilenameDialogData } from '../filename-dialog/filename-dialog.component';
import { ProgressDialogComponent, ProgressDialogData } from '../progress-dialog/progress-dialog.component';

@Component({
  selector: 'app-sql-query-builder',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FormsModule,
    MatSnackBarModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatCheckboxModule,
    MatDialogModule,
    MatStepperModule,
    MatProgressBarModule,
    MatTabsModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatTooltipModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './sql-query-builder.component.html',
  styleUrls: ['./sql-query-builder.component.css']
})
export class SQLQueryBuilderComponent implements OnInit {
  // Wizard state
  currentStep = 0;
  totalSteps = 4;
  stepLabels = ['Build Query', 'Review Query', 'Preview Data', 'Save to Warehouse'];
  stepCompleted: boolean[] = [false, false, false, false];
  
  queryForm: FormGroup;
  availableTables: TableInfo[] = [];
  joinTypes: JoinType[] = [];
  generatedSQL: string = '';
  formattedSQL: string = '';
  queryResponse: SQLQueryResponse | null = null;
  isLoading = false;
  showPreview = false;
  queryResults: any[] = [];
  queryColumns: string[] = [];
  totalRows = 0;
  executionTime = '';
  isExecuting = false;
  
  // Database connection properties
  isDatabaseMode = false;
  connectionConfig: any = null;
  selectedTables: string[] = [];
  
  // Warehouse save data
  warehouseSchema: string = '';
  warehouseTable: string = '';
  isSaving = false;
  
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
  
  // Schema editor integration properties
  schemaForm: FormGroup;
  schemaPreview: any = null;
  isSchemaLoading = false;
  isValidating = false;
  tableCreated = false;
  createdTableInfo: any = null;
  isCreatingTable = false;
  isInsertingData = false;
  insertionProgress = 0;
  insertionMessage = '';
  insertionStats: any = null;
  availableSchemas: string[] = [];

  constructor(
    private fb: FormBuilder,
    private sqlQueryService: SQLQueryService,
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private columnMatchingService: ColumnMatchingService,
    private route: ActivatedRoute,
    private router: Router,
    private http: HttpClient
  ) {
    this.queryForm = this.createForm();
    this.schemaForm = this.createSchemaForm();
  }

  ngOnInit(): void {
    // Check if we have database connection parameters
    this.route.queryParams.subscribe((params: any) => {
      if (params['dbMode'] === 'true' && params['connectionConfig']) {
        this.isDatabaseMode = true;
        this.connectionConfig = JSON.parse(params['connectionConfig']);
        this.selectedTables = params['selectedTables'] ? JSON.parse(params['selectedTables']) : [];
        this.loadDatabaseTables();
      } else {
        this.loadAvailableTables();
      }
    });
    
    this.loadJoinTypes();
  }

  createForm(): FormGroup {
    return this.fb.group({
      tables: this.fb.array([]),
      joins: this.fb.array([]),
      where_conditions: this.fb.array([]),
      group_by: this.fb.array([]),
      order_by: this.fb.array([]),
      limit: [null]
    });
  }

  createSchemaForm(): FormGroup {
    return this.fb.group({
      schema: ['processed_data', Validators.required],
      tableName: ['', Validators.required]
    });
  }

  get tablesArray(): FormArray {
    return this.queryForm.get('tables') as FormArray;
  }

  get joinsArray(): FormArray {
    return this.queryForm.get('joins') as FormArray;
  }

  get whereConditionsArray(): FormArray {
    return this.queryForm.get('where_conditions') as FormArray;
  }

  get groupByArray(): FormArray {
    return this.queryForm.get('group_by') as FormArray;
  }

  get orderByArray(): FormArray {
    return this.queryForm.get('order_by') as FormArray;
  }

  getTableColumnsArray(tableIndex: number): FormArray {
    return this.tablesArray.at(tableIndex).get('columns') as FormArray;
  }

  getJoinConditionsArray(joinIndex: number): FormArray {
    return this.joinsArray.at(joinIndex).get('conditions') as FormArray;
  }

  // Wizard navigation methods
  nextStep(): void {
    if (this.canProceedToNext()) {
      this.markStepCompleted(this.currentStep);
      this.currentStep++;
    }
  }

  previousStep(): void {
    if (this.currentStep > 0) {
      this.currentStep--;
    }
  }

  goToStep(step: number): void {
    if (step >= 0 && step < this.totalSteps && this.canGoToStep(step)) {
      this.currentStep = step;
    }
  }

  canProceedToNext(): boolean {
    switch (this.currentStep) {
      case 0: // Build Query
        return this.tablesArray.length > 0 && this.queryForm.valid;
      case 1: // Review Query
        return this.generatedSQL.length > 0;
      case 2: // Preview Data
        return this.queryResults.length > 0 || this.stepCompleted[2];
      case 3: // Save to Warehouse
        return this.queryResults.length > 0;
      default:
        return false;
    }
  }

  canGoToStep(step: number): boolean {
    // Can go to any completed step or the next step
    return this.stepCompleted[step] || step === this.currentStep + 1;
  }

  markStepCompleted(step: number): void {
    this.stepCompleted[step] = true;
  }

  finishWizard(): void {
    if (this.canProceedToNext()) {
      this.saveToWarehouse();
    }
  }

  getStepProgress(): number {
    return ((this.currentStep + 1) / this.totalSteps) * 100;
  }

  isStepAccessible(step: number): boolean {
    return step <= this.currentStep || this.stepCompleted[step];
  }

  getJoinColumnsArray(joinIndex: number): FormArray {
    return this.joinsArray.at(joinIndex).get('columns') as FormArray;
  }

  getJoinTableName(joinIndex: number): string {
    return this.joinsArray.at(joinIndex).get('table')?.value || '';
  }

  getJoinTableColumns(joinIndex: number): string[] {
    const tableName = this.getJoinTableName(joinIndex);
    const table = this.availableTables.find(t => t.name === tableName);
    return table?.columns || [];
  }

  getTableName(tableIndex: number): string {
    return this.tablesArray.at(tableIndex).get('name')?.value || '';
  }

  getTableColumns(tableIndex: number): string[] {
    const tableName = this.getTableName(tableIndex);
    const table = this.availableTables.find(t => t.name === tableName);
    return table?.columns || [];
  }

  getCustomExpressionsArray(tableIndex: number): FormArray {
    return (this.tablesArray.at(tableIndex) as FormGroup).get('custom_expressions') as FormArray;
  }

  addCustomExpression(tableIndex: number): void {
    const customExpressionsArray = this.getCustomExpressionsArray(tableIndex);
    const expressionControl = this.fb.control('', Validators.required);
    customExpressionsArray.push(expressionControl);
  }

  removeCustomExpression(tableIndex: number, expressionIndex: number): void {
    const customExpressionsArray = this.getCustomExpressionsArray(tableIndex);
    customExpressionsArray.removeAt(expressionIndex);
  }

  loadAvailableTables(): void {
    this.isSchemaLoading = true;
    this.sqlQueryService.getAvailableTables().subscribe({
      next: (response) => {
        this.availableTables = response.tables;
        this.isSchemaLoading = false;
      },
      error: (error) => {
        console.error('Error loading tables:', error);
        this.snackBar.open('Error loading available tables', 'Close', { duration: 3000 });
        this.isSchemaLoading = false;
      }
    });
  }

  loadDatabaseTables(): void {
    this.isSchemaLoading = true;
    this.sqlQueryService.getDatabaseTables(this.connectionConfig).subscribe({
      next: (response) => {
        this.availableTables = response.tables;
        this.isSchemaLoading = false;
        
        // Don't auto-add tables - let user select from dropdown
        // Just show success message
        this.snackBar.open(`Loaded ${response.tables.length} database tables. Use the dropdown to select tables.`, 'Close', { duration: 5000 });
      },
      error: (error) => {
        console.error('Error loading database tables:', error);
        this.snackBar.open('Error loading database tables', 'Close', { duration: 3000 });
        this.isSchemaLoading = false;
      }
    });
  }

  loadJoinTypes(): void {
    this.sqlQueryService.getSupportedJoinTypes().subscribe({
      next: (response) => {
        this.joinTypes = response.join_types;
      },
      error: (error) => {
        console.error('Error loading join types:', error);
      }
    });
  }

  addTable(): void {
    const tableForm = this.fb.group({
      name: ['', Validators.required],
      alias: [''],
      columns: this.fb.array([]),
      selectAll: [false],
      custom_expressions: this.fb.array([])
    });
    this.tablesArray.push(tableForm);
  }

  addTableWithData(table: TableInfo): void {
    const tableForm = this.fb.group({
      name: [table.name, Validators.required],
      alias: [''],
      columns: this.fb.array([]),
      selectAll: [false],
      custom_expressions: this.fb.array([])
    });
    this.tablesArray.push(tableForm);
  }

  clearAllTables(): void {
    this.tablesArray.clear();
  }

  removeTable(index: number): void {
    this.tablesArray.removeAt(index);
  }

  addJoin(): void {
    const joinForm = this.fb.group({
      type: ['INNER JOIN', Validators.required],
      table: ['', Validators.required],
      alias: [''],
      left_table: [''],
      right_table: [''],
      columns: this.fb.array([]),
      selectAll: [false],
      conditions: this.fb.array([])
    });
    this.joinsArray.push(joinForm);
  }

  removeJoin(index: number): void {
    this.joinsArray.removeAt(index);
  }

  addJoinCondition(joinIndex: number): void {
    const conditionForm = this.fb.group({
      left_table: ['', Validators.required],
      left_column: ['', Validators.required],
      operator: ['=', Validators.required],
      right_table: ['', Validators.required],
      right_column: ['', Validators.required]
    });
    const joinForm = this.joinsArray.at(joinIndex) as FormGroup;
    const conditionsArray = joinForm.get('conditions') as FormArray;
    conditionsArray.push(conditionForm);
  }

  removeJoinCondition(joinIndex: number, conditionIndex: number): void {
    const joinForm = this.joinsArray.at(joinIndex) as FormGroup;
    const conditionsArray = joinForm.get('conditions') as FormArray;
    conditionsArray.removeAt(conditionIndex);
  }

  addWhereCondition(): void {
    const whereForm = this.fb.group({
      left_side: ['', Validators.required],
      operator: ['=', Validators.required],
      right_side: ['', Validators.required],
      logical_operator: ['AND']
    });
    this.whereConditionsArray.push(whereForm);
  }

  removeWhereCondition(index: number): void {
    this.whereConditionsArray.removeAt(index);
  }

  addGroupBy(): void {
    const groupByForm = this.fb.group({
      column: ['', Validators.required]
    });
    this.groupByArray.push(groupByForm);
  }

  removeGroupBy(index: number): void {
    this.groupByArray.removeAt(index);
  }

  addOrderBy(): void {
    const orderByForm = this.fb.group({
      column: ['', Validators.required],
      direction: ['ASC']
    });
    this.orderByArray.push(orderByForm);
  }

  removeOrderBy(index: number): void {
    this.orderByArray.removeAt(index);
  }

  onTableChange(tableIndex: number): void {
    const tableForm = this.tablesArray.at(tableIndex) as FormGroup;
    const selectedTableName = tableForm.get('name')?.value;
    
    if (selectedTableName) {
      const selectedTable = this.availableTables.find(t => t.name === selectedTableName);
      if (selectedTable) {
        // Clear existing columns and add all available columns (unselected by default)
        const columnsArray = tableForm.get('columns') as FormArray;
        columnsArray.clear();
        
        selectedTable.columns.forEach(() => {
          const columnControl = this.fb.control(false); // Start with false (unselected)
          columnsArray.push(columnControl);
        });
        
        // Reset select all checkbox
        tableForm.get('selectAll')?.setValue(false);
      }
    }
  }

  onJoinTableChange(joinIndex: number): void {
    const joinForm = this.joinsArray.at(joinIndex) as FormGroup;
    const selectedTableName = joinForm.get('table')?.value;
    
    if (selectedTableName) {
      // Update the right_table field for auto-suggestion
      joinForm.get('right_table')?.setValue(selectedTableName);
      
      // Get the left table (first table in the query)
      const leftTableName = this.tablesArray.at(0)?.get('name')?.value;
      if (leftTableName) {
        joinForm.get('left_table')?.setValue(leftTableName);
        
        // Auto-suggest relationships if no conditions exist yet
        const conditionsArray = joinForm.get('conditions') as FormArray;
        if (conditionsArray.length === 0) {
          setTimeout(() => {
            this.suggestColumnRelationships(joinIndex);
          }, 500);
        }
      }
    }
  }

  toggleSelectAllColumns(tableIndex: number): void {
    const tableForm = this.tablesArray.at(tableIndex) as FormGroup;
    const selectAllValue = tableForm.get('selectAll')?.value;
    const columnsArray = tableForm.get('columns') as FormArray;
    
    // Update all column checkboxes to match select all state
    columnsArray.controls.forEach(control => {
      control.setValue(selectAllValue);
    });
  }

  onIndividualColumnChange(tableIndex: number): void {
    const tableForm = this.tablesArray.at(tableIndex) as FormGroup;
    const columnsArray = tableForm.get('columns') as FormArray;
    const selectAllControl = tableForm.get('selectAll');
    
    // Check if all columns are selected
    const allSelected = columnsArray.controls.every(control => control.value);
    const noneSelected = columnsArray.controls.every(control => !control.value);
    
    // Update select all checkbox state
    if (allSelected) {
      selectAllControl?.setValue(true);
    } else if (noneSelected) {
      selectAllControl?.setValue(false);
    } else {
      // Some columns selected - set to indeterminate state
      selectAllControl?.setValue(false);
    }
  }

  toggleSelectAllJoinColumns(joinIndex: number): void {
    const joinForm = this.joinsArray.at(joinIndex) as FormGroup;
    const selectAllValue = joinForm.get('selectAll')?.value;
    const columnsArray = joinForm.get('columns') as FormArray;
    
    // Update all column checkboxes to match select all state
    columnsArray.controls.forEach(control => {
      control.setValue(selectAllValue);
    });
  }

  onIndividualJoinColumnChange(joinIndex: number): void {
    const joinForm = this.joinsArray.at(joinIndex) as FormGroup;
    const columnsArray = joinForm.get('columns') as FormArray;
    const selectAllControl = joinForm.get('selectAll');
    
    // Check if all columns are selected
    const allSelected = columnsArray.controls.every(control => control.value);
    const noneSelected = columnsArray.controls.every(control => !control.value);
    
    // Update select all checkbox state
    if (allSelected) {
      selectAllControl?.setValue(true);
    } else if (noneSelected) {
      selectAllControl?.setValue(false);
    } else {
      // Some columns selected - set to indeterminate state
      selectAllControl?.setValue(false);
    }
  }

  generateSQL(): void {
    if (this.queryForm.valid) {
      this.isSchemaLoading = true;
      
      const formValue = this.queryForm.value;
      const request: SQLQueryRequest = {
        tables: formValue.tables.map((table: any, tableIndex: number) => {
          // Filter only selected columns
          const selectedColumns: string[] = [];
          const actualColumns = this.getTableColumns(tableIndex);
          table.columns.forEach((isSelected: boolean, colIndex: number) => {
            if (isSelected && actualColumns[colIndex]) {
              selectedColumns.push(actualColumns[colIndex]);
            }
          });
          
          return {
            name: table.name,
            alias: table.alias || undefined,
            columns: selectedColumns,
            custom_expressions: table.custom_expressions || []
          };
        }).filter((table: any) => table.columns.length > 0), // Only include tables with selected columns
        joins: formValue.joins.map((join: any, joinIndex: number) => {
          // Get columns for joined table
          const joinTable = this.availableTables.find(t => t.name === join.table);
          const selectedJoinColumns: string[] = [];
          
          if (joinTable && join.columns) {
            join.columns.forEach((isSelected: boolean, colIndex: number) => {
              if (isSelected && joinTable.columns[colIndex]) {
                selectedJoinColumns.push(joinTable.columns[colIndex]);
              }
            });
          }
          
          return {
            type: join.type,
            table: join.table,
            alias: join.alias || undefined,
            columns: selectedJoinColumns,
            conditions: join.conditions || []
          };
        }),
        where_conditions: formValue.where_conditions.map((where: any) => ({
          left_side: where.left_side,
          operator: where.operator,
          right_side: where.right_side,
          logical_operator: where.logical_operator
        })),
        group_by: formValue.group_by.map((gb: any) => gb.column).filter((col: string) => col),
        order_by: formValue.order_by.map((ob: any) => ({
          column: ob.column,
          direction: ob.direction
        })),
        limit: formValue.limit || undefined,
        source_type: this.isDatabaseMode ? 'database' : 'file',
        connection_config: this.isDatabaseMode ? this.connectionConfig : undefined
      };

      if (this.isDatabaseMode) {
        // Use database query generation
        this.sqlQueryService.generateDatabaseSQLQuery(this.connectionConfig, request).subscribe({
          next: (response) => {
            this.queryResponse = response;
            this.generatedSQL = response.sql;
            this.formattedSQL = response.formatted_sql;
            this.isSchemaLoading = false;
            this.markStepCompleted(1);
            this.snackBar.open('SQL query generated and executed successfully!', 'Close', { duration: 3000 });
          },
          error: (error) => {
            console.error('Error generating database SQL:', error);
            this.snackBar.open('Error generating database SQL query', 'Close', { duration: 3000 });
            this.isSchemaLoading = false;
          }
        });
      } else {
        // Use file-based query generation
        this.sqlQueryService.generateSQLQuery(request).subscribe({
          next: (response) => {
            this.queryResponse = response;
            this.generatedSQL = response.sql;
            this.formattedSQL = response.formatted_sql;
            this.isSchemaLoading = false;
            this.markStepCompleted(1);
            this.snackBar.open('SQL query generated successfully!', 'Close', { duration: 3000 });
          },
          error: (error) => {
            console.error('Error generating SQL:', error);
            this.snackBar.open('Error generating SQL query', 'Close', { duration: 3000 });
            this.isSchemaLoading = false;
          }
        });
      }
    } else {
      this.snackBar.open('Please fill in all required fields', 'Close', { duration: 3000 });
    }
  }

  editSQL(): void {
    // Allow manual editing of SQL
    const dialogRef = this.dialog.open(SchemaEditorDialogComponent, {
      width: '80%',
      height: '80%',
      data: {
        title: 'Edit SQL Query',
        content: this.generatedSQL,
        isEditable: true
      }
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result) {
        this.generatedSQL = result;
        this.formattedSQL = result;
      }
    });
  }

  validateQuery(): void {
    if (this.queryForm.valid) {
      const formValue = this.queryForm.value;
      const request: SQLQueryRequest = {
        tables: formValue.tables.map((table: any) => ({
          name: table.name,
          alias: table.alias || undefined,
          columns: table.columns || []
        })),
        joins: formValue.joins.map((join: any) => ({
          type: join.type,
          table: join.table,
          alias: join.alias || undefined,
          conditions: join.conditions || []
        })),
        where_conditions: formValue.where_conditions.map((where: any) => ({
          left_side: where.left_side,
          operator: where.operator,
          right_side: where.right_side,
          logical_operator: where.logical_operator
        })),
        group_by: formValue.group_by.map((gb: any) => gb.column).filter((col: string) => col),
        order_by: formValue.order_by.map((ob: any) => ({
          column: ob.column,
          direction: ob.direction
        })),
        limit: formValue.limit || undefined
      };

      this.sqlQueryService.validateQueryConfig(request).subscribe({
        next: (response) => {
          if (response.valid) {
            this.snackBar.open('Query configuration is valid!', 'Close', { duration: 3000 });
          } else {
            this.snackBar.open(`Validation errors: ${response.errors.join(', ')}`, 'Close', { duration: 5000 });
          }
        },
        error: (error) => {
          console.error('Error validating query:', error);
          this.snackBar.open('Error validating query configuration', 'Close', { duration: 3000 });
        }
      });
    }
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      this.snackBar.open('SQL copied to clipboard!', 'Close', { duration: 2000 });
    });
  }

  clearForm(): void {
    this.queryForm = this.createForm();
    this.generatedSQL = '';
    this.formattedSQL = '';
    this.queryResponse = null;
    this.queryResults = [];
    this.queryColumns = [];
    this.totalRows = 0;
    this.executionTime = '';
    this.showPreview = false;
  }

  togglePreview(): void {
    this.showPreview = !this.showPreview;
  }

  private processQueryConfiguration(): SQLQueryRequest {
    const formValue = this.queryForm.value;
    return {
      tables: formValue.tables.map((table: any, tableIndex: number) => {
        // Filter only selected columns
        const selectedColumns: string[] = [];
        const actualColumns = this.getTableColumns(tableIndex);
        table.columns.forEach((isSelected: boolean, colIndex: number) => {
          if (isSelected && actualColumns[colIndex]) {
            selectedColumns.push(actualColumns[colIndex]);
          }
        });
        
        return {
          name: table.name,
          alias: table.alias || undefined,
          columns: selectedColumns,
          custom_expressions: table.custom_expressions || []
        };
      }).filter((table: any) => table.columns.length > 0),
      joins: formValue.joins.map((join: any, joinIndex: number) => {
        // Get columns for joined table
        const joinTable = this.availableTables.find(t => t.name === join.table);
        const selectedJoinColumns: string[] = [];
        
        if (joinTable && join.columns) {
          join.columns.forEach((isSelected: boolean, colIndex: number) => {
            if (isSelected && joinTable.columns[colIndex]) {
              selectedJoinColumns.push(joinTable.columns[colIndex]);
            }
          });
        }
        
        return {
          type: join.type,
          table: join.table,
          alias: join.alias || undefined,
          columns: selectedJoinColumns,
          conditions: join.conditions || []
        };
      }),
      where_conditions: formValue.where_conditions.map((where: any) => ({
        left_side: where.left_side,
        operator: where.operator,
        right_side: where.right_side,
        logical_operator: where.logical_operator
      })),
      group_by: formValue.group_by.map((gb: any) => gb.column).filter((col: string) => col),
      order_by: formValue.order_by.map((ob: any) => ({
        column: ob.column,
        direction: ob.direction
      })),
      limit: formValue.limit || undefined
    };
  }

  executeQuery(): void {
    if (this.queryForm.valid) {
      this.isExecuting = true;
      
      if (this.isDatabaseMode && this.generatedSQL) {
        // Use database preview for database mode
        this.sqlQueryService.previewDatabaseQuery(this.connectionConfig, this.generatedSQL, 1000).subscribe({
          next: (response) => {
            this.queryResults = response.data || [];
            this.queryColumns = response.columns || [];
            this.totalRows = response.row_count || 0;
            this.executionTime = response.execution_time || '';
            this.isExecuting = false;
            this.showPreview = true;
            this.markStepCompleted(2);
            this.snackBar.open(`Query executed successfully! Showing ${this.queryResults.length} rows.`, 'Close', { duration: 3000 });
          },
          error: (error) => {
            console.error('Error executing database query:', error);
            this.snackBar.open('Error executing database query', 'Close', { duration: 3000 });
            this.isExecuting = false;
          }
        });
      } else {
        // Use file-based query execution
        const request: SQLQueryRequest = this.processQueryConfiguration();

        this.sqlQueryService.executeQuery({ query_config: request, sample_size: 1000 }).subscribe({
          next: (response) => {
            this.queryResults = response.sample_data || [];
            this.queryColumns = response.columns || [];
            this.totalRows = response.total_rows || 0;
            this.executionTime = response.execution_time || '';
            this.isExecuting = false;
            this.showPreview = true;
            this.markStepCompleted(2);
            this.snackBar.open(`Query executed successfully! Showing ${this.queryResults.length} out of ${this.totalRows.toLocaleString()} records.`, 'Close', { duration: 3000 });
          },
          error: (error) => {
            console.error('Error executing query:', error);
            this.snackBar.open('Error executing query', 'Close', { duration: 3000 });
            this.isExecuting = false;
          }
        });
      }
    } else {
      this.snackBar.open('Please fill in all required fields', 'Close', { duration: 3000 });
    }
  }

  exportToCSV(): void {
    if (this.queryResults.length === 0) {
      this.snackBar.open('No data to export', 'Close', { duration: 2000 });
      return;
    }

    // Generate default filename
    const defaultFilename = `query_results_${new Date().toISOString().split('T')[0]}.csv`;
    
    // Process query configuration the same way as executeQuery()
    const processedQueryConfig = this.processQueryConfiguration();

    // Open filename dialog
    const dialogRef = this.dialog.open(FilenameDialogComponent, {
      width: '500px',
      data: { 
        defaultFilename: defaultFilename,
        useBackendExport: true,
        queryConfig: processedQueryConfig
      } as FilenameDialogData
    });

    dialogRef.afterClosed().subscribe((result: any) => {
      if (result) {
        this.performBackendCSVExport(result.filename, result.queryConfig);
      }
    });
  }


  private performBackendCSVExport(filename: string, queryConfig: any): void {
    this.snackBar.open('Exporting CSV...', 'Close', { duration: 1000 });
    
    this.sqlQueryService.exportToCSV(queryConfig, filename).subscribe({
      next: (blob: Blob) => {
        // Create download link for the blob
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        window.URL.revokeObjectURL(url);
        
        this.snackBar.open(`Data exported to ${filename} successfully!`, 'Close', { duration: 3000 });
      },
      error: (error) => {
        console.error('CSV export error:', error);
        this.snackBar.open('Export failed. Please try again.', 'Close', { duration: 3000 });
      }
    });
  }

  openSchemaEditor(): void {
    // Check if we have query results to work with
    if (!this.generatedSQL || this.queryResults.length === 0) {
      this.snackBar.open('Please execute a query first to save results to warehouse', 'Close', { duration: 3000 });
      return;
    }

    if (this.isDatabaseMode) {
      // For database mode, use schema editor dialog (same as file mode)
      // Prepare data for the schema editor dialog
      const dialogData: SchemaEditorData = {
        sql: this.generatedSQL,
        totalRows: this.totalRows,
        columns: this.queryColumns,
        sampleData: this.queryResults.slice(0, 5),
        isDatabaseMode: true,
        connectionConfig: this.connectionConfig,
        limit: this.queryForm.get('limit')?.value || undefined // Pass limit from form
      };

      // Open the schema editor dialog
      const dialogRef = this.dialog.open(SchemaEditorDialogComponent, {
        width: '90vw',
        maxWidth: '900px',
        maxHeight: '90vh',
        data: dialogData,
        disableClose: true // Prevent accidental closing
      });

      // Handle dialog result
      dialogRef.afterClosed().subscribe((result: any) => {
        if (result?.success) {
          // Table was successfully created and data inserted
          this.snackBar.open(
            `🎉 Data Warehouse Updated! Table "${result.tableName}" now contains ${result.totalRows?.toLocaleString()} records from your query.`, 
            'Close', 
            { duration: 6000 }
          );
          console.log('Table Creation Success:', result.insertionStats);
        } else if (result) {
          // Dialog was closed with some result but not successful
          console.log('Schema Editor Result:', result);
        }
      });
    } else {
      // For file mode, use schema editor dialog
      // Prepare data for the schema editor dialog
      const dialogData: SchemaEditorData = {
        sql: this.generatedSQL,
        totalRows: this.totalRows,
        columns: this.queryColumns,
        sampleData: this.queryResults.slice(0, 5),
        limit: this.queryForm.get('limit')?.value || undefined // Pass limit from form
      };

      // Open the schema editor dialog
      const dialogRef = this.dialog.open(SchemaEditorDialogComponent, {
        width: '90vw',
        maxWidth: '900px',
        maxHeight: '90vh',
        data: dialogData,
        disableClose: true // Prevent accidental closing
      });

      // Handle dialog result
      dialogRef.afterClosed().subscribe((result: any) => {
        if (result?.success) {
          // Table was successfully created and data inserted
          this.snackBar.open(
            `🎉 Data Warehouse Updated! Table "${result.tableName}" now contains ${result.totalRows?.toLocaleString()} records from your query.`, 
            'Close', 
            { duration: 6000 }
          );
          console.log('Table Creation Success:', result.insertionStats);
        } else if (result) {
          // Dialog was closed with some result but not successful
          console.log('Schema Editor Result:', result);
        }
      });
    }
  }


  /**
   * Suggest column relationships for a specific join
   */
  suggestColumnRelationships(joinIndex: number): void {
    const joinForm = this.joinsArray.at(joinIndex);
    const leftTable = joinForm.get('left_table')?.value;
    const rightTable = joinForm.get('right_table')?.value;
    
    if (!leftTable || !rightTable) {
      this.snackBar.open('Please select both left and right tables first', 'Close', { duration: 3000 });
      return;
    }

    this.isSchemaLoading = true;
    
    this.columnMatchingService.suggestRelationships({
      left_table: leftTable,
      right_table: rightTable,
      connection_config: this.isDatabaseMode ? this.connectionConfig : undefined
    }).subscribe({
      next: (response) => {
        this.isSchemaLoading = false;
        if (response.success && response.relationships.length > 0) {
          this.applySuggestedRelationships(joinIndex, response.relationships);
          this.snackBar.open(
            `Found ${response.total_matches} matching columns! Relationships added automatically.`, 
            'Close', 
            { duration: 4000 }
          );
        } else {
          this.snackBar.open('No matching columns found between these tables', 'Close', { duration: 3000 });
        }
      },
      error: (error) => {
        this.isSchemaLoading = false;
        console.error('Error suggesting relationships:', error);
        this.snackBar.open('Error suggesting relationships. Please try again.', 'Close', { duration: 3000 });
      }
    });
  }

  /**
   * Apply suggested relationships to a join
   */
  private applySuggestedRelationships(joinIndex: number, relationships: ColumnRelationship[]): void {
    const joinForm = this.joinsArray.at(joinIndex);
    const conditionsArray = joinForm.get('conditions') as FormArray;
    
    // Clear existing conditions
    while (conditionsArray.length !== 0) {
      conditionsArray.removeAt(0);
    }
    
    // Add suggested relationships
    relationships.forEach(relationship => {
      const conditionGroup = this.fb.group({
        left_table: [relationship.left_table],
        left_column: [relationship.left_column],
        operator: ['='],
        right_table: [relationship.right_table],
        right_column: [relationship.right_column]
      });
      
      conditionsArray.push(conditionGroup);
    });
  }

  /**
   * Auto-suggest relationships when tables are selected
   */
  onTableSelectionChange(joinIndex: number): void {
    const joinForm = this.joinsArray.at(joinIndex);
    const leftTable = joinForm.get('left_table')?.value;
    const rightTable = joinForm.get('right_table')?.value;
    
    // Only suggest if both tables are selected and no conditions exist yet
    if (leftTable && rightTable) {
      const conditionsArray = joinForm.get('conditions') as FormArray;
      if (conditionsArray.length === 0) {
        // Auto-suggest after a short delay to avoid too many requests
        setTimeout(() => {
          this.suggestColumnRelationships(joinIndex);
        }, 500);
      }
    }
  }

  /**
   * Clear all suggested relationships for a join
   */
  clearSuggestedRelationships(joinIndex: number): void {
    const joinForm = this.joinsArray.at(joinIndex);
    const conditionsArray = joinForm.get('conditions') as FormArray;
    
    // Clear all conditions
    while (conditionsArray.length !== 0) {
      conditionsArray.removeAt(0);
    }
    
    this.snackBar.open('All relationships cleared', 'Close', { duration: 2000 });
  }

  private convertToCSV(data: any[], columns: string[]): string {
    if (data.length === 0) return '';
    
    // CSV header
    const header = columns.join(',');
    
    // CSV rows
    const rows = data.map(row => 
      columns.map(col => {
        const value = row[col];
        // Escape values that contain commas or quotes
        if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    );
    
    return [header, ...rows].join('\n');
  }

  // Schema Editor Methods (integrated from SchemaEditorDialogComponent)
  generateSchemaPreview(): void {
    const tableName = this.schemaForm.get('tableName')?.value?.trim();
    if (!tableName) {
      return;
    }

    this.isSchemaLoading = true;
    const schema = this.schemaForm.get('schema')?.value || 'processed_data';

    const requestData = {
      query_sql: this.generatedSQL,
      db_schema: schema,
      user_table_name: tableName,
      limit: 100,
      is_database_mode: this.isDatabaseMode,
      connection_config: this.connectionConfig
    };

    this.http.post<any>('http://localhost:8000/api/schema-editor/preview', requestData)
      .subscribe({
        next: (response) => {
          this.isSchemaLoading = false;
          this.schemaPreview = response;
          
          // If schema preview doesn't have create_sql, generate it
          if (!response.create_sql && response.columns) {
            this.updateCreateTableSQL();
          }
          
          console.log('Schema preview generated:', response);
        },
        error: (error) => {
          this.isSchemaLoading = false;
          console.error('Schema preview error:', error);
          this.snackBar.open('Error generating schema preview', 'Close', { duration: 3000 });
        }
      });
  }

  createTableOnly(): void {
    if (!this.canCreateTable()) {
      this.snackBar.open('Please fix validation errors before creating table', 'Close', { duration: 3000 });
      return;
    }

    this.isCreatingTable = true;

    // Prepare column corrections from user edits
    const columnCorrections: { [key: string]: string } = {};
    if (this.schemaPreview?.columns) {
      this.schemaPreview.columns.forEach((col: any) => {
        columnCorrections[col.clean_name] = col.suggested_pg_type;
      });
    }

    const requestData = {
      query_sql: this.generatedSQL,
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
            this.snackBar.open(`Error creating table: ${response.error || 'Unknown error'}`, 'Close', { duration: 5000 });
          }
        },
        error: (error) => {
          this.isCreatingTable = false;
          this.snackBar.dismiss();
          console.error('Table creation error:', error);
          this.snackBar.open('Error creating table', 'Close', { duration: 3000 });
        }
      });
  }

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
      query_sql: this.generatedSQL,
      db_schema: this.schemaForm.get('schema')?.value || 'processed_data',
      user_table_name: this.schemaForm.get('tableName')?.value,
      limit: this.queryForm.get('limit')?.value || null,
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

      const readStream = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            this.isInsertingData = false;
            this.insertionMessage = 'Data insertion completed!';
            this.markStepCompleted(3);
            this.snackBar.open(
              `🎉 Data Warehouse Updated! Table "${this.schemaForm.get('tableName')?.value}" now contains ${this.insertionStats?.totalRows?.toLocaleString()} records from your query.`, 
              'Close', 
              { duration: 6000 }
            );
            
            // Navigate back to main dashboard
            setTimeout(() => {
              this.router.navigate(['/']);
            }, 2000);
            return;
          }

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                this.handleInsertionUpdate(data);
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }

          readStream();
        });
      };

      readStream();
    }).catch(error => {
      this.isInsertingData = false;
      console.error('Data insertion error:', error);
      this.snackBar.open('Error inserting data', 'Close', { duration: 3000 });
    });
  }

  handleInsertionUpdate(data: any): void {
    if (data.type === 'progress') {
      this.insertionProgress = data.percentage;
      this.insertionMessage = data.message;
      this.insertionStats = data.stats;
    } else if (data.type === 'error') {
      this.isInsertingData = false;
      this.snackBar.open(`Error: ${data.message}`, 'Close', { duration: 5000 });
    }
  }

  canCreateTable(): boolean {
    return this.schemaForm.valid && this.schemaPreview?.can_create === true;
  }

  onTableNameChange(): void {
    // Debounce the schema preview generation
    setTimeout(() => {
      this.validateTableName();
      this.generateSchemaPreview();
    }, 500);
  }

  validateTableName(): void {
    const tableName = this.schemaForm.get('tableName')?.value?.trim();
    if (!tableName) {
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
          // Update schema preview with validation info
          this.schemaPreview = { ...this.schemaPreview, ...response };
        }
      },
      error: (error) => {
        this.isValidating = false;
        console.error('Table validation error:', error);
        this.snackBar.open('Error validating table name', 'Close', { duration: 3000 });
      }
    });
  }

  updateColumnType(columnIndex: number, newType: string): void {
    if (this.schemaPreview && this.schemaPreview.columns[columnIndex]) {
      const column = this.schemaPreview.columns[columnIndex];
      column.suggested_pg_type = newType;
      // Regenerate CREATE TABLE SQL with updated types
      this.updateCreateTableSQL();
    }
  }

  updateCreateTableSQL(): void {
    if (!this.schemaPreview || !this.schemaPreview.columns) {
      return;
    }

    const tableName = this.schemaForm.get('tableName')?.value;
    const schema = this.schemaForm.get('schema')?.value || 'processed_data';
    
    // Generate CREATE TABLE SQL based on updated column types
    const columnDefinitions = this.schemaPreview.columns
      .map((col: any) => `  ${col.clean_name} ${col.suggested_pg_type}`)
      .join(',\n');
    
    this.schemaPreview.create_sql = 
      `CREATE TABLE IF NOT EXISTS ${schema}.${tableName} (\n${columnDefinitions}\n);`;
  }

  getTableNameError(): string {
    const control = this.schemaForm.get('tableName');
    if (control?.hasError('required')) {
      return 'Table name is required';
    }
    if (control?.hasError('duplicate')) {
      return control.errors?.['message'] || 'This table name already exists';
    }
    if (control?.hasError('invalid')) {
      return control.errors?.['message'] || 'Invalid table name';
    }
    return '';
  }

  // Step 4: Save to Warehouse methods
  saveToWarehouse(): void {
    // Check if we have query results to work with
    if (!this.generatedSQL || this.queryResults.length === 0) {
      this.snackBar.open('Please execute a query first to save results to warehouse', 'Close', { duration: 3000 });
      return;
    }

    if (this.isDatabaseMode) {
      // For database mode, use schema editor dialog (same as file mode)
      // Prepare data for the schema editor dialog
      const dialogData: SchemaEditorData = {
        sql: this.generatedSQL,
        totalRows: this.totalRows,
        columns: this.queryColumns,
        sampleData: this.queryResults.slice(0, 5),
        isDatabaseMode: true,
        connectionConfig: this.connectionConfig,
        limit: this.queryForm.get('limit')?.value || undefined // Pass limit from form
      };

      // Open the schema editor dialog
      const dialogRef = this.dialog.open(SchemaEditorDialogComponent, {
        width: '90vw',
        maxWidth: '900px',
        maxHeight: '90vh',
        data: dialogData,
        disableClose: true // Prevent accidental closing
      });

      // Handle dialog result
      dialogRef.afterClosed().subscribe((result: any) => {
        if (result?.success) {
          // Table was successfully created and data inserted
          this.snackBar.open(
            `🎉 Data Warehouse Updated! Table "${result.tableName}" now contains ${result.totalRows?.toLocaleString()} records from your query.`, 
            'Close', 
            { duration: 6000 }
          );
          console.log('Table Creation Success:', result.insertionStats);
          this.markStepCompleted(3);
          
          // Navigate back to main dashboard or show success message
          setTimeout(() => {
            this.router.navigate(['/']);
          }, 2000);
        } else if (result) {
          // Dialog was closed with some result but not successful
          console.log('Schema Editor Result:', result);
        }
      });
    } else {
      // For file mode, use schema editor dialog
      // Prepare data for the schema editor dialog
      const dialogData: SchemaEditorData = {
        sql: this.generatedSQL,
        totalRows: this.totalRows,
        columns: this.queryColumns,
        sampleData: this.queryResults.slice(0, 5),
        isDatabaseMode: false,
        limit: this.queryForm.get('limit')?.value || undefined // Pass limit from form
      };

      // Open the schema editor dialog
      const dialogRef = this.dialog.open(SchemaEditorDialogComponent, {
        width: '90vw',
        maxWidth: '900px',
        maxHeight: '90vh',
        data: dialogData,
        disableClose: true // Prevent accidental closing
      });

      // Handle dialog result
      dialogRef.afterClosed().subscribe((result: any) => {
        if (result?.success) {
          // Table was successfully created and data inserted
          this.snackBar.open(
            `🎉 Data Warehouse Updated! Table "${result.tableName}" now contains ${result.totalRows?.toLocaleString()} records from your query.`, 
            'Close', 
            { duration: 6000 }
          );
          console.log('Table Creation Success:', result.insertionStats);
          this.markStepCompleted(3);
          
          // Navigate back to main dashboard or show success message
          setTimeout(() => {
            this.router.navigate(['/']);
          }, 2000);
        } else if (result) {
          // Dialog was closed with some result but not successful
          console.log('Schema Editor Result:', result);
        }
      });
    }
  }
}