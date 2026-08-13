"use client";

import { useState } from "react";
import { Subscription, SubscriptionInput } from "@/lib/api";

interface Props {
  initial?: Subscription | null;
  onSave: (payload: SubscriptionInput) => Promise<void>;
  onClose: () => void;
}

const CURRENCIES = ["INR", "USD", "EUR", "GBP"];
const CYCLES: { value: SubscriptionInput["billing_cycle"]; label: string }[] = [
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];

export default function SubscriptionFormModal({ initial, onSave, onClose }: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [provider, setProvider] = useState(initial?.provider ?? "");
  const [amount, setAmount] = useState(initial?.amount ?? "");
  const [currency, setCurrency] = useState(initial?.currency ?? "INR");
  const [billingCycle, setBillingCycle] = useState<SubscriptionInput["billing_cycle"]>(
    initial?.billing_cycle ?? "monthly"
  );
  const [nextRenewal, setNextRenewal] = useState(initial?.next_renewal ?? "");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function validate(): boolean {
    const next: Record<string, string> = {};
    if (!name.trim()) next.name = "Name is required.";
    if (!provider.trim()) next.provider = "Provider is required.";
    const amountNum = Number(amount);
    if (!amount || Number.isNaN(amountNum) || amountNum <= 0) {
      next.amount = "Enter an amount greater than 0.";
    }
    if (!nextRenewal) next.next_renewal = "Next renewal date is required.";
    setErrors(next);
    return Object.keys(next).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);
    if (!validate()) return;

    setSubmitting(true);
    try {
      await onSave({
        name: name.trim(),
        provider: provider.trim(),
        amount,
        currency,
        billing_cycle: billingCycle,
        next_renewal: nextRenewal,
      });
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not save the subscription.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">{initial ? "Edit subscription" : "Add subscription"}</h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Name</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Netflix"
              className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            />
            {errors.name && <p className="mt-1 text-xs text-red-600">{errors.name}</p>}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Provider</label>
            <input
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              placeholder="e.g. Netflix Inc."
              className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            />
            {errors.provider && <p className="mt-1 text-xs text-red-600">{errors.provider}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Amount</label>
              <input
                inputMode="decimal"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
              />
              {errors.amount && <p className="mt-1 text-xs text-red-600">{errors.amount}</p>}
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Currency</label>
              <select
                value={currency}
                onChange={(e) => setCurrency(e.target.value)}
                className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
              >
                {CURRENCIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Billing cycle</label>
            <select
              value={billingCycle}
              onChange={(e) => setBillingCycle(e.target.value as SubscriptionInput["billing_cycle"])}
              className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            >
              {CYCLES.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Next renewal</label>
            <input
              type="date"
              value={nextRenewal}
              onChange={(e) => setNextRenewal(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            />
            {errors.next_renewal && <p className="mt-1 text-xs text-red-600">{errors.next_renewal}</p>}
          </div>

          {formError && (
            <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
              {formError}
            </p>
          )}

          <div className="mt-2 flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="rounded-md border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-100"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-brand-600 px-4 py-2 text-white hover:bg-brand-700 disabled:opacity-60"
            >
              {submitting ? "Saving..." : "Save subscription"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
