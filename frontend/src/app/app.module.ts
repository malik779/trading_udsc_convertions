import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { HttpClientModule, HTTP_INTERCEPTORS } from '@angular/common/http';
import { RouterModule, Routes } from '@angular/router';
import { ReactiveFormsModule } from '@angular/forms';

import { AppComponent } from './app.component';
import { DashboardComponent } from './features/dashboard/dashboard.component';
import { LogsTableComponent } from './features/logs/logs-table.component';
import { SubscriptionComponent } from './features/subscription/subscription.component';
import { AuthInterceptor } from './core/services/auth.interceptor';

const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'logs', component: LogsTableComponent },
  { path: 'subscription', component: SubscriptionComponent },
];

@NgModule({
  declarations: [
    AppComponent,
    DashboardComponent,
    LogsTableComponent,
    SubscriptionComponent,
  ],
  imports: [BrowserModule, HttpClientModule, ReactiveFormsModule, RouterModule.forRoot(routes)],
  providers: [{ provide: HTTP_INTERCEPTORS, useClass: AuthInterceptor, multi: true }],
  bootstrap: [AppComponent],
})
export class AppModule {}
