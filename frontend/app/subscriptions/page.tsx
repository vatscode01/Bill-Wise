"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";
import SubscriptionFormModal from "@/components/SubscriptionFormModal";
import ConfirmDialog from "@/components/ConfirmDialog";
import { useAuth } from "@/lib/auth-context";
import { api, Subscription, SubscriptionInput } from "@/lib/api";
import { formatMoney, formatDate } from "@/lib/format";

type FilterValue = "all" | "active" | "cancelled";

const FILTERS: { value: FilterValue; label: string }[] = [
  { value: "all", label: "All" },
  { value: "active", label: "Active" },
  { value: "cancelled", label: "Cancelled" },
];

function StatusBadge({ status }: { status: Subscription["status"] }) {
  if (status === "cancelled") {
    return <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">Cancelled</span>;
  }
  return <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">Active</span>;
}

export default function SubscriptionsPage() {
  const { token } = useAuth();
  const [subs, setSubs] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterValue>("all");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingSub, setEditingSub] = useState<Subscription | null>(null);
  const [deletingSub, setDeletingSub] = useState<Subscription | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadSubs = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const statusParam = filter === "all" ? undefined : filter;
      const data = await api.listSubscriptions(token, statusParam);
      setSubs(data);
    } catch {
      setError("Couldn't load your subscriptions. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }, [token, filter]);

  useEffect(() => {
    loadSubs();
  }, [loadSubs]);

  // Day 28: recurring monthly spend, normalizing yearly subscriptions down to a monthly figure.
  const { monthlyTotal, currency } = useMemo(() => {
    const active = subs.filter((s) => s.status === "active");
    const total = active.reduce((sum, s) => {
      const amount = Number(s.amount);
      return sum + (s.billing_cycle === "monthly" ? amount : amount / 12);
    }, 0);
    return { monthlyTotal: total, currency: active[0]?.currency ?? "INR" };
  }, [subs]);

  async function handleSave(payload: SubscriptionInput) {
    if (!token) return;
    if (editingSub) {
      const updated = await api.updateSubscription(token, editingSub.id, payload);
      setSubs((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } else {
      const created = await api.createSubscription(token, payload);
      setSubs((prev) => [...prev, created].sort((a, b) => a.next_renewal.localeCompare(b.next_renewal)));
    }
    setModalOpen(false);
    setEditingSub(null);
  }

  async function handleDelete() {
    if (!token || !deletingSub) return;
    setDeleteBusy(true);
    setActionError(null);
    try {
      await api.deleteSubscription(token, deletingSub.id);
      setSubs((prev) => prev.filter((s) => s.id !== deletingSub.id));
      setDeletingSub(null);
    } catch {
      setActionError("Couldn't delete that subscription. Please try again.");
    } finally {
      setDeleteBusy(false);
    }
  }

  async function handleToggleStatus(sub: Subscription) {
    if (!token) return;
    setActionError(null);
    const nextStatus = sub.status === "active" ? "cancelled" : "active";
    try {
      const updated = await api.updateSubscription(token, sub.id, { status: nextStatus });
      setSubs((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    } catch {
      setActionError("Couldn't update that subscription. Please try again.");
    }
  }

  return (
    <ProtectedRoute>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold">Subscriptions</h1>
          <button
            onClick={() => {
              setEditingSub(null);
              setModalOpen(true);
            }}
            className="rounded-md bg-brand-600 px-4 py-2 text-white hover:bg-brand-700"
          >
            + Add subscription
          </button>
        </div>

        {!loading && !error && subs.some((s) => s.status === "active") && (
          <p className="mb-6 rounded-lg border border-slate-200 bg-white px-4 py-3 text-slate-700">
            You spend approximately{" "}
            <span className="font-semibold text-slate-900">{formatMoney(monthlyTotal, currency)}/month</span> on
            recurring subscriptions.
          </p>
        )}

        <div className="mb-4 flex gap-2">
          {FILTERS.map((f) => (
            <button
              key={f.value}
              onClick={() => setFilter(f.value)}
              className={`rounded-full px-3 py-1.5 text-sm font-medium ${
                filter === f.value
                  ? "bg-brand-600 text-white"
                  : "bg-white text-slate-600 border border-slate-300 hover:bg-slate-100"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {actionError && (
          <p className="mb-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
            {actionError}
          </p>
        )}

        {loading && (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 animate-pulse rounded-lg bg-slate-200" />
            ))}
          </div>
        )}

        {!loading && error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadSubs}
              className="mt-3 rounded-md border border-red-300 px-4 py-1.5 text-red-700 hover:bg-red-100"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && subs.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="text-slate-600">
              {filter === "all" ? "You haven't added any subscriptions yet." : `No ${filter} subscriptions right now.`}
            </p>
            {filter === "all" && (
              <button
                onClick={() => setModalOpen(true)}
                className="mt-4 rounded-md bg-brand-600 px-4 py-2 text-white hover:bg-brand-700"
              >
                Add your first subscription
              </button>
            )}
          </div>
        )}

        {!loading && !error && subs.length > 0 && (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Name</th>
                  <th className="px-4 py-3 font-medium">Amount</th>
                  <th className="px-4 py-3 font-medium">Cycle</th>
                  <th className="px-4 py-3 font-medium">Next renewal</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {subs.map((sub) => (
                  <tr key={sub.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{sub.name}</td>
                    <td className="px-4 py-3">
                      {formatMoney(sub.amount, sub.currency)} / {sub.billing_cycle === "monthly" ? "mo" : "yr"}
                    </td>
                    <td className="px-4 py-3 capitalize">{sub.billing_cycle}</td>
                    <td className="px-4 py-3">{formatDate(sub.next_renewal)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={sub.status} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-3 text-slate-500">
                        <button onClick={() => handleToggleStatus(sub)} className="hover:text-brand-700">
                          {sub.status === "active" ? "Cancel" : "Reactivate"}
                        </button>
                        <button
                          onClick={() => {
                            setEditingSub(sub);
                            setModalOpen(true);
                          }}
                          className="hover:text-brand-700"
                        >
                          Edit
                        </button>
                        <button onClick={() => setDeletingSub(sub)} className="hover:text-red-700">
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </main>

      {modalOpen && (
        <SubscriptionFormModal
          initial={editingSub}
          onSave={handleSave}
          onClose={() => {
            setModalOpen(false);
            setEditingSub(null);
          }}
        />
      )}

      {deletingSub && (
        <ConfirmDialog
          title="Delete this subscription?"
          message={`This will permanently remove "${deletingSub.name}" from your subscriptions. This can't be undone.`}
          busy={deleteBusy}
          onConfirm={handleDelete}
          onCancel={() => setDeletingSub(null)}
        />
      )}
    </ProtectedRoute>
  );
}
