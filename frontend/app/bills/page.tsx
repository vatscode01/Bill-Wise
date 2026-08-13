"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";
import BillFormModal from "@/components/BillFormModal";
import ConfirmDialog from "@/components/ConfirmDialog";
import { useAuth } from "@/lib/auth-context";
import { api, Bill, BillInput } from "@/lib/api";
import { formatMoney, formatDate, isOverdue } from "@/lib/format";

type FilterValue = "all" | "unpaid" | "paid";

const FILTERS: { value: FilterValue; label: string }[] = [
  { value: "all", label: "All" },
  { value: "unpaid", label: "Unpaid" },
  { value: "paid", label: "Paid" },
];

function StatusBadge({ bill }: { bill: Bill }) {
  const overdue = isOverdue(bill.due_date, bill.status);
  if (overdue) {
    return <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700">Overdue</span>;
  }
  if (bill.status === "paid") {
    return <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700">Paid</span>;
  }
  return <span className="rounded-full bg-amber-100 px-2.5 py-0.5 text-xs font-medium text-amber-700">Unpaid</span>;
}

export default function BillsPage() {
  const { token } = useAuth();
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterValue>("all");

  const [modalOpen, setModalOpen] = useState(false);
  const [editingBill, setEditingBill] = useState<Bill | null>(null);
  const [deletingBill, setDeletingBill] = useState<Bill | null>(null);
  const [deleteBusy, setDeleteBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadBills = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const statusParam = filter === "all" ? undefined : filter;
      const data = await api.listBills(token, statusParam);
      setBills(data);
    } catch {
      setError("Couldn't load your bills. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }, [token, filter]);

  useEffect(() => {
    loadBills();
  }, [loadBills]);

  async function handleSave(payload: BillInput) {
    if (!token) return;
    if (editingBill) {
      const updated = await api.updateBill(token, editingBill.id, payload);
      setBills((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
    } else {
      const created = await api.createBill(token, payload);
      setBills((prev) => [...prev, created].sort((a, b) => a.due_date.localeCompare(b.due_date)));
    }
    setModalOpen(false);
    setEditingBill(null);
  }

  async function handleDelete() {
    if (!token || !deletingBill) return;
    setDeleteBusy(true);
    setActionError(null);
    try {
      await api.deleteBill(token, deletingBill.id);
      setBills((prev) => prev.filter((b) => b.id !== deletingBill.id));
      setDeletingBill(null);
    } catch {
      setActionError("Couldn't delete that bill. Please try again.");
    } finally {
      setDeleteBusy(false);
    }
  }

  async function handleMarkPaid(bill: Bill) {
    if (!token) return;
    setActionError(null);
    try {
      const updated = await api.markPaid(token, bill.id);
      setBills((prev) => prev.map((b) => (b.id === updated.id ? updated : b)));
    } catch {
      setActionError("Couldn't mark that bill as paid. Please try again.");
    }
  }

  return (
    <ProtectedRoute>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-10">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
          <h1 className="text-2xl font-semibold">Bills</h1>
          <div className="flex gap-3">
            <Link
              href="/dashboard/upload"
              className="rounded-md border border-slate-300 bg-white px-4 py-2 text-slate-700 hover:bg-slate-50"
            >
              Upload AI Bill
            </Link>
            <button
              onClick={() => {
                setEditingBill(null);
                setModalOpen(true);
              }}
              className="rounded-md bg-brand-600 px-4 py-2 text-white hover:bg-brand-700"
            >
              + Add bill
            </button>
          </div>
        </div>

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
              onClick={loadBills}
              className="mt-3 rounded-md border border-red-300 px-4 py-1.5 text-red-700 hover:bg-red-100"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && bills.length === 0 && (
          <div className="rounded-lg border border-dashed border-slate-300 bg-white p-10 text-center">
            <p className="text-slate-600">
              {filter === "all" ? "You haven't added any bills yet." : `No ${filter} bills right now.`}
            </p>
            {filter === "all" && (
              <button
                onClick={() => setModalOpen(true)}
                className="mt-4 rounded-md bg-brand-600 px-4 py-2 text-white hover:bg-brand-700"
              >
                Add your first bill
              </button>
            )}
          </div>
        )}

        {!loading && !error && bills.length > 0 && (
          <div className="overflow-hidden rounded-lg border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500">
                <tr>
                  <th className="px-4 py-3 font-medium">Provider</th>
                  <th className="px-4 py-3 font-medium">Amount</th>
                  <th className="px-4 py-3 font-medium">Due date</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {bills.map((bill) => (
                  <tr key={bill.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{bill.provider}</td>
                    <td className="px-4 py-3">{formatMoney(bill.amount, bill.currency)}</td>
                    <td className="px-4 py-3">{formatDate(bill.due_date)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge bill={bill} />
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-3 text-slate-500">
                        {bill.status !== "paid" && (
                          <button
                            onClick={() => handleMarkPaid(bill)}
                            className="hover:text-green-700"
                          >
                            Mark paid
                          </button>
                        )}
                        <button
                          onClick={() => {
                            setEditingBill(bill);
                            setModalOpen(true);
                          }}
                          className="hover:text-brand-700"
                        >
                          Edit
                        </button>
                        <button onClick={() => setDeletingBill(bill)} className="hover:text-red-700">
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
        <BillFormModal
          initial={editingBill}
          onSave={handleSave}
          onClose={() => {
            setModalOpen(false);
            setEditingBill(null);
          }}
        />
      )}

      {deletingBill && (
        <ConfirmDialog
          title="Delete this bill?"
          message={`This will permanently remove "${deletingBill.provider}" from your bills. This can't be undone.`}
          busy={deleteBusy}
          onConfirm={handleDelete}
          onCancel={() => setDeletingBill(null)}
        />
      )}
    </ProtectedRoute>
  );
}
