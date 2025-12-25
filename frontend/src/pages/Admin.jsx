import React, { useEffect, useState } from 'react';
import { getLogs, triggerPipeline, retrainModel, getTrainingResults, getTrainingMetrics } from '../services/api';
import { Terminal, Play, RefreshCw, Activity, Server, ShieldCheck, BarChart2, TrendingUp, CheckCircle2 } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Brush } from 'recharts';

const Admin = () => {
    const [logs, setLogs] = useState([]);
    const [status, setStatus] = useState('');
    const [trainingData, setTrainingData] = useState([]);
    const [metrics, setMetrics] = useState([]);
    const [selectedModel, setSelectedModel] = useState('return');
    const [viewSymbol, setViewSymbol] = useState('');
    const [isTraining, setIsTraining] = useState(false);

    const fetchLogs = async () => {
        try {
            const res = await getLogs();
            setLogs(res.data.logs);
        } catch (err) {
            console.error(err);
        }
    };

    const fetchTrainingResults = async () => {
        try {
            const res = await getTrainingResults();
            if (res.data.status === "Success") {
                const normalized = (res.data.data || []).map(d => ({
                    ...d,
                    // Backend returns `time`; normalize to `date` for the chart
                    date: d.date || d.time,
                }));
                setTrainingData(normalized);
                if (normalized.length > 0 && !viewSymbol) {
                    setViewSymbol(normalized[0].symbol);
                }
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchMetrics = async () => {
        try {
            const res = await getTrainingMetrics();
            if (res.data.status === "Success") {
                setMetrics(res.data.data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleTrigger = async () => {
        setStatus('Triggering pipeline...');
        try {
            await triggerPipeline();
            setStatus('Pipeline triggered. Logs will update shortly.');
            setIsTraining(true);
        } catch (err) {
            setStatus('Error triggering pipeline.');
        }
    };

    const handleRetrain = async () => {
        setStatus('Triggering model retraining...');
        try {
            await retrainModel();
            setStatus('Retraining started (PID). Check logs for progress.');
            setIsTraining(true);
        } catch (err) {
            setStatus('Error triggering retraining.');
        }
    };

    useEffect(() => {
        fetchLogs();
        fetchTrainingResults();
        fetchMetrics();
    }, []);

    // Controlled polling: Only poll when training
    useEffect(() => {
        let interval;
        if (isTraining) {
            interval = setInterval(() => {
                fetchLogs();
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [isTraining]);

    // Filter data for chart
    let chartData;
    if (viewSymbol === 'ALL') {
        const modelData = trainingData.filter(d => d.model === selectedModel);
        // Group by date and average
        const grouped = {};
        modelData.forEach(d => {
            const dateKey = d.date || d.time;
            if (!dateKey) return;
            if (!grouped[dateKey]) grouped[dateKey] = { date: dateKey, trueSum: 0, predSum: 0, count: 0 };
            grouped[dateKey].trueSum += d.true;
            grouped[dateKey].predSum += d.pred;
            grouped[dateKey].count += 1;
        });
        chartData = Object.values(grouped).map(g => ({
            date: g.date,
            true: g.trueSum / g.count,
            pred: g.predSum / g.count
        })).sort((a, b) => new Date(a.date) - new Date(b.date));
    } else {
        chartData = trainingData
            .filter(d => d.model === selectedModel && d.symbol === viewSymbol)
            .map(d => ({ ...d, date: d.date || d.time }))
            .sort((a, b) => new Date(a.date) - new Date(b.date));
    }

    // Unique symbols and models for selectors
    const symbols = ['ALL', ...new Set(trainingData.map(d => d.symbol))];
    const models = [...new Set(trainingData.map(d => d.model))];

    // Filter metrics for display
    const currentModelMetrics = metrics.find(m => m.model === selectedModel);

    // Auto-scroll to bottom of logs
    const logsEndRef = React.useRef(null);

    const formatDateTick = (val) => typeof val === 'string' ? val.slice(0, 10) : '';
    useEffect(() => {
        // Only auto-scroll if we are currently training/running a pipeline
        if (isTraining) {
            logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }

        // Check for completion
        if (logs.length > 0) {
            const lastLog = logs[logs.length - 1];
            if (lastLog.includes("Training Complete")) {
                if (isTraining) {
                    setStatus("Training Complete. Validation data updated.");
                    fetchTrainingResults();
                    fetchMetrics();
                    setIsTraining(false); // Stop polling and scrolling
                }
            }
        }
    }, [logs, isTraining]);

    return (
        <div className="p-8 space-y-8">
            <div className="flex items-center justify-between">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <ShieldCheck className="text-blue-500" />
                    System Administration
                </h1>
                <div className="flex items-center gap-2 px-4 py-2 bg-green-500/10 text-green-400 rounded-full border border-green-500/20 text-sm font-mono">
                    <Activity size={14} />
                    System Healthy
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl">
                    <h2 className="text-lg font-bold mb-6 flex items-center gap-2">
                        <Server size={18} className="text-gray-400" />
                        Pipeline Controls
                    </h2>
                    <div className="flex gap-4">
                        <button
                            onClick={handleTrigger}
                            className="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-lg font-medium transition-colors flex items-center gap-2"
                        >
                            <Play size={16} />
                            Run Data Pipeline
                        </button>
                        <button
                            onClick={handleRetrain}
                            className="bg-gray-800 hover:bg-gray-700 text-gray-200 px-5 py-2.5 rounded-lg font-medium transition-colors border border-gray-700 flex items-center gap-2"
                        >
                            <RefreshCw size={16} />
                            Retrain Models
                        </button>
                    </div>
                    {status && <p className="mt-4 text-sm font-medium text-blue-400 animate-pulse">{status}</p>}
                </div>

                <div className="bg-gray-900 border border-gray-800 p-6 rounded-xl">
                    <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                        <Activity size={18} className="text-gray-400" />
                        Live Status
                    </h2>
                    <div className="space-y-4">
                        <div className="flex justify-between items-center py-2 border-b border-gray-800">
                            <span className="text-gray-400">Backend API</span>
                            <span className="text-green-500 text-sm font-mono font-bold">ONLINE</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-gray-800">
                            <span className="text-gray-400">Database</span>
                            <span className="text-green-500 text-sm font-mono font-bold">CONNECTED</span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                            <span className="text-gray-400">Model Registry</span>
                            <span className="text-blue-500 text-sm font-mono font-bold">VERSION 1.0.4</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Training Visualization Section */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
                <h2 className="text-lg font-bold mb-6 flex items-center gap-2">
                    <BarChart2 size={18} className="text-purple-500" />
                    Model Performance Validation (True vs Pred)
                </h2>

                {trainingData.length > 0 ? (
                    <div>
                        <div className="flex flex-col md:flex-row gap-6 mb-6">
                            <div className="flex-1 space-y-4">
                                <div className="flex gap-4">
                                    <select
                                        value={selectedModel}
                                        onChange={e => setSelectedModel(e.target.value)}
                                        className="bg-gray-950 border border-gray-700 text-white rounded px-3 py-2 text-sm flex-1"
                                    >
                                        {models.map(m => <option key={m} value={m}>{m.toUpperCase()} Model</option>)}
                                    </select>

                                    <select
                                        value={viewSymbol}
                                        onChange={e => setViewSymbol(e.target.value)}
                                        className="bg-gray-950 border border-gray-700 text-white rounded px-3 py-2 text-sm flex-1"
                                    >
                                        {symbols.map(s => <option key={s} value={s}>{s === 'ALL' ? 'ALL SYMBOLS (AVG)' : s}</option>)}
                                    </select>
                                </div>

                                {currentModelMetrics && (
                                    <div className="bg-gray-950 border border-gray-800 rounded p-4 flex items-center gap-4">
                                        <div className="bg-purple-500/10 p-2 rounded-full">
                                            <TrendingUp size={20} className="text-purple-500" />
                                        </div>
                                        <div>
                                            <p className="text-gray-400 text-xs uppercase font-bold tracking-wider">Evaluation Metrics</p>
                                            <div className="flex gap-4 mt-1">
                                                {currentModelMetrics.rmse && (
                                                    <div>
                                                        <span className="text-gray-500 text-xs mr-1">RMSE:</span>
                                                        <span className="text-white font-mono font-bold">{currentModelMetrics.rmse.toFixed(4)}</span>
                                                    </div>
                                                )}
                                                {currentModelMetrics.accuracy && (
                                                    <div>
                                                        <span className="text-gray-500 text-xs mr-1">Accuracy:</span>
                                                        <span className="text-white font-mono font-bold">{(currentModelMetrics.accuracy * 100).toFixed(2)}%</span>
                                                    </div>
                                                )}
                                                <div className="flex items-center gap-1 text-green-500 text-xs bg-green-500/10 px-2 py-0.5 rounded-full border border-green-500/20">
                                                    <CheckCircle2 size={10} />
                                                    <span>Verified</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="h-80 w-full bg-white rounded border border-gray-200 p-4">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                                    <XAxis
                                        dataKey="date"
                                        stroke="#374151"
                                        tick={{ fill: '#374151', fontSize: 10 }}
                                        tickFormatter={formatDateTick}
                                    />
                                    <YAxis
                                        stroke="#374151"
                                        tick={{ fill: '#374151', fontSize: 10 }}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e5e7eb', color: '#111827' }}
                                        itemStyle={{ color: '#111827' }}
                                    />
                                    <Legend wrapperStyle={{ color: '#374151' }} />
                                    <Line type="monotone" dataKey="true" stroke="#10b981" name="True Value" strokeWidth={2} dot={false} />
                                    <Line type="monotone" dataKey="pred" stroke="#f59e0b" name="Predicted" strokeWidth={2} dot={false} strokeDasharray="5 5" />
                                    <Brush dataKey="date" height={30} stroke="#9ca3af" fill="#f3f4f6" tickFormatter={formatDateTick} />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                ) : (
                    <div className="text-gray-500 italic text-center py-10">
                        No training results available. Run "Retrain Models" to generate validation data.
                    </div>
                )}
            </div>

            <div className="bg-gray-950 border border-gray-800 rounded-xl overflow-hidden shadow-inner">
                <div className="bg-gray-900 px-6 py-3 border-b border-gray-800 flex items-center gap-2">
                    <Terminal size={14} className="text-gray-500" />
                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider">System Logs</h3>
                </div>
                <div className="p-6 font-mono text-xs h-64 overflow-y-auto space-y-1 text-gray-400 bg-gray-950">
                    {logs.length === 0 ? (
                        <p className="text-gray-600 italic">Reading system logs...</p>
                    ) : (
                        logs.map((log, i) => (
                            <div key={i} className="hover:bg-gray-900/50 py-0.5 px-2 rounded -mx-2 flex gap-4">
                                <span className="text-gray-500 select-none mr-2">$</span>
                                <span className="break-all">{log}</span>
                            </div>
                        ))
                    )}
                    <div ref={logsEndRef} />
                </div>
            </div>
        </div>
    );
};

export default Admin;
