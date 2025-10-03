import { Component, OnInit } from '@angular/core';
import { CommonModule, DecimalPipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { DatabaseConnectionService, DatabaseConnection, TableInfo, SupportedDatabase } from '../../services/database-connection.service';
import { MatSnackBar } from '@angular/material/snack-bar';

@Component({
  selector: 'app-database-connection',
  templateUrl: './database-connection.component.html',
  styleUrls: ['./database-connection.component.scss'],
  standalone: true,
  imports: [CommonModule, FormsModule]
})
export class DatabaseConnectionComponent implements OnInit {
  // Connection form
  connection: DatabaseConnection = {
    db_type: 'postgresql',
    host: 'localhost',
    port: 5432,
    database: '',
    username: '',
    password: '',
    connection_name: ''
  };

  // UI state
  isConnecting = false;
  isTesting = false;
  connectionTested = false;
  connectionSuccess = false;
  testMessage = '';

  // Data
  supportedDatabases: SupportedDatabase[] = [];
  savedConnections: any[] = [];
  discoveredTables: TableInfo[] = [];
  selectedTables: string[] = [];

  // Steps
  currentStep = 1; // 1: Connection, 2: Tables, 3: Query Builder

  constructor(
    private dbConnectionService: DatabaseConnectionService,
    private snackBar: MatSnackBar,
    private router: Router
  ) { }

  ngOnInit(): void {
    this.loadSupportedDatabases();
    this.loadSavedConnections();
  }

  loadSupportedDatabases(): void {
    this.dbConnectionService.getSupportedDatabases().subscribe({
      next: (response) => {
        if (response.success) {
          this.supportedDatabases = response.databases;
        }
      },
      error: (error) => {
        console.error('Error loading supported databases:', error);
        this.showError('Failed to load supported databases');
      }
    });
  }

  loadSavedConnections(): void {
    this.dbConnectionService.getConnections().subscribe({
      next: (response) => {
        if (response.success) {
          this.savedConnections = response.connections;
        }
      },
      error: (error) => {
        console.error('Error loading saved connections:', error);
      }
    });
  }

  onDatabaseTypeChange(): void {
    const selectedDb = this.supportedDatabases.find(db => db.type === this.connection.db_type);
    if (selectedDb) {
      this.connection.port = selectedDb.default_port;
    }
  }

  testConnection(): void {
    if (!this.validateConnectionForm()) {
      return;
    }

    this.isTesting = true;
    this.testMessage = '';

    this.dbConnectionService.testConnection(this.connection).subscribe({
      next: (response) => {
        this.isTesting = false;
        this.connectionTested = true;
        this.connectionSuccess = response.success;
        this.testMessage = response.message;

        if (response.success) {
          this.showSuccess('Connection test successful!');
        } else {
          this.showError(`Connection test failed: ${response.message}`);
        }
      },
      error: (error) => {
        this.isTesting = false;
        this.connectionTested = true;
        this.connectionSuccess = false;
        this.testMessage = 'Connection test failed';
        this.showError('Connection test failed');
        console.error('Connection test error:', error);
      }
    });
  }

  saveConnection(): void {
    if (!this.validateConnectionForm()) {
      return;
    }

    if (!this.connectionTested || !this.connectionSuccess) {
      this.showError('Please test the connection first');
      return;
    }

    this.isConnecting = true;

    this.dbConnectionService.saveConnection(this.connection).subscribe({
      next: (response) => {
        this.isConnecting = false;
        if (response.success) {
          this.showSuccess('Connection saved successfully!');
          this.loadSavedConnections();
          this.nextStep();
        } else {
          this.showError(`Failed to save connection: ${response.message}`);
        }
      },
      error: (error) => {
        this.isConnecting = false;
        this.showError('Failed to save connection');
        console.error('Save connection error:', error);
      }
    });
  }

  loadSavedConnection(connection: any): void {
    this.connection = {
      connection_id: connection.connection_id,
      db_type: connection.db_type,
      host: connection.host,
      port: connection.port,
      database: connection.database,
      username: connection.username,
      password: '', // Don't load password
      connection_name: connection.connection_name
    };
    this.connectionTested = false;
    this.connectionSuccess = false;
    this.testMessage = '';
  }

  discoverTables(): void {
    if (!this.validateConnectionForm()) {
      return;
    }

    this.isConnecting = true;

    this.dbConnectionService.discoverTables(this.connection).subscribe({
      next: (response) => {
        this.isConnecting = false;
        if (response.success) {
          this.discoveredTables = response.tables;
          this.showSuccess(`Found ${response.total_tables} tables`);
          this.nextStep();
        } else {
          this.showError(`Failed to discover tables: ${response.message}`);
        }
      },
      error: (error) => {
        this.isConnecting = false;
        this.showError('Failed to discover tables');
        console.error('Discover tables error:', error);
      }
    });
  }

  toggleTableSelection(tableName: string): void {
    const index = this.selectedTables.indexOf(tableName);
    if (index > -1) {
      this.selectedTables.splice(index, 1);
    } else {
      this.selectedTables.push(tableName);
    }
  }

  isTableSelected(tableName: string): boolean {
    return this.selectedTables.includes(tableName);
  }

  proceedToQueryBuilder(): void {
    if (this.selectedTables.length === 0) {
      this.showError('Please select at least one table');
      return;
    }
    
    // Navigate to SQL Query Builder with database connection parameters
    const queryParams = {
      dbMode: 'true',
      connectionConfig: JSON.stringify(this.connection),
      selectedTables: JSON.stringify(this.selectedTables)
    };
    
    this.router.navigate(['/sql-query-builder'], { queryParams });
  }

  nextStep(): void {
    this.currentStep++;
  }

  previousStep(): void {
    this.currentStep--;
  }

  resetForm(): void {
    this.connection = {
      db_type: 'postgresql',
      host: 'localhost',
      port: 5432,
      database: '',
      username: '',
      password: '',
      connection_name: ''
    };
    this.connectionTested = false;
    this.connectionSuccess = false;
    this.testMessage = '';
    this.discoveredTables = [];
    this.selectedTables = [];
    this.currentStep = 1;
  }

  private validateConnectionForm(): boolean {
    if (!this.connection.host || !this.connection.database || !this.connection.username) {
      this.showError('Please fill in all required fields');
      return false;
    }
    return true;
  }

  private showSuccess(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 3000,
      panelClass: ['success-snackbar']
    });
  }

  private showError(message: string): void {
    this.snackBar.open(message, 'Close', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  getSelectedTablesInfo(): TableInfo[] {
    return this.discoveredTables.filter(table => this.selectedTables.includes(table.table_name));
  }
}