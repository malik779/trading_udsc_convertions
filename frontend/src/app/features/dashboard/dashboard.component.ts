import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';
import { Subscription } from 'rxjs';

import { ApiService, Transaction } from '../../core/services/api.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css'],
})
export class DashboardComponent implements OnInit, OnDestroy {
  stats = { points: 0, activeWallets: 0, webhooks: 0 };
  transactions: Transaction[] = [];
  filters = this.fb.group({ network: [''], type: [''], status: [''] });

  private sub = new Subscription();

  constructor(private api: ApiService, private fb: FormBuilder) {}

  ngOnInit(): void {
    this.loadData();
    this.sub.add(
      this.filters.valueChanges.subscribe(() => {
        this.loadTransactions();
      })
    );
  }

  ngOnDestroy(): void {
    this.sub.unsubscribe();
  }

  refresh(): void {
    this.loadData();
  }

  private loadData(): void {
    this.api.getOverview().subscribe((stats) => (this.stats = stats));
    this.loadTransactions();
  }

  private loadTransactions(): void {
    this.api
      .getTransactions({
        network: this.filters.value.network || undefined,
        type: this.filters.value.type || undefined,
        status: this.filters.value.status || undefined,
      })
      .subscribe((rows) => (this.transactions = rows));
  }
}
