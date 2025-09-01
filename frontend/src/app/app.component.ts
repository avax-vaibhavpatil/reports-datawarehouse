import { Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterOutlet],
  template: `
    <div class="app-container">
      <header class="app-header">
        <h1>📊 Data Relationship </h1>
        <p>Upload Excel files and explore their structure</p>
      </header>
      
      <main class="app-main">
        <router-outlet></router-outlet>
      </main>
      
      <footer class="app-footer">
        <p>&copy; 2024 Excel Generator. Built with Angular & FastAPI.</p>
      </footer>
    </div>
  `,
  styles: [`
    .app-container {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .app-header {
      text-align: center;
      padding: 40px 20px;
      color: white;
      background: rgba(255, 255, 255, 0.1);
      backdrop-filter: blur(10px);
    }
    
    .app-header h1 {
      margin: 0 0 16px 0;
      font-size: 3rem;
      font-weight: 300;
      text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    .app-header p {
      margin: 0;
      font-size: 1.2rem;
      opacity: 0.9;
    }
    
    .app-main {
      flex: 1;
      padding: 20px;
    }
    
    .app-footer {
      text-align: center;
      padding: 20px;
      color: white;
      opacity: 0.8;
      background: rgba(0, 0, 0, 0.1);
    }
    
    @media (max-width: 768px) {
      .app-header h1 {
        font-size: 2rem;
      }
      
      .app-header p {
        font-size: 1rem;
      }
    }
  `]
})
export class AppComponent {
  title = 'Excel Generator';
} 