import React, { useState, useEffect } from 'react';
import { ShieldAlert, Activity, Cpu, CheckCircle2, RefreshCw } from 'lucide-react';

export default function App() {
  const [backendStatus, setBackendStatus] = useState({ loading: true, online: false, data: null });

  const checkBackend = async () => {
    setBackendStatus({ loading: true, online: false, data: null });
    try {
      const res = await fetch('/api/health');
      if (res.ok) {
        const data = await res.json();
        setBackendStatus({ loading: false, online: true, data });
      } else {
        setBackendStatus({ loading: false, online: false, data: null });
      }
    } catch (err) {
      setBackendStatus({ loading: false, online: false, data: null });
    }
  };

  useEffect(() => {
    checkBackend();
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Header Banner */}
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Cpu className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              CreditLens-MSME
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                Phase 0 Setup
              </span>
            </h1>
            <p className="text-xs text-slate-400">From Credit Risk Prediction to Safer MSME Lending</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <button
            onClick={checkBackend}
            className="flex items-center space-x-2 text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${backendStatus.loading ? 'animate-spin' : ''}`} />
            <span>Check Backend API</span>
          </button>
        </div>
      </header>

      {/* Synthetic Data Banner */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2.5 flex items-center space-x-2 text-xs text-amber-300">
        <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0" />
        <span>
          <strong>Synthetic Data Notice:</strong> This prototype operates strictly on 100% synthetic data for MSME profiles, transactions, and credit scores. No real borrower data or live APIs are used.
        </span>
      </div>

      {/* Main Content Area */}
      <main className="flex-1 p-8 max-w-5xl mx-auto w-full flex flex-col justify-center">
        <div className="p-8 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-2xl relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-indigo-600/5 rounded-full blur-3xl -z-10"></div>
          
          <h2 className="text-2xl font-bold text-white mb-2">Phase 0: Project Setup Verification</h2>
          <p className="text-slate-400 text-sm mb-6">
            The foundation for CreditLens-MSME has been created. Frontend and Backend modules are initialized and connected.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8">
            {/* Backend Status Card */}
            <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-4">
              <div className={`p-3 rounded-lg ${backendStatus.online ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'}`}>
                <Activity className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-sm text-slate-200">Backend API Status</h3>
                {backendStatus.loading ? (
                  <p className="text-xs text-slate-500 mt-1">Connecting to http://127.0.0.1:8000...</p>
                ) : backendStatus.online ? (
                  <div>
                    <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-medium mt-1">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Online (FastAPI + Uvicorn)
                    </span>
                    <p className="text-xs text-slate-500 mt-1">Data Mode: {backendStatus.data?.data_mode}</p>
                  </div>
                ) : (
                  <p className="text-xs text-rose-400 mt-1">Offline (Start backend service to connect)</p>
                )}
              </div>
            </div>

            {/* Frontend Status Card */}
            <div className="p-5 rounded-xl bg-slate-950/60 border border-slate-800 flex items-start space-x-4">
              <div className="p-3 rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
                <Cpu className="w-6 h-6" />
              </div>
              <div>
                <h3 className="font-semibold text-sm text-slate-200">Frontend Environment</h3>
                <span className="inline-flex items-center gap-1.5 text-xs text-emerald-400 font-medium mt-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> Running (Vite + React 18 + Tailwind CSS)
                </span>
                <p className="text-xs text-slate-500 mt-1">Proxy enabled on /api</p>
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3">Project Blueprint & Structure</h4>
            <ul className="text-xs text-slate-300 space-y-2 font-mono">
              <li className="flex items-center gap-2"><span className="text-emerald-400">✓</span> frontend/ — React + Tailwind CSS + Recharts Dashboard</li>
              <li className="flex items-center gap-2"><span className="text-emerald-400">✓</span> backend/ — FastAPI REST Server & CORS Middleware</li>
              <li className="flex items-center gap-2"><span className="text-emerald-400">✓</span> ml/ — Risk scoring, XAI, Fairness & Optimizer Engines</li>
              <li className="flex items-center gap-2"><span className="text-emerald-400">✓</span> data/ — Synthetic data storage & data schema validation</li>
              <li className="flex items-center gap-2"><span className="text-emerald-400">✓</span> tests/ — Pytest unit & API validation suite</li>
            </ul>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 px-6 py-4 text-center text-xs text-slate-500">
        CreditLens-MSME &copy; 2026 — Decision Support System for Safer MSME Lending
      </footer>
    </div>
  );
}
