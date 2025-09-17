# 🎨 Angular Frontend Setup Guide

## Prerequisites

- **Node.js**: Version 18.0.0 or higher
- **npm**: Version 9.0.0 or higher (comes with Node.js)
- **Angular CLI**: Version 20.0.0 or higher

## Installation Steps

### 1. Check Node.js Version
```bash
node --version
npm --version
```

If Node.js is not installed or version is too low:
- **Ubuntu/Debian**: `sudo apt update && sudo apt install nodejs npm`
- **macOS**: `brew install node`
- **Windows**: Download from [nodejs.org](https://nodejs.org/)

### 2. Install Angular CLI Globally
```bash
npm install -g @angular/cli@20
```

Verify installation:
```bash
ng version
```

### 3. Install Project Dependencies
```bash
cd frontend
npm install
```

### 4. Start Development Server
```bash
npm start
```

The app will be available at: `http://localhost:4200`

## Troubleshooting Common Issues

### Issue 1: "Cannot find module '@angular/core'"
**Solution**: This error appears because dependencies haven't been installed yet.
```bash
cd frontend
npm install
```

### Issue 2: "Angular CLI not found"
**Solution**: Install Angular CLI globally
```bash
npm install -g @angular/cli@20
```

### Issue 3: "Port 4200 is already in use"
**Solution**: Either stop the existing process or use a different port
```bash
# Use different port
ng serve --port 4201

# Or kill process using port 4200
sudo lsof -ti:4200 | xargs kill -9
```

### Issue 4: "TypeScript compilation errors"
**Solution**: Clear cache and reinstall
```bash
rm -rf node_modules package-lock.json
npm install
```

### Issue 5: "Material Design styles not loading"
**Solution**: Ensure Material dependencies are installed
```bash
npm install @angular/material @angular/cdk
```

## Project Structure

```
frontend/
├── src/
│   ├── app/
│   │   ├── components/
│   │   │   └── file-upload/          # Main file upload component
│   │   ├── services/
│   │   │   └── file.service.ts       # API communication service
│   │   ├── app.component.ts          # Root component
│   │   └── app.routes.ts             # Routing configuration
│   ├── assets/                       # Static assets
│   ├── styles.scss                   # Global styles
│   ├── main.ts                       # Application entry point
│   └── index.html                    # Main HTML file
├── package.json                      # Dependencies and scripts
├── angular.json                      # Angular CLI configuration
├── tsconfig.json                     # TypeScript configuration
└── .angular-cli.json                 # Legacy CLI configuration
```

## Available Scripts

- `npm start` - Start development server
- `npm run build` - Build for production
- `npm run watch` - Build with watch mode
- `npm test` - Run unit tests
- `npm run lint` - Run linting

## Development Workflow

1. **Start the backend** (FastAPI server on port 8000)
2. **Start the frontend** (`npm start` on port 4200)
3. **Make changes** to Angular components
4. **Auto-reload** - Changes automatically refresh the browser
5. **Check console** for any errors

## Material Design Components Used

- `MatCardModule` - Card layouts
- `MatButtonModule` - Buttons and icons
- `MatIconModule` - Material icons
- `MatTableModule` - Data tables
- `MatChipsModule` - Column display chips
- `MatProgressBarModule` - Upload progress
- `MatSnackBarModule` - Notifications
- `MatInputModule` - Form inputs
- `MatFormFieldModule` - Form field styling

## API Integration

The frontend communicates with the FastAPI backend at `http://localhost:8000`:

- **File Upload**: `POST /api/files/upload`
- **Metadata**: `GET /api/files/metadata`
- **Health Check**: `GET /api/files/health`

## Browser Compatibility

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance Tips

- Use `OnPush` change detection for large lists
- Implement virtual scrolling for large datasets
- Lazy load components when possible
- Use trackBy functions in ngFor loops

## Testing

```bash
# Run unit tests
npm test

# Run tests with coverage
ng test --code-coverage

# Run e2e tests (if configured)
ng e2e
```

## Production Build

```bash
# Build for production
npm run build

# The built files will be in `dist/excel-generator/`
```

## Deployment

The built files in `dist/excel-generator/` can be deployed to any static hosting service:
- Netlify
- Vercel
- AWS S3
- GitHub Pages
- Firebase Hosting

## Need Help?

If you encounter issues:
1. Check the browser console for errors
2. Verify all dependencies are installed
3. Ensure Node.js version is 18+
4. Check if ports 4200 and 8000 are available
5. Review the backend logs for API errors 