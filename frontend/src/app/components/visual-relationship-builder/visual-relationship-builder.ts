import { Component, OnInit, ElementRef, ViewChild, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatChipsModule } from '@angular/material/chips';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import * as d3 from 'd3';

import { FileService } from '../../services/file.service';
import { RelationshipService } from '../../services/relationship.service';

interface TableNode {
  id: string;
  name: string;
  filename: string;
  columns: string[];
  x: number;
  y: number;
  width: number;
  height: number;
  fx?: number;
  fy?: number;
}

interface RelationshipLink {
  id: string;
  source: TableNode;
  target: TableNode;
  sourceColumn: string;
  targetColumn: string;
  type: 'one-to-one' | 'one-to-many' | 'many-to-many';
  strength: number;
}

interface ColumnConnection {
  sourceTable: string;
  sourceColumn: string;
  targetTable: string;
  targetColumn: string;
}

@Component({
  selector: 'app-visual-relationship-builder',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatChipsModule,
    MatTooltipModule,
    MatSnackBarModule
  ],
  templateUrl: './visual-relationship-builder.html',
  styleUrls: ['./visual-relationship-builder.scss']
})
export class VisualRelationshipBuilderComponent implements OnInit, AfterViewInit {
  @ViewChild('svgContainer', { static: false }) svgContainer!: ElementRef;

  // Data properties
  tables: TableNode[] = [];
  relationships: RelationshipLink[] = [];
  filesMetadata: any[] = [];
  
  // D3 properties
  private svg: any;
  private simulation: any;
  private width = 1200;
  private height = 800;
  
  // UI state
  selectedTable: TableNode | null = null;
  selectedColumn: string | null = null;
  isConnecting = false;
  pendingConnection: ColumnConnection | null = null;
  sidenavOpened = true;

  constructor(
    private fileService: FileService,
    private relationshipService: RelationshipService,
    private snackBar: MatSnackBar
  ) {}

  ngOnInit(): void {
    this.loadTablesData();
  }

  ngAfterViewInit(): void {
    setTimeout(() => {
      this.initializeVisualization();
    }, 100);
  }

  private loadTablesData(): void {
    this.fileService.getFilesMetadata().subscribe({
      next: (response) => {
        this.filesMetadata = response.files || [];
        this.createTableNodes();
        console.log('Loaded tables:', this.tables);
      },
      error: (error) => {
        console.error('Error loading files metadata:', error);
        this.snackBar.open('Error loading table data', 'Close', { duration: 3000 });
      }
    });
  }

  private createTableNodes(): void {
    this.tables = this.filesMetadata.map((file, index) => {
      const tableName = file.filename
        .replace(/\.(xlsx|xls|csv)$/i, '')
        .toLowerCase()
        .replace(/[^a-z0-9]/g, '_')
        .replace(/_+/g, '_')
        .replace(/^_|_$/g, '');

      // Calculate table dimensions based on columns
      const columnCount = file.columns ? file.columns.length : 0;
      const width = Math.max(200, Math.min(300, columnCount * 8 + 100));
      const height = Math.max(150, Math.min(400, columnCount * 20 + 80));

      return {
        id: `table_${index}`,
        name: tableName,
        filename: file.filename,
        columns: file.columns || [],
        x: (index % 3) * 350 + 200,
        y: Math.floor(index / 3) * 300 + 150,
        width: width,
        height: height
      };
    });

    // Update visualization if already initialized
    if (this.svg) {
      this.updateVisualization();
    }
  }

  private initializeVisualization(): void {
    // Clear any existing SVG
    d3.select(this.svgContainer.nativeElement).selectAll("*").remove();

    // Create SVG
    this.svg = d3.select(this.svgContainer.nativeElement)
      .append('svg')
      .attr('width', this.width)
      .attr('height', this.height)
      .style('border', '1px solid #ddd')
      .style('background', '#fafafa');

    // Add zoom behavior
    const zoom = d3.zoom()
      .scaleExtent([0.5, 3])
      .on('zoom', (event) => {
        this.svg.select('.main-group').attr('transform', event.transform);
      });

    this.svg.call(zoom);

    // Create main group for all elements
    const mainGroup = this.svg.append('g').attr('class', 'main-group');

    // Create groups for different elements
    mainGroup.append('g').attr('class', 'relationships');
    mainGroup.append('g').attr('class', 'tables');

    // Initialize force simulation
    this.simulation = d3.forceSimulation(this.tables)
      .force('charge', d3.forceManyBody().strength(-1000))
      .force('center', d3.forceCenter(this.width / 2, this.height / 2))
      .force('collision', d3.forceCollide().radius(150))
      .on('tick', () => this.ticked());

    this.updateVisualization();
  }

  private updateVisualization(): void {
    this.drawTables();
    this.drawRelationships();
  }

  private drawTables(): void {
    const tableGroups = this.svg.select('.tables')
      .selectAll('.table-group')
      .data(this.tables, (d: TableNode) => d.id);

    const tableEnter = tableGroups.enter()
      .append('g')
      .attr('class', 'table-group')
      .attr('transform', (d: TableNode) => `translate(${d.x}, ${d.y})`)
      .call(d3.drag<SVGGElement, TableNode>()
        .on('start', (event, d) => this.dragStarted(event, d))
        .on('drag', (event, d) => this.dragged(event, d))
        .on('end', (event, d) => this.dragEnded(event, d))
      );

    // Table container
    const tableContainer = tableEnter.append('g').attr('class', 'table-container');

    // Table background
    tableContainer.append('rect')
      .attr('class', 'table-bg')
      .attr('width', (d: TableNode) => d.width)
      .attr('height', (d: TableNode) => d.height)
      .attr('rx', 8)
      .attr('fill', '#ffffff')
      .attr('stroke', '#2196f3')
      .attr('stroke-width', 2)
      .style('cursor', 'move')
      .style('filter', 'drop-shadow(0px 4px 8px rgba(0,0,0,0.1))');

    // Table header
    tableContainer.append('rect')
      .attr('class', 'table-header')
      .attr('width', (d: TableNode) => d.width)
      .attr('height', 40)
      .attr('rx', 8)
      .attr('fill', '#2196f3');

    // Table header bottom rectangle to square off bottom corners
    tableContainer.append('rect')
      .attr('class', 'table-header-bottom')
      .attr('width', (d: TableNode) => d.width)
      .attr('height', 8)
      .attr('y', 32)
      .attr('fill', '#2196f3');

    // Table title
    tableContainer.append('text')
      .attr('class', 'table-title')
      .attr('x', (d: TableNode) => d.width / 2)
      .attr('y', 25)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-weight', 'bold')
      .attr('font-size', '14px')
      .text((d: TableNode) => d.name);

    // Column count badge
    tableContainer.append('circle')
      .attr('class', 'column-count-bg')
      .attr('cx', (d: TableNode) => d.width - 20)
      .attr('cy', 20)
      .attr('r', 12)
      .attr('fill', '#ff9800');

    tableContainer.append('text')
      .attr('class', 'column-count')
      .attr('x', (d: TableNode) => d.width - 20)
      .attr('y', 25)
      .attr('text-anchor', 'middle')
      .attr('fill', 'white')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .text((d: TableNode) => d.columns.length);

    // Columns list
    const columnsGroup = tableContainer.append('g').attr('class', 'columns-group');

    const self = this;
    tableEnter.each(function(this: SVGGElement, d: TableNode) {
      const columnGroup = d3.select(this).select('.columns-group');
      
      d.columns.slice(0, Math.floor((d.height - 60) / 20)).forEach((column, index) => {
        const columnItem = columnGroup.append('g')
          .attr('class', 'column-item')
          .attr('transform', `translate(10, ${60 + index * 20})`)
          .style('cursor', 'pointer')
          .on('click', () => self.onColumnClick(d, column))
          .on('mouseenter', function(this: SVGGElement) {
            d3.select(this).select('.column-bg').attr('fill', '#e3f2fd');
          })
          .on('mouseleave', function(this: SVGGElement) {
            d3.select(this).select('.column-bg').attr('fill', 'transparent');
          });

        // Column background
        columnItem.append('rect')
          .attr('class', 'column-bg')
          .attr('width', d.width - 20)
          .attr('height', 18)
          .attr('rx', 2)
          .attr('fill', 'transparent');

        // Column icon
        columnItem.append('circle')
          .attr('cx', 8)
          .attr('cy', 9)
          .attr('r', 3)
          .attr('fill', '#4caf50');

        // Column text
        columnItem.append('text')
          .attr('x', 18)
          .attr('y', 13)
          .attr('font-size', '11px')
          .attr('fill', '#333')
          .text(column.length > 25 ? column.substring(0, 22) + '...' : column);
      });

      // Show "..." if there are more columns
      if (d.columns.length > Math.floor((d.height - 60) / 20)) {
        columnGroup.append('text')
          .attr('x', d.width / 2)
          .attr('y', d.height - 10)
          .attr('text-anchor', 'middle')
          .attr('font-size', '10px')
          .attr('fill', '#666')
          .text(`... +${d.columns.length - Math.floor((d.height - 60) / 20)} more`);
      }
          });

    // Update existing tables
    tableGroups.merge(tableEnter)
      .attr('transform', (d: TableNode) => `translate(${d.x}, ${d.y})`);

    // Remove old tables
    tableGroups.exit().remove();
  }

  private drawRelationships(): void {
    const links = this.svg.select('.relationships')
      .selectAll('.relationship-link')
      .data(this.relationships, (d: RelationshipLink) => d.id);

    const linkEnter = links.enter()
      .append('g')
      .attr('class', 'relationship-link');

    // Connection line
    linkEnter.append('line')
      .attr('class', 'connection-line')
      .attr('stroke', '#4caf50')
      .attr('stroke-width', 3)
      .attr('marker-end', 'url(#arrowhead)');

    // Connection label
    linkEnter.append('text')
      .attr('class', 'connection-label')
      .attr('font-size', '10px')
      .attr('fill', '#333')
      .attr('text-anchor', 'middle')
      .text((d: RelationshipLink) => `${d.sourceColumn} → ${d.targetColumn}`);

    // Update positions
    links.merge(linkEnter)
      .select('.connection-line')
      .attr('x1', (d: RelationshipLink) => d.source.x + d.source.width / 2)
      .attr('y1', (d: RelationshipLink) => d.source.y + d.source.height / 2)
      .attr('x2', (d: RelationshipLink) => d.target.x + d.target.width / 2)
      .attr('y2', (d: RelationshipLink) => d.target.y + d.target.height / 2);

    links.merge(linkEnter)
      .select('.connection-label')
      .attr('x', (d: RelationshipLink) => (d.source.x + d.target.x + d.source.width / 2 + d.target.width / 2) / 2)
      .attr('y', (d: RelationshipLink) => (d.source.y + d.target.y + d.source.height / 2 + d.target.height / 2) / 2);

    links.exit().remove();

    // Add arrowhead marker
    this.svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 8)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#4caf50');
  }

  private onColumnClick(table: TableNode, column: string): void {
    if (!this.isConnecting) {
      // Start connection
      this.selectedTable = table;
      this.selectedColumn = column;
      this.isConnecting = true;
      this.pendingConnection = {
        sourceTable: table.id,
        sourceColumn: column,
        targetTable: '',
        targetColumn: ''
      };
      this.snackBar.open(`Select target column to connect with ${column}`, 'Cancel', {
        duration: 5000
      }).onAction().subscribe(() => {
        this.cancelConnection();
      });
    } else if (this.pendingConnection) {
      // Complete connection
      if (table.id !== this.pendingConnection.sourceTable) {
        this.pendingConnection.targetTable = table.id;
        this.pendingConnection.targetColumn = column;
        this.createRelationship();
      } else {
        this.snackBar.open('Cannot connect to the same table', 'OK', { duration: 3000 });
      }
    }
  }

  private createRelationship(): void {
    if (!this.pendingConnection) return;

    const sourceTable = this.tables.find(t => t.id === this.pendingConnection!.sourceTable);
    const targetTable = this.tables.find(t => t.id === this.pendingConnection!.targetTable);

    if (sourceTable && targetTable) {
      const newRelationship: RelationshipLink = {
        id: `rel_${Date.now()}`,
        source: sourceTable,
        target: targetTable,
        sourceColumn: this.pendingConnection.sourceColumn,
        targetColumn: this.pendingConnection.targetColumn,
        type: 'one-to-many',
        strength: 0.8
      };

      this.relationships.push(newRelationship);
      this.updateVisualization();
      
      this.snackBar.open(
        `Created relationship: ${sourceTable.name}.${this.pendingConnection.sourceColumn} → ${targetTable.name}.${this.pendingConnection.targetColumn}`,
        'OK',
        { duration: 4000 }
      );
    }

    this.cancelConnection();
  }

  cancelConnection(): void {
    this.isConnecting = false;
    this.selectedTable = null;
    this.selectedColumn = null;
    this.pendingConnection = null;
  }

  // D3 drag handlers
  private dragStarted(event: any, d: TableNode): void {
    if (!event.active) this.simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  private dragged(event: any, d: TableNode): void {
    d.fx = event.x;
    d.fy = event.y;
    d.x = event.x;
    d.y = event.y;
    this.drawRelationships(); // Update relationship lines
  }

  private dragEnded(event: any, d: TableNode): void {
    if (!event.active) this.simulation.alphaTarget(0);
    d.fx = undefined;
    d.fy = undefined;
  }

  private ticked(): void {
    // Update table positions
    this.svg.selectAll('.table-group')
      .attr('transform', (d: TableNode) => `translate(${d.x}, ${d.y})`);
    
    // Update relationship lines
    this.drawRelationships();
  }

  // Public methods for UI
  clearAllRelationships(): void {
    this.relationships = [];
    this.updateVisualization();
    this.snackBar.open('All relationships cleared', 'OK', { duration: 2000 });
  }

  autoLayout(): void {
    this.simulation.alpha(1).restart();
    this.snackBar.open('Auto-arranging tables...', 'OK', { duration: 2000 });
  }

  exportRelationships(): void {
    const exportData = {
      tables: this.tables.map(t => ({
        id: t.id,
        name: t.name,
        filename: t.filename,
        columns: t.columns
      })),
      relationships: this.relationships.map(r => ({
        id: r.id,
        sourceTable: r.source.id,
        targetTable: r.target.id,
        sourceColumn: r.sourceColumn,
        targetColumn: r.targetColumn,
        type: r.type
      }))
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'relationships.json';
    link.click();
    URL.revokeObjectURL(url);

    this.snackBar.open('Relationships exported', 'OK', { duration: 2000 });
  }

  toggleSidenav(): void {
    this.sidenavOpened = !this.sidenavOpened;
  }

  getTotalColumns(): number {
    return this.tables.reduce((sum, t) => sum + t.columns.length, 0);
  }
}
