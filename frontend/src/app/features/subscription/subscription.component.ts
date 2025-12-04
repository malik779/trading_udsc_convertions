import { Component } from '@angular/core';
import { FormBuilder } from '@angular/forms';

@Component({
  selector: 'app-subscription',
  templateUrl: './subscription.component.html',
  styleUrls: ['./subscription.component.css'],
})
export class SubscriptionComponent {
  plans = [
    { id: 'starter', price: 199, quota: '250k API calls', chains: 3 },
    { id: 'growth', price: 499, quota: '1M API calls', chains: 5 },
    { id: 'enterprise', price: 1499, quota: 'Unlimited', chains: 'Custom' },
  ];

  form = this.fb.group({ plan: ['starter'], card: [''], expiry: [''], cvc: [''] });

  constructor(private fb: FormBuilder) {}

  checkout(): void {
    alert(`Plan ${this.form.value.plan} submitted`);
  }
}
