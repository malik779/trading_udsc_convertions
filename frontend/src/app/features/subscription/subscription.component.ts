import { Component, OnInit } from '@angular/core';
import { FormBuilder } from '@angular/forms';

import { ApiService, Plan } from '../../core/services/api.service';

@Component({
  selector: 'app-subscription',
  templateUrl: './subscription.component.html',
  styleUrls: ['./subscription.component.css'],
})
export class SubscriptionComponent implements OnInit {
  plans: Plan[] = [];
  isSubmitting = false;
  form = this.fb.group({ plan: ['starter'] });

  constructor(private fb: FormBuilder, private api: ApiService) {}

  ngOnInit(): void {
    this.api.getPlans().subscribe((plans) => {
      this.plans = plans;
      if (!this.form.value.plan && plans.length) {
        this.form.patchValue({ plan: plans[0].id });
      }
    });
  }

  checkout(): void {
    if (!this.form.value.plan) {
      return;
    }
    this.isSubmitting = true;
    const origin = window.location.origin;
    this.api
      .createCheckout({
        plan_id: this.form.value.plan,
        success_url: `${origin}/subscription?status=success`,
        cancel_url: `${origin}/subscription?status=cancel`,
      })
      .subscribe({
        next: (res) => {
          window.location.href = res.checkout_url;
        },
        error: () => {
          this.isSubmitting = false;
        },
      });
  }
}
