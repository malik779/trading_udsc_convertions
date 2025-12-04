import { Component, OnInit } from '@angular/core';
import { ApiService, Transaction } from '../../core/services/api.service';

@Component({
  selector: 'app-logs-table',
  templateUrl: './logs-table.component.html',
  styleUrls: ['./logs-table.component.css'],
})
export class LogsTableComponent implements OnInit {
  logs: Transaction[] = [];
  isLoading = false;

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.fetchLogs();
  }

  fetchLogs(): void {
    this.isLoading = true;
    this.api.getTransactions({}).subscribe((rows) => {
      this.logs = rows;
      this.isLoading = false;
    });
  }
}
