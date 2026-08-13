const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}, token?: string | null): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_URL}${path}`, { ...options, headers });

  if (res.status === 204) {
    return undefined as T;
  }

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const message = data?.detail || "Something went wrong. Please try again.";
    throw new ApiError(typeof message === "string" ? message : "Request failed", res.status);
  }

  return data as T;
}

export interface Bill {
  id: string;
  provider: string;
  amount: string;
  currency: string;
  due_date: string;
  billing_period: "one_time" | "monthly" | "yearly";
  status: "unpaid" | "paid" | "overdue";
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BillInput {
  provider: string;
  amount: string;
  currency: string;
  due_date: string;
  billing_period: "one_time" | "monthly" | "yearly";
  notes?: string;
}

export interface User {
  id: string;
  email: string;
  created_at: string;
}

export interface Subscription {
  id: string;
  name: string;
  provider: string;
  amount: string;
  currency: string;
  billing_cycle: "monthly" | "yearly";
  next_renewal: string;
  status: "active" | "cancelled";
  created_at: string;
  updated_at: string;
}

export interface SubscriptionInput {
  name: string;
  provider: string;
  amount: string;
  currency: string;
  billing_cycle: "monthly" | "yearly";
  next_renewal: string;
}

export interface StatCard {
  amount: string;
  currency: string;
  count: number;
}

export interface UpcomingPayment {
  id: string;
  provider: string;
  amount: string;
  currency: string;
  due_date: string;
  status: string;
}

export interface DashboardStats {
  upcoming: StatCard;
  overdue: StatCard;
  paid_this_month: StatCard;
  recurring_monthly: StatCard;
  upcoming_payments: UpcomingPayment[];
}

export interface MonthlySpendPoint {
  month: string;
  amount: string;
}

export interface ProviderSpend {
  provider: string;
  amount: string;
}

export interface DashboardCharts {
  currency: string;
  monthly_spending: MonthlySpendPoint[];
  spending_by_provider: ProviderSpend[];
}

export interface ExtractedBillData {
  provider: string | null;
  amount: number | null;
  currency: string | null;
  due_date: string | null;
  billing_period: string | null;
}

export const api = {
  register: (email: string, password: string) =>
    request<User>("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) }),

  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  listBills: (token: string, status?: string) =>
    request<Bill[]>(`/bills${status ? `?status=${status}` : ""}`, { method: "GET" }, token),

  createBill: (token: string, payload: BillInput) =>
    request<Bill>("/bills", { method: "POST", body: JSON.stringify(payload) }, token),

  updateBill: (token: string, id: string, payload: Partial<BillInput>) =>
    request<Bill>(`/bills/${id}`, { method: "PUT", body: JSON.stringify(payload) }, token),

  deleteBill: (token: string, id: string) =>
    request<void>(`/bills/${id}`, { method: "DELETE" }, token),

  markPaid: (token: string, id: string) =>
    request<Bill>(`/bills/${id}/mark-paid`, { method: "POST" }, token),

  getDashboardStats: (token: string) => request<DashboardStats>("/dashboard/stats", { method: "GET" }, token),

  getDashboardCharts: (token: string) => request<DashboardCharts>("/dashboard/charts", { method: "GET" }, token),

  listSubscriptions: (token: string, status?: string) =>
    request<Subscription[]>(
      `/subscriptions${status ? `?status_filter=${status}` : ""}`,
      { method: "GET" },
      token
    ),

  createSubscription: (token: string, payload: SubscriptionInput) =>
    request<Subscription>("/subscriptions", { method: "POST", body: JSON.stringify(payload) }, token),

  updateSubscription: (token: string, id: string, payload: Partial<SubscriptionInput & { status: string }>) =>
    request<Subscription>(`/subscriptions/${id}`, { method: "PUT", body: JSON.stringify(payload) }, token),

  deleteSubscription: (token: string, id: string) =>
    request<void>(`/subscriptions/${id}`, { method: "DELETE" }, token),

  extractBill: async (token: string, file: File): Promise<ExtractedBillData> => {
    const formData = new FormData();
    formData.append("file", file);
    
    const res = await fetch(`${API_URL}/bills/extract`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });
    
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      const message = data?.detail || "AI Extraction failed";
      throw new ApiError(typeof message === "string" ? message : "Extraction failed", res.status);
    }
    return res.json();
  },
};
