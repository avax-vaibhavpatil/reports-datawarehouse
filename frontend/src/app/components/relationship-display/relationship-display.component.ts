import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatTableModule } from '@angular/material/table';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';

import { RelationshipService, Relationship, RelationshipSummary } from '../../services/relationship.service';

@Component({
  selector: 'app-relationship-display',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatTableModule,
    MatButtonModule,
    MatIconModule,
    MatChipsModule,
    MatProgressBarModule,
    MatSnackBarModule
  ],
  templateUrl: './relationship-display.component.html',
  styleUrls: ['./relationship-display.component.scss']
})
export class RelationshipDisplayComponent implements OnInit {
  relationships: Relationship[] = [];
  summary: RelationshipSummary | null = null;

  displayedColumns = [
    'source_table', 'source_column', 'arrow', 'target_table', 'target_column', 
    'strength', 'confidence', 'source', 'actions'
  ];

  constructor(
    private relationshipService: RelationshipService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadExistingRelationships();
  }

  loadExistingRelationships(): void {
    this.relationshipService.getAllRelationships().subscribe({
      next: (response) => {
        // Combine automatic and manual relationships
        this.relationships = [
          ...(response.automatic || []),
          ...(response.manual || [])
        ];
        
        // Calculate summary
        this.calculateSummary();
      },
      error: (error) => {
        console.error('Error loading relationships:', error);
        this.snackBar.open(
          'Error loading relationships. Please try again.',
          'Close',
          { duration: 5000 }
        );
      }
    });
  }

  calculateSummary(): void {
    const total = this.relationships.length;
    const strong = this.relationships.filter(r => r.strength === 'strong').length;
    const medium = this.relationships.filter(r => r.strength === 'medium').length;
    const weak = this.relationships.filter(r => r.strength === 'weak').length;
    const automatic = this.relationships.filter(r => r.source === 'automatic').length;
    const manual = this.relationships.filter(r => r.source === 'manual').length;

    this.summary = {
      total,
      strong,
      medium,
      weak,
      automatic,
      manual
    };
  }

  getStrengthColor(strength: string): string {
    return this.relationshipService.getStrengthColor(strength);
  }

  getStrengthIcon(strength: string): string {
    return this.relationshipService.getStrengthIcon(strength);
  }

  viewRelationshipDetails(relationship: Relationship): void {
    // TODO: Implement relationship details view
    console.log('View relationship details:', relationship);
  }

  editRelationship(relationship: Relationship): void {
    // TODO: Implement relationship editing
    console.log('Edit relationship:', relationship);
  }

  deleteRelationship(relationship: Relationship): void {
    // TODO: Implement relationship deletion
    console.log('Delete relationship:', relationship);
  }
} 