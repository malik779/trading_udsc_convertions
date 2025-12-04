import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface Transaction {
  id: number;
  type: 'deposit' | 'withdrawal';
  network: 'ethereum' | 'bnb' | 'solana';
  amount_usdc: string;
  status: string;
  tx_hash?: string;
  created_at: string;
  user_reference?: string;
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly baseUrl = '/api/v1';

  constructor(private http: HttpClient) {}

  getOverview(): Observable<{ points: number; activeWallets: number; webhooks: number }> {
    return this.http.get<{ points: number; activeWallets: number; webhooks: number }>(`${this.baseUrl}/metrics`);
  }

  getTransactions(filters: Record<string, string | number | undefined>): Observable<Transaction[]> {
    let params = new HttpParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        params = params.set(key, value);
      }
    });
    return this.http.get<Transaction[]>(`${this.baseUrl}/transactions`, { params });
  }

  createWithdrawal(payload: {
    user_reference: string;
    network: string;
    destination_address: string;
    amount_usdc: number;
    idempotency_key?: string;
  }): Observable<Transaction> {
    return this.http.post<Transaction>(`${this.baseUrl}/transactions/withdrawals`, payload);
  }

  getUsage(): Observable<{ day: string; hits: number; successes: number; failures: number }[]> {
    return this.http.get<{ day: string; hits: number; successes: number; failures: number }[]>(`${this.baseUrl}/metrics/usage`);
  }
}
