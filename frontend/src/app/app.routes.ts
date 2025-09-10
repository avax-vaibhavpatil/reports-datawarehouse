import { Routes } from '@angular/router';
import { FileUploadComponent } from './components/file-upload/file-upload.component';
import { RelationshipDisplayComponent } from './components/relationship-display/relationship-display.component';
import { ColumnSelectionComponent } from './components/column-selection/column-selection.component';
import { VisualRelationshipBuilderComponent } from './components/visual-relationship-builder/visual-relationship-builder';

export const routes: Routes = [
  { path: '', component: FileUploadComponent },
  { path: 'relationships', component: RelationshipDisplayComponent },
  { path: 'column-selection', component: ColumnSelectionComponent },
  { path: 'visual-builder', component: VisualRelationshipBuilderComponent },
  { path: '**', redirectTo: '' }
]; 