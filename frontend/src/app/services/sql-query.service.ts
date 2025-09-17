import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface TableConfig {
  name: string;
  alias?: string;
  columns: string[];
  custom_expressions?: string[];
}

export interface JoinCondition {
  left_table: string;
  left_column: string;
  operator: string;
  right_table: string;
  right_column: string;
}

export interface JoinConfig {
  type: string;
  table: string;
  alias?: string;
  conditions: JoinCondition[];
}

export interface WhereCondition {
  left_side: string;
  operator: string;
  right_side: string;
  logical_operator: string;
}

export interface OrderByConfig {
  column: string;
  direction: string;
}

export interface SQLQueryRequest {
  tables: TableConfig[];
  joins?: JoinConfig[];
  where_conditions?: WhereCondition[];
  group_by?: string[];
  order_by?: OrderByConfig[];
  limit?: number;
}

export interface SQLQueryResponse {
  sql: string;
  formatted_sql: string;
  query_config: any;
  generated_at: string;
  join_count: number;
  table_count: number;
}

export interface QueryPreviewRequest {
  query_config: any;
  sample_size: number;
}

export interface QueryPreviewResponse {
  success: boolean;
  sample_data: any[];
  total_rows: number;
  columns: string[];
  execution_time: string;
  error?: string;
}

export interface TableInfo {
  name: string;
  filename: string;
  columns: string[];
  row_count: number;
  file_type: string;
}

export interface JoinType {
  type: string;
  description: string;
  example: string;
}

@Injectable({
  providedIn: 'root'
})
export class SQLQueryService {
  private readonly apiUrl = 'http://localhost:8000/api/sql-query';

  constructor(private http: HttpClient) { }

  /**
   * Get available tables from uploaded files
   */
  getAvailableTables(): Observable<{tables: TableInfo[], count: number}> {
    return this.http.get<{tables: TableInfo[], count: number}>(`${this.apiUrl}/tables`);
  }

  /**
   * Get supported JOIN types
   */
  getSupportedJoinTypes(): Observable<{join_types: JoinType[]}> {
    return this.http.get<{join_types: JoinType[]}>(`${this.apiUrl}/join-types`);
  }

  /**
   * Generate SQL query
   */
  generateSQLQuery(request: SQLQueryRequest): Observable<SQLQueryResponse> {
    return this.http.post<SQLQueryResponse>(`${this.apiUrl}/generate`, request);
  }

  /**
   * Validate query configuration
   */
  validateQueryConfig(request: SQLQueryRequest): Observable<{valid: boolean, errors: string[], warnings: string[]}> {
    return this.http.post<{valid: boolean, errors: string[], warnings: string[]}>(`${this.apiUrl}/validate`, request);
  }

  /**
   * Preview query results
   */
  previewQuery(request: QueryPreviewRequest): Observable<QueryPreviewResponse> {
    return this.http.post<QueryPreviewResponse>(`${this.apiUrl}/preview`, request);
  }

  /**
   * Execute query and return full results
   */
  executeQuery(request: QueryPreviewRequest): Observable<QueryPreviewResponse> {
    return this.http.post<QueryPreviewResponse>(`${this.apiUrl}/execute`, request);
  }

  /**
   * Get example queries
   */
  getQueryExamples(): Observable<{examples: any[]}> {
    return this.http.get<{examples: any[]}>(`${this.apiUrl}/examples`);
  }

  /**
   * Save query results as a new table
   */
  saveAsTable(request: SaveTableRequest): Observable<SaveTableResponse> {
    return this.http.post<SaveTableResponse>(`${this.apiUrl}/save-table`, request);
  }
}

// Save Table interfaces
export interface SaveTableRequest {
  table_name: string;
  data: any[];
  columns: string[];
  sql_query: string;
}

export interface SaveTableResponse {
  success: boolean;
  table_name: string;
  rows_inserted: number;
  message: string;