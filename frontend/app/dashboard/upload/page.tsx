"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Navbar from "@/components/Navbar";
import ProtectedRoute from "@/components/ProtectedRoute";
import { api, ExtractedBillData, BillInput } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import BillFormModal from "@/components/BillFormModal";

export default function UploadBillPage() {
  const { token } = useAuth();
  const router = useRouter();
  
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [extractedData, setExtractedData] = useState<ExtractedBillData | null>(null);
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file || !token) return;
    
    setUploading(true);
    setError(null);
    
    try {
      const data = await api.extractBill(token, file);
      setExtractedData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to extract bill data");
    } finally {
      setUploading(false);
    }
  };

  const handleSaveBill = async (payload: BillInput) => {
    if (!token) return;
    await api.createBill(token, payload);
    router.push("/bills");
  };

  const mapExtractedToInitial = (data: ExtractedBillData): any => {
    return {
      provider: data.provider || "",
      amount: data.amount ? data.amount.toString() : "",
      currency: data.currency || "INR",
      due_date: data.due_date || "",
      billing_period: (data.billing_period?.toLowerCase() === "monthly" || data.billing_period?.toLowerCase() === "yearly") ? data.billing_period.toLowerCase() : "one_time",
    };
  };

  return (
    <ProtectedRoute>
      <Navbar />
      <main className="mx-auto max-w-3xl px-4 py-10">
        <h1 className="text-2xl font-semibold text-slate-900">Upload a Bill</h1>
        <p className="mt-2 text-slate-600 mb-8">
          Upload a PDF or image of your bill. Our AI will extract the details automatically.
        </p>

        {!extractedData ? (
          <div className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-slate-300 rounded-lg bg-slate-50">
              <input
                type="file"
                accept=".pdf,image/jpeg,image/png"
                onChange={handleFileChange}
                className="mb-4 text-slate-700"
              />
              <p className="text-sm text-slate-500 mb-6">Supported formats: PDF, JPG, PNG</p>
              
              {error && (
                <p className="text-red-600 text-sm mb-4 px-4 py-2 bg-red-50 rounded-md">
                  {error}
                </p>
              )}
              
              <button
                onClick={handleUpload}
                disabled={!file || uploading}
                className="bg-brand-600 hover:bg-brand-700 text-white font-medium py-2 px-6 rounded-md disabled:opacity-50 transition-colors"
              >
                {uploading ? "Extracting..." : "Upload & Extract"}
              </button>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-slate-900 mb-4">Review Extracted Data</h2>
            <p className="text-sm text-slate-600 mb-6">
              Please review the extracted information below and correct any mistakes before saving.
            </p>
            {/* Render the modal properly */}
            <BillFormModal 
              initial={mapExtractedToInitial(extractedData)} 
              onSave={handleSaveBill} 
              onClose={() => setExtractedData(null)} 
            />
          </div>
        )}
      </main>
    </ProtectedRoute>
  );
}
