import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Activity,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Sliders,
  TrendingDown,
  TrendingUp,
  ArrowRight,
  ShieldCheck,
  FileText,
  DollarSign,
  Percent,
  Clock,
  Award,
  ChevronRight
} from 'lucide-react';

export default function App() {
  const [msmeList, setMsmeList] = useState([]);
  const [selectedMsmeId, setSelectedMsmeId] = useState('MSME_005');
  const [customAmount, setCustomAmount] = useState('');
  const [customTenure, setCustomTenure] = useState('36');
  const [customRate, setCustomRate] = useState('12.0');

  const [backendStatus, setBackendStatus] = useState({ loading: true, online: false });
  const [optimizerState, setOptimizerState] = useState({
    loading: false,
    data: null,
    error: null
  });

  // Check backend health & fetch sample MSME list
  const initializeApp = async () => {
    setBackendStatus({ loading: true, online: false });
    try {
      const healthRes = await fetch('/api/health');
      if (healthRes.ok) {
        setBackendStatus({ loading: false, online: true });
      } else {
        setBackendStatus({ loading: false, online: false });
      }

      const listRes = await fetch('/api/msme-list');
      if (listRes.ok) {
        const listData = await listRes.json();
        setMsmeList(listData.msmes || []);
      }
    } catch (err) {
      setBackendStatus({ loading: false, online: false });
    }
  };

  useEffect(() => {
    initializeApp();
  }, []);

  // Run credit optimization
  const runOptimization = async (msmeIdToUse = selectedMsmeId) => {
    setOptimizerState({ loading: true, data: null, error: null });
    try {
      const payload = {
        msme_id: msmeIdToUse,
        requested_loan_amount: customAmount ? parseFloat(customAmount) : null,
        requested_tenure_months: parseInt(customTenure, 10),
        interest_rate: parseFloat(customRate)
      };

      const res = await fetch('/api/optimize-credit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData.detail || `Optimization request failed with status ${res.status}`);
      }

      const data = await res.json();
      setOptimizerState({ loading: false, data, error: null });
    } catch (err) {
      setOptimizerState({ loading: false, data: null, error: err.message });
    }
  };

  // Run initial optimization when selected MSME changes or on load
  useEffect(() => {
    if (selectedMsmeId) {
      runOptimization(selectedMsmeId);
    }
  }, [selectedMsmeId]);

  const handleSelectMsme = (id) => {
    setSelectedMsmeId(id);
    setCustomAmount(''); // reset custom amount override on MSME switch
  };

  const selectedMsmeInfo = msmeList.find((m) => m.msme_id === selectedMsmeId);
  const result = optimizerState.data;

  const formatINR = (val) => {
    if (val === undefined || val === null) return '₹0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  const getRiskBandBadge = (band) => {
    switch (band) {
      case 'Standard':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Standard Risk</span>;
      case 'Watchlist':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">Watchlist</span>;
      case 'High Risk':
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">High Risk</span>;
      default:
        return <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-300">{band || 'Unknown'}</span>;
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-indigo-600/20 border border-indigo-500/30 rounded-xl text-indigo-400">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-lg font-bold tracking-tight text-white flex items-center gap-2">
              CreditLens-MSME
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                Phase 6 Credit Optimizer
              </span>
            </h1>
            <p className="text-xs text-slate-400">Explainable & Feasibility-Constrained Credit Structuring</p>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-xs">
            <div className={`w-2 h-2 rounded-full ${backendStatus.online ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`}></div>
            <span className="text-slate-300 font-mono">
              API: {backendStatus.loading ? 'Checking...' : backendStatus.online ? 'Online' : 'Offline'}
            </span>
          </div>
          <button
            onClick={initializeApp}
            className="flex items-center space-x-1.5 text-xs px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-all border border-slate-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${backendStatus.loading ? 'animate-spin' : ''}`} />
            <span>Reload</span>
          </button>
        </div>
      </header>

      {/* Synthetic Data Banner */}
      <div className="bg-amber-500/10 border-b border-amber-500/20 px-6 py-2 flex items-center justify-between text-xs text-amber-300">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-amber-400 flex-shrink-0" />
          <span>
            <strong>Synthetic Data Notice:</strong> 100% synthetic MSME profiles. Objective weights: Amount=0.40 | PD=0.25 | DSCR=0.25 | Expected Loss=0.10.
          </span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 p-6 max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Column: MSME Selector & Controls */}
        <aside className="lg:col-span-4 space-y-6">
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-400" />
                Borrower & Parameters
              </h2>
              <span className="text-xs text-slate-500">{msmeList.length} Sample MSMEs</span>
            </div>

            {/* MSME Dropdown Selector */}
            <div>
              <label className="block text-xs font-medium text-slate-400 mb-1.5">Select Portfolio MSME</label>
              <select
                value={selectedMsmeId}
                onChange={(e) => handleSelectMsme(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500 transition-all"
              >
                {msmeList.map((m) => (
                  <option key={m.msme_id} value={m.msme_id}>
                    {m.msme_id} — {m.business_name} ({m.sector})
                  </option>
                ))}
              </select>
            </div>

            {/* Selected MSME Quick Metadata */}
            {selectedMsmeInfo && (
              <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs space-y-1.5">
                <div className="flex justify-between">
                  <span className="text-slate-400">Business:</span>
                  <span className="text-slate-200 font-medium">{selectedMsmeInfo.business_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Sector:</span>
                  <span className="text-slate-200">{selectedMsmeInfo.sector}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Turnover:</span>
                  <span className="text-slate-200 font-mono">{formatINR(selectedMsmeInfo.annual_turnover)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400">Credit Score:</span>
                  <span className="text-slate-200 font-mono">{selectedMsmeInfo.credit_score}</span>
                </div>
              </div>
            )}

            {/* Parameter Adjustment Form */}
            <div className="space-y-3 pt-2 border-t border-slate-800">
              <div>
                <label className="block text-xs text-slate-400 mb-1">
                  Requested Loan Amount (INR) <span className="text-slate-500">(Optional override)</span>
                </label>
                <input
                  type="number"
                  placeholder={selectedMsmeInfo ? selectedMsmeInfo.requested_loan_amount : 'e.g. 500000'}
                  value={customAmount}
                  onChange={(e) => setCustomAmount(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Tenure (Months)</label>
                  <select
                    value={customTenure}
                    onChange={(e) => setCustomTenure(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-2 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  >
                    <option value="24">24 months</option>
                    <option value="36">36 months</option>
                    <option value="48">48 months</option>
                    <option value="60">60 months</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs text-slate-400 mb-1">Interest Rate (%)</label>
                  <input
                    type="number"
                    step="0.5"
                    value={customRate}
                    onChange={(e) => setCustomRate(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-1.5 text-xs text-white focus:outline-none focus:border-indigo-500 font-mono"
                  />
                </div>
              </div>

              <button
                onClick={() => runOptimization()}
                disabled={optimizerState.loading}
                className="w-full mt-2 py-2.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-semibold text-xs transition-all shadow-lg shadow-indigo-600/20 flex items-center justify-center space-x-2"
              >
                {optimizerState.loading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Running Optimization Grid...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>Run Credit Optimizer</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Policy Constraint Configuration Card */}
          <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 text-xs space-y-2">
            <h3 className="font-semibold text-slate-300 uppercase tracking-wider text-[10px]">Active Risk Policy Constraints</h3>
            <ul className="text-slate-400 space-y-1 font-mono text-[11px]">
              <li className="flex justify-between"><span>Min Base DSCR:</span> <span className="text-indigo-400 font-semibold">1.20x</span></li>
              <li className="flex justify-between"><span>Min Downside DSCR:</span> <span className="text-indigo-400 font-semibold">1.00x</span></li>
              <li className="flex justify-between"><span>Max Downside Months &lt; 1:</span> <span className="text-indigo-400 font-semibold">0</span></li>
              <li className="flex justify-between"><span>Max Allowed PD:</span> <span className="text-indigo-400 font-semibold">25.0%</span></li>
            </ul>
          </div>
        </aside>

        {/* Right Column: Optimization Results & Analysis */}
        <main className="lg:col-span-8 space-y-6">

          {/* Loading State */}
          {optimizerState.loading && (
            <div className="p-12 rounded-2xl bg-slate-900 border border-slate-800 text-center space-y-3">
              <RefreshCw className="w-8 h-8 text-indigo-400 animate-spin mx-auto" />
              <h3 className="text-sm font-semibold text-white">Searching Feasibility Space</h3>
              <p className="text-xs text-slate-400">Evaluating multi-dimensional grid of loan amounts, tenures, and rates under cashflow downside bounds...</p>
            </div>
          )}

          {/* Error State */}
          {optimizerState.error && (
            <div className="p-6 rounded-2xl bg-rose-500/10 border border-rose-500/30 text-rose-300 flex items-start space-x-3">
              <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-sm text-rose-200">Optimization Failed</h3>
                <p className="text-xs text-rose-300/80 mt-1">{optimizerState.error}</p>
              </div>
            </div>
          )}

          {/* Result Loaded */}
          {!optimizerState.loading && !optimizerState.error && result && (
            <div className="space-y-6">

              {/* Status Header Banner */}
              <div className={`p-4 rounded-2xl border flex items-center justify-between ${
                result.status === 'REQUESTED_FEASIBLE'
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : result.status === 'OPTIMIZED_RECOMMENDATION_FOUND'
                  ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
                  : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
              }`}>
                <div className="flex items-center space-x-3">
                  {result.status === 'REQUESTED_FEASIBLE' ? (
                    <CheckCircle2 className="w-6 h-6 text-emerald-400 flex-shrink-0" />
                  ) : result.status === 'OPTIMIZED_RECOMMENDATION_FOUND' ? (
                    <ShieldCheck className="w-6 h-6 text-indigo-400 flex-shrink-0" />
                  ) : (
                    <AlertTriangle className="w-6 h-6 text-amber-400 flex-shrink-0" />
                  )}
                  <div>
                    <h2 className="text-sm font-bold uppercase tracking-wider text-white">
                      {result.status === 'REQUESTED_FEASIBLE' && 'Requested Loan Fully Feasible'}
                      {result.status === 'OPTIMIZED_RECOMMENDATION_FOUND' && 'Optimized Feasible Loan Found'}
                      {result.status === 'NO_FEASIBLE_STRUCTURE' && 'No Feasible Structure Under Policy Limits'}
                    </h2>
                    <p className="text-xs opacity-90 mt-0.5">{result.reason}</p>
                  </div>
                </div>
                {result.recommended?.objective_score !== undefined && (
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase tracking-wider block">Objective Score</span>
                    <span className="text-lg font-bold font-mono text-white">{result.recommended.objective_score.toFixed(4)}</span>
                  </div>
                )}
              </div>

              {/* Side-by-Side: Requested vs Recommended Structure Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Requested Structure Card */}
                <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-4">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                    <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Requested Loan</span>
                    <span className="text-xs text-slate-500 font-mono">Original Baseline</span>
                  </div>
                  
                  {result.requested && (
                    <div className="space-y-3">
                      <div>
                        <span className="text-xs text-slate-400 block">Loan Principal</span>
                        <span className="text-2xl font-bold font-mono text-white">{formatINR(result.requested.loan_amount)}</span>
                      </div>
                      
                      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[11px]">Tenure</span>
                          <span className="font-semibold text-slate-200">{result.requested.tenure_months} mos</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[11px]">Rate</span>
                          <span className="font-semibold text-slate-200">{result.requested.interest_rate}%</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[11px]">Monthly EMI</span>
                          <span className="font-semibold text-slate-200 font-mono">{formatINR(result.requested.emi)}</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[11px]">Base DSCR</span>
                          <span className="font-semibold font-mono text-slate-200">{result.requested.average_base_dscr.toFixed(2)}x</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[11px]">Downside DSCR</span>
                          <span className={`font-semibold font-mono ${result.requested.worst_downside_dscr < 1.0 ? 'text-rose-400' : 'text-emerald-400'}`}>
                            {result.requested.worst_downside_dscr.toFixed(2)}x
                          </span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[11px]">Risk Band</span>
                          <div className="mt-0.5">{getRiskBandBadge(result.requested.risk_band)}</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Recommended Structure Card */}
                <div className={`p-5 rounded-2xl bg-slate-900 border shadow-md space-y-4 ${
                  result.recommended ? 'border-indigo-500/40 ring-1 ring-indigo-500/20' : 'border-slate-800 opacity-60'
                }`}>
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                    <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                      <Award className="w-3.5 h-3.5" />
                      Recommended Structure
                    </span>
                    <span className="text-xs text-indigo-300 font-medium">Policy Feasible</span>
                  </div>

                  {result.recommended ? (
                    <div className="space-y-3">
                      <div>
                        <span className="text-xs text-slate-400 block">Optimized Principal</span>
                        <span className="text-2xl font-bold font-mono text-indigo-300">{formatINR(result.recommended.loan_amount)}</span>
                      </div>

                      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[11px]">Tenure</span>
                          <span className="font-semibold text-white">{result.recommended.tenure_months} mos</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[11px]">Rate</span>
                          <span className="font-semibold text-white">{result.recommended.interest_rate}%</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[11px]">Monthly EMI</span>
                          <span className="font-semibold text-emerald-400 font-mono">{formatINR(result.recommended.emi)}</span>
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-2 pt-2 border-t border-slate-800/60 text-xs">
                        <div>
                          <span className="text-slate-400 block text-[11px]">Base DSCR</span>
                          <span className="font-semibold font-mono text-emerald-400">{result.recommended.average_base_dscr.toFixed(2)}x</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[11px]">Downside DSCR</span>
                          <span className="font-semibold font-mono text-emerald-400">{result.recommended.worst_downside_dscr.toFixed(2)}x</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[11px]">Risk Band</span>
                          <div className="mt-0.5">{getRiskBandBadge(result.recommended.risk_band)}</div>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="py-8 text-center text-xs text-slate-500">
                      No recommended structure available under active policy thresholds.
                    </div>
                  )}
                </div>
              </div>

              {/* Improvement Metrics Row */}
              {result.improvement && (
                <div className="p-5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-xl space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400">Optimization Improvement Impact</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                      <span className="text-[11px] text-slate-400 block">Loan Amount Retained</span>
                      <span className="text-lg font-bold font-mono text-emerald-400">
                        {(100 - result.improvement.loan_reduction_pct).toFixed(1)}%
                      </span>
                      <span className="text-[10px] text-slate-500 block mt-0.5">({result.improvement.loan_reduction_pct.toFixed(1)}% reduction)</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                      <span className="text-[11px] text-slate-400 block">EMI Relief</span>
                      <span className="text-lg font-bold font-mono text-emerald-400">
                        -{result.improvement.emi_reduction_pct.toFixed(1)}%
                      </span>
                      <span className="text-[10px] text-slate-500 block mt-0.5">Monthly cashflow savings</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                      <span className="text-[11px] text-slate-400 block">Base DSCR Gain</span>
                      <span className="text-lg font-bold font-mono text-emerald-400">
                        +{result.improvement.dscr_change.toFixed(2)}x
                      </span>
                      <span className="text-[10px] text-slate-500 block mt-0.5">Debt service coverage</span>
                    </div>

                    <div className="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
                      <span className="text-[11px] text-slate-400 block">Expected Loss Δ</span>
                      <span className="text-lg font-bold font-mono text-indigo-300">
                        {formatINR(result.improvement.expected_loss_change)}
                      </span>
                      <span className="text-[10px] text-slate-500 block mt-0.5">Lender risk reduction</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Borrower Explanation Card */}
              {result.borrower_explanation && (
                <div className="p-5 rounded-2xl bg-indigo-950/30 border border-indigo-500/20 space-y-2">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                    <FileText className="w-4 h-4" />
                    Structured Borrower Explanation
                  </h3>
                  <p className="text-sm text-slate-200 leading-relaxed italic bg-slate-950/50 p-4 rounded-xl border border-slate-800">
                    "{result.borrower_explanation}"
                  </p>
                </div>
              )}

              {/* Trade-off Frontier Table */}
              {result.tradeoff_frontier && result.tradeoff_frontier.length > 0 && (
                <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-3">
                  <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                      Trade-off Frontier (Alternative Feasible Structures)
                    </h3>
                    <span className="text-[11px] text-slate-500">{result.tradeoff_frontier.length} Non-dominated options</span>
                  </div>

                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs font-mono">
                      <thead>
                        <tr className="border-b border-slate-800 text-slate-400 text-[11px]">
                          <th className="pb-2">Loan Amount</th>
                          <th className="pb-2">Tenure</th>
                          <th className="pb-2">Rate</th>
                          <th className="pb-2">EMI</th>
                          <th className="pb-2">Base DSCR</th>
                          <th className="pb-2">Downside DSCR</th>
                          <th className="pb-2">PD</th>
                          <th className="pb-2">Obj Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800/60 text-slate-300">
                        {result.tradeoff_frontier.map((cand, idx) => (
                          <tr key={idx} className={result.recommended && cand.loan_amount === result.recommended.loan_amount && cand.tenure_months === result.recommended.tenure_months ? 'bg-indigo-600/10 text-white font-semibold' : 'hover:bg-slate-950/40'}>
                            <td className="py-2.5 text-white">{formatINR(cand.loan_amount)}</td>
                            <td className="py-2.5">{cand.tenure_months}m</td>
                            <td className="py-2.5">{cand.interest_rate}%</td>
                            <td className="py-2.5">{formatINR(cand.emi)}</td>
                            <td className="py-2.5 text-emerald-400">{cand.average_base_dscr.toFixed(2)}x</td>
                            <td className="py-2.5 text-emerald-400">{cand.worst_downside_dscr.toFixed(2)}x</td>
                            <td className="py-2.5">{(cand.pd * 100).toFixed(1)}%</td>
                            <td className="py-2.5 font-bold text-indigo-300">{cand.objective_score ? cand.objective_score.toFixed(4) : '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Closest Rejected Candidates (when NO_FEASIBLE_STRUCTURE) */}
              {result.status === 'NO_FEASIBLE_STRUCTURE' && result.closest_rejected_candidates && (
                <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 shadow-md space-y-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-rose-400">
                    Closest Rejected Candidates & Policy Violations
                  </h3>
                  <div className="space-y-2">
                    {result.closest_rejected_candidates.map((rej, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs space-y-1">
                        <div className="flex justify-between font-mono font-semibold text-slate-200">
                          <span>INR {formatINR(rej.loan_amount)} / {rej.tenure_months} mos @ {rej.interest_rate}%</span>
                          <span className="text-rose-400">Downside DSCR: {rej.worst_downside_dscr.toFixed(2)}x</span>
                        </div>
                        <ul className="text-[11px] text-rose-300/80 list-disc list-inside">
                          {rej.violations.map((v, vIdx) => (
                            <li key={vIdx}>{v}</li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}

        </main>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 px-6 py-4 text-center text-xs text-slate-500">
        CreditLens-MSME &copy; 2026 — Decision Support System for Safer MSME Lending
      </footer>
    </div>
  );
}
