import Link from "next/link";
import Navbar from "@/components/Navbar";

export default function Home() {
  return (
    <>
      <Navbar />
      <main className="mx-auto flex max-w-3xl flex-col items-center gap-6 px-4 py-24 text-center">
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">
          Never lose track of a bill again.
        </h1>
        <p className="max-w-xl text-slate-600">
          BillWise tracks your recurring bills and subscriptions, reminds you before due dates,
          and can read the numbers off an uploaded bill for you.
        </p>
        <div className="flex gap-3">
          <Link
            href="/register"
            className="rounded-md bg-brand-600 px-5 py-2.5 text-white hover:bg-brand-700"
          >
            Get started
          </Link>
          <Link
            href="/login"
            className="rounded-md border border-slate-300 px-5 py-2.5 text-slate-700 hover:bg-slate-100"
          >
            Log in
          </Link>
        </div>
      </main>
    </>
  );
}
