import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ColumnSelection {
  table_name: string;
  selected_columns: string[];
  column_count: number;
}

export interface ColumnMapping {
  from_table: string;
  from_column: string;
  to_table: string;
  to_column: string;
  relationship: string;
  description: string;
  type: string;
}

export interface SelectedColumnsSummary {
  total_tables: number;
  total_columns: number;
  tables: ColumnSelection[];
}

export interface ColumnMappingSummary {
  total_mappings: number;
  mappings: ColumnMapping[];
  summary: string;
}

export interface CombinedTableStructure {
  table_name: string;
  columns: string[];
  source_tables: string[];
  column_count: number;
  mappings: ColumnMapping[];
}

@Injectable({
  providedIn: 'root'
})
export class ColumnMappingService {
  private readonly apiUrl = 'http://localhost:8000/api/column-mapping';

  constructor(private http: HttpClient) {}

  /**
   * Select columns from a specific table
   */
  selectColumns(tableName: string, columns: string[]): Observable<any> {
    const params = { table_name: tableName, columns: columns };
    return this.http.post(`${this.apiUrl}/select-columns`, params);
  }

  /**
   * Deselect columns from a specific table
   */
  deselectColumns(tableName: string, columns: string[]): Observable<any> {
    const params = { table_name: tableName, columns: columns };
    return this.http.post(`${this.apiUrl}/deselect-columns`, params);
  }

  /**
   * Get summary of all selected columns
   */
  getSelectedColumns(): Observable<SelectedColumnsSummary> {
    return this.http.get<SelectedColumnsSummary>(`${this.apiUrl}/selected-columns`);
  }

  /**
   * Get all column mappings/relationships
   */
  getColumnMappings(): Observable<ColumnMappingSummary> {
    return this.http.get<ColumnMappingSummary>(`${this.apiUrl}/column-mappings`);
  }

  /**
   * Get the structure for the new combined table
   */
  getCombinedTableStructure(): Observable<CombinedTableStructure> {
    return this.http.get<CombinedTableStructure>(`${this.apiUrl}/combined-table-structure`);
  }

  /**
   * Clear all column selections and mappings
   */
  clearAllSelections(): Observable<any> {
    return this.http.delete(`${this.apiUrl}/clear-selections`);
  }

  /**
   * Create a composite key relationship between two tables
   */
  createCompositeRelationship(table1: string, table2: string, columnPairs: any[]): Observable<any> {
    const request = {
      table1: table1,
      table2: table2,
      column_pairs: columnPairs
    };
    return this.http.post(`${this.apiUrl}/create-composite-relationship`, request);
  }

  /**
   * Health check for column mapping service
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  /**
   * Format table.column notation for display
   */
  formatColumnNotation(tableName: string, columnName: string): string {
    return `${tableName}.${columnName}`;
  }

  /**
   * Get mapping description for display
   */
  getMappingDescription(mapping: ColumnMapping): string {
    return `${mapping.from_table}.${mapping.from_column} = ${mapping.to_table}.${mapping.to_column}`;
  }

  /**
   * Check if a column is selected in a table
   */
  isColumnSelected(tableName: string, columnName: string, selectedColumns: SelectedColumnsSummary): boolean {
    const table = selectedColumns.tables.find(t => t.table_name === tableName);
    return table ? table.selected_columns.includes(columnName) : false;
  }
} 