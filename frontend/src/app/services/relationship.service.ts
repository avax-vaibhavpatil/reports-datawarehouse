import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Relationship {
  id: string;
  source_table: string;
  source_column: string;
  target_table: string;
  target_column: string;
  relationship_type: string;
  strength: 'strong' | 'medium' | 'weak';
  confidence: number;
  description: string;
  source: 'automatic' | 'manual';
  created_at: string;
  notes?: string;
}

export interface RelationshipSummary {
  total: number;
  strong: number;
  medium: number;
  weak: number;
  automatic: number;
  manual: number;
}



export interface RelationshipSummaryResponse {
  files_count: number;
  summary: RelationshipSummary;
}

@Injectable({
  providedIn: 'root'
})
export class RelationshipService {
  private readonly apiUrl = 'http://localhost:8000/api/relationships';

  constructor(private http: HttpClient) {}



  /**
   * Get all relationships (automatic and manual)
   */
  getAllRelationships(): Observable<any> {
    return this.http.get(`${this.apiUrl}/all`);
  }

  /**
   * Get a summary of detected relationships
   */
  getRelationshipsSummary(): Observable<RelationshipSummaryResponse> {
    return this.http.get<RelationshipSummaryResponse>(`${this.apiUrl}/summary`);
  }

  /**
   * Health check for relationship service
   */
  healthCheck(): Observable<any> {
    return this.http.get(`${this.apiUrl}/health`);
  }

  /**
   * Get strength color for UI display
   */
  getStrengthColor(strength: string): string {
    switch (strength) {
      case 'strong':
        return '#4caf50'; // Green
      case 'medium':
        return '#ff9800'; // Orange
      case 'weak':
        return '#f44336'; // Red
      default:
        return '#9e9e9e'; // Gray
    }
  }

  /**
   * Get strength icon for UI display
   */
  getStrengthIcon(strength: string): string {
    switch (strength) {
      case 'strong':
        return '🔗'; // Link
      case 'medium':
        return '⚠️'; // Warning
      case 'weak':
        return '❌'; // Cross
      default:
        return '❓'; // Question
    }
  }

  /**
   * Format relationship description for display
   */
  formatRelationshipDescription(relationship: Relationship): string {
    return relationship.description || 'No description available';
  }
} 