import React, { useState } from 'react';
import { consultAdvisor } from '../services/api';
import { Loader2, Sparkles, Brain } from 'lucide-react';

const Advisor = () => {
    const [symbol, setSymbol] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleConsult = async () => {
        if (!symbol) return;
        setLoading(true);
        setResult(null);
        try {
            // Backend now runs inference
            const res = await consultAdvisor({ symbol: symbol.toUpperCase() });
            setResult(res.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-8">
            <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-purple-900/50 text-purple-400 mb-4">
                    <Brain size={24} />
                </div>
                <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-blue-400">AI Investment Advisor</h1>
                <p className="text-gray-500">Powered by Groq LLM & Interpretation Engines</p>
            </div>

            <div className="bg-gray-900 border border-gray-800 p-8 rounded-2xl shadow-xl max-w-lg mx-auto">
                <label className="block text-sm font-medium mb-3 text-gray-300">Select Bank Stock</label>
                <div className="flex gap-3">
                    <input
                        type="text"
                        value={symbol}
                        onChange={(e) => setSymbol(e.target.value)}
                        className="flex-1 bg-gray-950 border border-gray-700 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-purple-500 transition-colors"
                        placeholder="e.g. TCB"
                    />
                    <button
                        onClick={handleConsult}
                        disabled={loading}
                        className="bg-purple-600 text-white px-6 py-3 rounded-lg font-bold hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 transition-all shadow-lg shadow-purple-900/20"
                    >
                        {loading ? <Loader2 className="animate-spin" /> : <Sparkles size={18} />}
                        <span>Consult</span>
                    </button>
                </div>
            </div>

            {result && (
                <div className="bg-gray-900/80 backdrop-blur border border-purple-500/30 p-8 rounded-2xl animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <div className="flex items-center justify-between mb-6 border-b border-gray-800 pb-4">
                        <h2 className="text-2xl font-bold text-gray-100 flex items-center gap-2">
                            <span className="text-purple-400">{result.symbol}</span> Analysis
                        </h2>
                        <span className={`px-4 py-1.5 rounded-full font-bold text-sm tracking-wide border ${result.recommendation.includes('BUY')
                            ? 'bg-green-500/10 text-green-400 border-green-500/20'
                            : 'bg-gray-700 text-gray-300 border-gray-600'
                            }`}>
                            {result.recommendation}
                        </span>
                    </div>

                    {/* Confidence Meter */}
                    <div className="mb-6 bg-gray-950 p-4 rounded-xl border border-gray-800">
                        <div className="flex justify-between text-sm text-gray-400 mb-2">
                            <span>Độ tin cậy mô hình</span>
                            <span className="text-white font-medium">{(result.confidence ? result.confidence * 100 : 0).toFixed(0)}%</span>
                        </div>
                        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-gradient-to-r from-purple-600 to-blue-500 transition-all duration-1000"
                                style={{ width: `${result.confidence ? result.confidence * 100 : 0}%` }}
                            />
                        </div>
                    </div>

                    {/* Signals Grid */}
                    {result.signals && (
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                            <SignalCard label="Lợi nhuận dự báo" value={result.signals.predicted_return_21d ? `${(result.signals.predicted_return_21d * 100).toFixed(2)}%` : 'N/A'} />
                            <SignalCard label="Biến động (Risk)" value={result.signals.predicted_volatility_21d ? `${(result.signals.predicted_volatility_21d * 100).toFixed(2)}%` : 'N/A'} />
                            <SignalCard label="Chế độ (Regime)" value={['Bear', 'Neutral', 'Bull'][result.signals.regime] || result.signals.regime || 'Unknown'} />
                            <SignalCard label="Xu hướng (Trend)" value={result.signals.direction === 1 || result.signals.direction === "Up" ? 'Tăng' : (result.signals.direction === 0 || result.signals.direction === "Down" ? 'Giảm' : result.signals.direction)} />
                        </div>
                    )}

                    <div className="prose prose-invert max-w-none">
                        <h3 className="text-lg font-bold text-gray-200 mb-3">Nhận định chi tiết</h3>
                        <p className="whitespace-pre-wrap text-gray-400 leading-relaxed font-light">{result.rationale}</p>
                    </div>
                </div>
            )}
        </div>
    );
};

const SignalCard = ({ label, value }) => (
    <div className="bg-gray-950/50 p-3 rounded-lg border border-gray-800/50">
        <p className="text-xs text-gray-500 mb-1 uppercase tracking-wider">{label}</p>
        <p className="text-gray-200 font-medium">{value}</p>
    </div>
);

export default Advisor;
