"use client";

import { useState } from "react";
import { Bill, BillInput } from "@/lib/api";

interface Props {
  initial?: Bill | null;
  onSave: (payload: BillInput) => Promise<void>;
  onClose: () => void;
}

const CURRENCIES = ["INR", "USD", "EUR", "GBP"];
const PERIODS: { value: BillInput["billing_period"]; label: string }[] = [
  { value: "one_time", label: "One-time" },
  { value: "monthly", label: "Monthly" },
  { value: "yearly", label: "Yearly" },
];

export default function BillFormModal({ initial, onSave, onClose }: Props) {
  const [provider, setProvider] = useState(initial?.provider ?? "");
  const [amount, setAmount] = useState(initial?.amount ?? "");
  const [currency, setCurrency] = useState(initial?.currency ?? "INR");
  const [dueDate, setDueDate] = useState(initial?.due_date ?? "");
  const [billingPeriod, setBillingPeriod] = useState<BillInput["billing_period"]>(
    initial?.billing_period ?? "one_time"
  );
  const [notes, setNotes] = useState(initial?.notes ?? "");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  function validate(): boolean {
    const next: Record<string, string> = {};
    if (!provider.trim()) next.provider = "Provider is required.";
    const amountNum = Number(amount);
    if (!amount || Number.isNaN(amountNum) || amountNum <= 0) {
      next.amount = "Enter an amount greater than 0.";
    }
    if (!dueDate) next.due_date = "Due date is required.";
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
        provider: provider.trim(),
        amount,
        currency,
        due_date: dueDate,
        billing_period: billingPeriod,
        notes: notes.trim() || undefined,
      });
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Could not save the bill.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="mb-4 text-lg font-semibold">{initial ? "Edit bill" : "Add bill"}</h2>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Provider</label>
            <input
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              placeholder="e.g. Electricity"
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
            <label className="mb-1 block text-sm font-medium text-slate-700">Due date</label>
            <input
              type="date"
              value={dueDate}
              onChange={(e) => setDueDate(e.target.value)}
              className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            />
            {errors.due_date && <p className="mt-1 text-xs text-red-600">{errors.due_date}</p>}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Billing period</label>
            <select
              value={billingPeriod}
              onChange={(e) => setBillingPeriod(e.target.value as BillInput["billing_period"])}
              className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            >
              {PERIODS.map((p) => (
                <option key={p.value} value={p.value}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Notes (optional)</label>
            <textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
              className="w-full rounded-md border border-slate-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
            />
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
              {submitting ? "Saving..." : "Save bill"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
