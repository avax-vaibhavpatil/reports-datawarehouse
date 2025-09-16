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
import { SQLQueryService, TableInfo, JoinType, SQLQueryRequest, SQLQueryResponse } from '../../services/sql-query.service';

@Component({
  selector: 'app-sql-query-builder',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatSnackBarModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatCheckboxModule
  ],
  templateUrl: './sql-query-builder.component.html',
  styleUrls: ['./sql-query-builder.component.css']
})
export class SQLQueryBuilderComponent implements OnInit {
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

  constructor(
    private fb: FormBuilder,
    private sqlQueryService: SQLQueryService,
    private snackBar: MatSnackBar
  ) {
    this.queryForm = this.createForm();
  }

  ngOnInit(): void {
    this.loadAvailableTables();
    this.loadJoinTypes();
  }

  createForm(): FormGroup {
    return this.fb.group({
      tables: this.fb.array([]),
      joins: this.fb.array([]),
      where_conditions: this.fb.array([]),
      group_by: this.fb.array([]),
      order_by: this.fb.array([]),
      limit: [null],
      custom_table_name: ['', Validators.required]
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
    this.isLoading = true;
    this.sqlQueryService.getAvailableTables().subscribe({
      next: (response) => {
        this.availableTables = response.tables;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Error loading tables:', error);
        this.snackBar.open('Error loading available tables', 'Close', { duration: 3000 });
        this.isLoading = false;
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

  removeTable(index: number): void {
    this.tablesArray.removeAt(index);
  }

  addJoin(): void {
    const joinForm = this.fb.group({
      type: ['INNER JOIN', Validators.required],
      table: ['', Validators.required],
      alias: [''],
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

  onJoinTableChange(joinIndex: number): void {
    const joinForm = this.joinsArray.at(joinIndex) as FormGroup;
    const selectedTableName = joinForm.get('table')?.value;
    
    if (selectedTableName) {
      const selectedTable = this.availableTables.find(t => t.name === selectedTableName);
      if (selectedTable) {
        // Clear existing columns and add all available columns (unselected by default)
        const columnsArray = joinForm.get('columns') as FormArray;
        columnsArray.clear();
        
        selectedTable.columns.forEach(() => {
          const columnControl = this.fb.control(false); // Start with false (unselected)
          columnsArray.push(columnControl);
        });
        
        // Reset select all checkbox
        joinForm.get('selectAll')?.setValue(false);
      }
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
      this.isLoading = true;
      
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
        limit: formValue.limit || undefined
      };

      this.sqlQueryService.generateSQLQuery(request).subscribe({
        next: (response) => {
          this.queryResponse = response;
          this.generatedSQL = response.sql;
          this.formattedSQL = response.formatted_sql;
          this.isLoading = false;
          this.snackBar.open('SQL query generated successfully!', 'Close', { duration: 3000 });
        },
        error: (error) => {
          console.error('Error generating SQL:', error);
          this.snackBar.open('Error generating SQL query', 'Close', { duration: 3000 });
          this.isLoading = false;
        }
      });
    } else {
      this.snackBar.open('Please fill in all required fields', 'Close', { duration: 3000 });
    }
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

  executeQuery(): void {
    if (this.queryForm.valid) {
      this.isExecuting = true;
      
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

      this.sqlQueryService.executeQuery({ query_config: request, sample_size: 1000 }).subscribe({
        next: (response) => {
          this.queryResults = response.sample_data || [];
          this.queryColumns = response.columns || [];
          this.totalRows = response.total_rows || 0;
          this.executionTime = response.execution_time || '';
          this.isExecuting = false;
          this.showPreview = true;
          this.snackBar.open(`Query executed successfully! Found ${this.totalRows} rows.`, 'Close', { duration: 3000 });
        },
        error: (error) => {
          console.error('Error executing query:', error);
          this.snackBar.open('Error executing query', 'Close', { duration: 3000 });
          this.isExecuting = false;
        }
      });
    } else {
      this.snackBar.open('Please fill in all required fields', 'Close', { duration: 3000 });
    }
  }

  exportToCSV(): void {
    if (this.queryResults.length === 0) {
      this.snackBar.open('No data to export', 'Close', { duration: 2000 });
      return;
    }

    // Get custom table name from form
    const customTableName = this.queryForm.get('custom_table_name')?.value;
    if (!customTableName) {
      this.snackBar.open('Please enter a table name before exporting', 'Close', { duration: 3000 });
      return;
    }

    // Convert data to CSV
    const csvContent = this.convertToCSV(this.queryResults, this.queryColumns);
    
    // Create and download file with custom table name
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${customTableName}_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    window.URL.revokeObjectURL(url);
    
    this.snackBar.open(`Data exported to ${customTableName}.csv successfully!`, 'Close', { duration: 2000 });
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
}