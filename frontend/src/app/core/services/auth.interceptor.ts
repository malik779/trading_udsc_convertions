import { Injectable } from '@angular/core';
import { HttpEvent, HttpHandler, HttpInterceptor, HttpRequest } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  intercept(req: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const apiKey = localStorage.getItem('tenantApiKey');
    const headers = apiKey ? req.headers.set('X-API-Key', apiKey) : req.headers;
    return next.handle(req.clone({ headers }));
  }
}
