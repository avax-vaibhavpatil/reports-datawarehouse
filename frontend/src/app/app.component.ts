import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, MatToolbarModule, MatButtonModule, MatIconModule],
  template: `
    <div class="app-container">
      <mat-toolbar color="primary" class="main-toolbar">
        <span class="toolbar-title">
          <mat-icon style="margin-right: 8px;">analytics</mat-icon>
          Excel Relationship Manager
        </span>
        
        <span class="toolbar-spacer"></span>
        
        <nav class="toolbar-nav">
          <button mat-button routerLink="/" routerLinkActive="active-nav" [routerLinkActiveOptions]="{exact: true}">
            <mat-icon>cloud_upload</mat-icon>
            Upload
          </button>
          <button mat-button routerLink="/column-selection" routerLinkActive="active-nav">
            <mat-icon>view_column</mat-icon>
            Column Selection
          </button>
          <button mat-button routerLink="/relationships" routerLinkActive="active-nav">
            <mat-icon>link</mat-icon>
            Relationships
          </button>
          <button mat-button routerLink="/visual-builder" routerLinkActive="active-nav">
            <mat-icon>account_tree</mat-icon>
            Visual Builder
          </button>
        </nav>
      </mat-toolbar>
      
      <main class="app-main">
        <router-outlet></router-outlet>
      </main>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background: #f5f5f5;
    }
    
    .main-toolbar {
      position: sticky;
      top: 0;
      z-index: 1000;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .toolbar-title {
      display: flex;
      align-items: center;
      font-size: 18px;
      font-weight: 500;
    }
    
    .toolbar-spacer {
      flex: 1 1 auto;
    }
    
    .toolbar-nav {
      display: flex;
      gap: 8px;
      align-items: center;
    }
    
    .toolbar-nav button {
      display: flex;
      align-items: center;
      gap: 6px;
      color: rgba(255,255,255,0.8);
    }
    
    .toolbar-nav button:hover {
      background: rgba(255,255,255,0.1);
    }
    
    .toolbar-nav button.active-nav {
      background: rgba(255,255,255,0.2);
      color: white;
    }
    
    .app-main {
      flex: 1;
      overflow: hidden;
    }
    
    @media (max-width: 768px) {
      .toolbar-title {
        font-size: 16px;
      }
      
      .toolbar-nav {
        gap: 4px;
      }
      
      .toolbar-nav button {
        min-width: auto;
        padding: 0 8px;
      }
      
      .toolbar-nav button span {
        display: none;
      }
    }
  `]
})
export class AppComponent {
  title = 'Excel Generator';
} 