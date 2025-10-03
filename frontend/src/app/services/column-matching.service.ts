import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface ColumnRelationship {
  left_table: string;
  left_column: string;
  operator: string;
  right_table: string;
  right_column: string;
  is_auto_suggested: boolean;
  confidence: number;
  suffix?: string;
}

export interface ColumnMatchingRequest {
  left_table: string;
  right_table: string;
  connection_config?: any;  // For database mode
}

export interface ColumnMatchingResponse {
  success: boolean;
  relationships: ColumnRelationship[];
  total_matches: number;
  left_table: string;
  right_table: string;
  message?: string;
  error?: string;
}

@Injectable({
  providedIn: 'root'
})
export class ColumnMatchingService {
  private apiUrl = 'http://localhost:8000/api/column-matching';

  constructor(private http: HttpClient) { }

  /**
   * Suggest column relationships between two tables
   */
  suggestRelationships(request: ColumnMatchingRequest): Observable<ColumnMatchingResponse> {
    return this.http.post<ColumnMatchingResponse>(`${this.apiUrl}/suggest`, request);
  }

  /**
   * Get suggestions for all possible table combinations
   */
  suggestAllRelationships(): Observable<any> {
    return this.http.get(`${this.apiUrl}/suggest-all`);
  }

  /**
   * Health check for the column matching service
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }
}