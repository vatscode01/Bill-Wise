"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth-context";

export default function Navbar() {
  const { user, logout } = useAuth();

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
        <Link href={user ? "/dashboard" : "/"} className="text-lg font-semibold text-brand-700">
          BillWise
        </Link>

        {user ? (
          <div className="flex items-center gap-4 text-sm">
            <Link href="/dashboard" className="text-slate-600 hover:text-brand-700">
              Dashboard
            </Link>
            <Link href="/bills" className="text-slate-600 hover:text-brand-700">
              Bills
            </Link>
            <Link href="/subscriptions" className="text-slate-600 hover:text-brand-700">
              Subscriptions
            </Link>
            <span className="text-slate-400">{user.email}</span>
            <button
              onClick={logout}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-slate-700 hover:bg-slate-100"
            >
              Log out
            </button>
          </div>
        ) : (
          <div className="flex items-center gap-3 text-sm">
            <Link href="/login" className="text-slate-600 hover:text-brand-700">
              Log in
            </Link>
            <Link
              href="/register"
              className="rounded-md bg-brand-600 px-3 py-1.5 text-white hover:bg-brand-700"
            >
              Sign up
            </Link>
          </div>
        )}
      </div>
    </nav>
  );
}
