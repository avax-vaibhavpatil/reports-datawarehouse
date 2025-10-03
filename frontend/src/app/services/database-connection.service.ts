import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

export interface DatabaseConnection {
  connection_id?: string;
  db_type: string;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  connection_name?: string;
}

export interface TableInfo {
  table_name: string;
  columns: ColumnInfo[];
  foreign_keys: ForeignKeyInfo[];
  row_count: number;
}

export interface ColumnInfo {
  name: string;
  type: string;
  nullable: boolean;
  primary_key: boolean;
}

export interface ForeignKeyInfo {
  column: string;
  referenced_table: string;
  referenced_column: string;
}

export interface QueryResult {
  success: boolean;
  data: any[];
  columns: string[];
  row_count: number;
  query: string;
  message?: string;
  error?: string;
}

export interface SupportedDatabase {
  type: string;
  name: string;
  default_port: number;
  description: string;
}

@Injectable({
  providedIn: 'root'
})
export class DatabaseConnectionService {
  private apiUrl = environment.apiUrl || 'http://localhost:8000';

  constructor(private http: HttpClient) { }

  // Test database connection
  testConnection(connection: DatabaseConnection): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/database-connection/test`, connection);
  }

  // Save database connection
  saveConnection(connection: DatabaseConnection): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/database-connection/save`, connection);
  }

  // Get all saved connections
  getConnections(): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/database-connection/connections`);
  }

  // Get specific connection
  getConnection(connectionId: string): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/database-connection/connections/${connectionId}`);
  }

  // Delete connection
  deleteConnection(connectionId: string): Observable<any> {
    return this.http.delete(`${this.apiUrl}/api/database-connection/connections/${connectionId}`);
  }

  // Discover tables in database
  discoverTables(connection: DatabaseConnection): Observable<any> {
    return this.http.post(`${this.apiUrl}/api/database-connection/discover-tables`, connection);
  }

  // Execute query on database
  executeQuery(connection: DatabaseConnection, query: string, limit: number = 1000): Observable<QueryResult> {
    const request = {
      ...connection,
      query: query,
      limit: limit
    };
    return this.http.post<QueryResult>(`${this.apiUrl}/api/database-connection/execute-query`, request);
  }

  // Get supported database types
  getSupportedDatabases(): Observable<any> {
    return this.http.get(`${this.apiUrl}/api/database-connection/supported-databases`);
  }
}