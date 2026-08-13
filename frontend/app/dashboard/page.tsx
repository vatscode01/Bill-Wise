"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/lib/auth-context";
import { api, DashboardStats, DashboardCharts } from "@/lib/api";
import { formatMoney, formatDate, formatMonthLabel } from "@/lib/format";

function StatCardView({
  label,
  amount,
  currency,
  count,
  tone,
}: {
  label: string;
  amount: string;
  currency: string;
  count: number;
  tone: "brand" | "red" | "green" | "slate";
}) {
  const toneClasses: Record<string, string> = {
    brand: "border-brand-100 bg-brand-50",
    red: "border-red-200 bg-red-50",
    green: "border-green-200 bg-green-50",
    slate: "border-slate-200 bg-white",
  };
  return (
    <div className={`rounded-lg border p-5 ${toneClasses[tone]}`}>
      <p className="text-sm font-medium text-slate-600">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-slate-900">{formatMoney(amount, currency)}</p>
      <p className="mt-1 text-xs text-slate-500">
        {count} {count === 1 ? "bill" : "bills"}
      </p>
    </div>
  );
}

function MonthlySpendChart({ data, currency }: { data: DashboardCharts["monthly_spending"]; currency: string }) {
  const max = Math.max(1, ...data.map((d) => Number(d.amount)));
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-medium text-slate-600">Monthly spending</h3>
      <div className="mt-4 flex h-40 items-end gap-3">
        {data.map((point) => {
          const value = Number(point.amount);
          const heightPct = Math.max(2, (value / max) * 100);
          return (
            <div key={point.month} className="flex flex-1 flex-col items-center gap-2">
              <div className="flex h-32 w-full items-end">
                <div
                  className="w-full rounded-t-sm bg-brand-500"
                  style={{ height: `${heightPct}%` }}
                  title={formatMoney(value, currency)}
                />
              </div>
              <span className="text-xs text-slate-500">{formatMonthLabel(point.month)}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ProviderSpendChart({ data, currency }: { data: DashboardCharts["spending_by_provider"]; currency: string }) {
  if (data.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-5">
        <h3 className="text-sm font-medium text-slate-600">Spending by provider</h3>
        <p className="mt-4 text-sm text-slate-500">No paid bills yet — this fills in once you mark bills as paid.</p>
      </div>
    );
  }
  const max = Math.max(...data.map((d) => Number(d.amount)));
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      <h3 className="text-sm font-medium text-slate-600">Spending by provider</h3>
      <div className="mt-4 flex flex-col gap-3">
        {data.map((row) => {
          const value = Number(row.amount);
          const widthPct = Math.max(4, (value / max) * 100);
          return (
            <div key={row.provider}>
              <div className="mb-1 flex justify-between text-xs text-slate-600">
                <span>{row.provider}</span>
                <span>{formatMoney(value, currency)}</span>
              </div>
              <div className="h-2 w-full rounded-full bg-slate-100">
                <div className="h-2 rounded-full bg-brand-500" style={{ width: `${widthPct}%` }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const { user, token } = useAuth();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [charts, setCharts] = useState<DashboardCharts | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    if (!token) return;
    setLoading(true);
    setError(null);
    try {
      const [statsData, chartsData] = await Promise.all([
        api.getDashboardStats(token),
        api.getDashboardCharts(token),
      ]);
      setStats(statsData);
      setCharts(chartsData);
    } catch {
      setError("Couldn't load your dashboard. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  return (
    <ProtectedRoute>
      <Navbar />
      <main className="mx-auto max-w-5xl px-4 py-10">
        <h1 className="text-2xl font-semibold">Welcome back{user ? `, ${user.email}` : ""}</h1>
        <p className="mt-2 text-slate-600">Here's where your bills and subscriptions stand right now.</p>

        {loading && (
          <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-28 animate-pulse rounded-lg bg-slate-200" />
            ))}
          </div>
        )}

        {!loading && error && (
          <div className="mt-8 rounded-lg border border-red-200 bg-red-50 p-6 text-center">
            <p className="text-red-700">{error}</p>
            <button
              onClick={loadDashboard}
              className="mt-3 rounded-md border border-red-300 px-4 py-1.5 text-red-700 hover:bg-red-100"
            >
              Try again
            </button>
          </div>
        )}

        {!loading && !error && stats && charts && (
          <>
            <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <StatCardView
                label="Upcoming Bills"
                amount={stats.upcoming.amount}
                currency={stats.upcoming.currency}
                count={stats.upcoming.count}
                tone="brand"
              />
              <StatCardView
                label="Overdue"
                amount={stats.overdue.amount}
                currency={stats.overdue.currency}
                count={stats.overdue.count}
                tone="red"
              />
              <StatCardView
                label="Paid This Month"
                amount={stats.paid_this_month.amount}
                currency={stats.paid_this_month.currency}
                count={stats.paid_this_month.count}
                tone="green"
              />
              <StatCardView
                label="Recurring"
                amount={stats.recurring_monthly.amount}
                currency={stats.recurring_monthly.currency}
                count={stats.recurring_monthly.count}
                tone="slate"
              />
            </div>

            <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-2">
              <MonthlySpendChart data={charts.monthly_spending} currency={charts.currency} />
              <ProviderSpendChart data={charts.spending_by_provider} currency={charts.currency} />
            </div>

            <div className="mt-8 rounded-lg border border-slate-200 bg-white p-5">
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-sm font-medium text-slate-600">Upcoming Payments</h3>
                <Link href="/bills" className="text-sm text-brand-700 hover:underline">
                  View all bills
                </Link>
              </div>
              {stats.upcoming_payments.length === 0 ? (
                <p className="text-sm text-slate-500">Nothing due soon. You're all caught up.</p>
              ) : (
                <ul className="divide-y divide-slate-100">
                  {stats.upcoming_payments.map((payment) => (
                    <li key={payment.id} className="flex items-center justify-between py-3 text-sm">
                      <span className="font-medium text-slate-900">{payment.provider}</span>
                      <span className="text-slate-500">{formatDate(payment.due_date)}</span>
                      <span className="font-medium text-slate-900">
                        {formatMoney(payment.amount, payment.currency)}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </>
        )}
      </main>
    </ProtectedRoute>
  );
}
