import React, { useEffect, useMemo, useState } from 'react';
import { getMarketSummary, getBankHistory } from '../services/api';
import {
    ArrowUpRight,
    ArrowDownRight,
    Activity,
    DollarSign,
    BarChart2,
    LineChart,
    Waves,
    PieChart as PieChartIcon,
} from 'lucide-react';
import {
    ResponsiveContainer,
    ComposedChart,
    Area,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Brush,
    PieChart,
    Pie,
    Cell,
    Legend,
} from 'recharts';

//const USE_MOCK = typeof import.meta !== 'undefined' && import.meta.env?.VITE_USE_MOCK === 'true';

const MOCK_SUMMARY = {
    date: '2025-01-10',
    total_volume: 125_000_000,
    top_gainers: [
        { symbol: 'VCB', change: 2.8 },
        { symbol: 'ACB', change: 2.1 },
        { symbol: 'MBB', change: 1.9 },
        { symbol: 'CTG', change: 1.5 },
        { symbol: 'TCB', change: 1.2 },
    ],
    top_losers: [
        { symbol: 'VPB', change: -2.4 },
        { symbol: 'STB', change: -1.9 },
        { symbol: 'EIB', change: -1.4 },
        { symbol: 'HDB', change: -1.2 },
        { symbol: 'TPB', change: -0.8 },
    ],
};

function generateMockHistory(days = 120) {
    const data = [];
    let close = 100;
    for (let i = days - 1; i >= 0; i -= 1) {
        const date = new Date(Date.now() - i * 24 * 3600 * 1000).toISOString().slice(0, 10);
        const ret = (Math.random() - 0.5) * 0.02; // +/-1% per day
        close = close * (1 + ret);
        const volume = 50_000_000 + Math.random() * 50_000_000;
        data.push({ date, close, volume });
    }
    return data;
}

const StatCard = ({ title, value, change, isPositive, icon: Icon }) => (
    <div className="bg-gray-900 border border-gray-800 p-6 rounded-lg relative overflow-hidden group hover:border-blue-900 transition-colors">
        <div className={`absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
            <Icon size={64} />
        </div>
        <h3 className="text-gray-400 text-sm font-medium uppercase tracking-wider mb-2">{title}</h3>
        <div className="flex items-end gap-3">
            <span className="text-2xl font-bold text-white">{value}</span>
            {change && (
                <span className={`text-sm font-bold flex items-center ${isPositive ? 'text-green-500' : 'text-red-500'}`}>
                    {isPositive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
                    {change}%
                </span>
            )}
        </div>
    </div>
);

const TickerItem = ({ symbol, change }) => {
    const isPos = change >= 0;
    return (
        <div className="flex items-center gap-2 px-4 py-2 bg-gray-900 border border-gray-800 rounded mx-2 min-w-[120px]">
            <span className="font-bold text-sm">{symbol}</span>
            <span className={`text-xs font-mono font-bold ${isPos ? 'text-green-500' : 'text-red-500'}`}>
                {isPos ? '+' : ''}{change}%
            </span>
        </div>
    );
};

const Dashboard = () => {
    const [summary, setSummary] = useState(null);
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            try {
                if (USE_MOCK) {
                    if (cancelled) return;
                    setSummary(MOCK_SUMMARY);
                    setHistory(generateMockHistory());
                    return;
                }

                const [sumRes, histRes] = await Promise.all([
                    getMarketSummary(),
                    getBankHistory('ALL'),
                ]);
                if (cancelled) return;

                const summaryData = sumRes?.data || {};
                const hasTopGainers = Array.isArray(summaryData.top_gainers) && summaryData.top_gainers.length;
                const hasTopLosers = Array.isArray(summaryData.top_losers) && summaryData.top_losers.length;
                setSummary({
                    ...summaryData,
                    top_gainers: hasTopGainers ? summaryData.top_gainers : MOCK_SUMMARY.top_gainers,
                    top_losers: hasTopLosers ? summaryData.top_losers : MOCK_SUMMARY.top_losers,
                });

                const hist = Array.isArray(histRes?.data) && histRes.data.length ? histRes.data : generateMockHistory();
                setHistory(hist);
            } catch (err) {
                console.error(err);
                if (!cancelled) {
                    setSummary(MOCK_SUMMARY);
                    setHistory(generateMockHistory());
                }
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        load();
        return () => { cancelled = true; };
    }, []);

    const sortedHistory = useMemo(() => {
        return [...history].sort((a, b) => new Date(a.date) - new Date(b.date));
    }, [history]);

    const historyWithRet = useMemo(() => {
        let prevClose = null;
        return sortedHistory.map((d) => {
            const close = Number(d.close ?? d.Close ?? 0);
            const volume = Number(d.volume ?? d.Volume ?? 0);
            const ret = prevClose ? (close - prevClose) / prevClose : 0;
            prevClose = close || prevClose;
            return { date: d.date, close, volume, ret };
        });
    }, [sortedHistory]);

    const lastWindow = historyWithRet.slice(-21);
    const expectedReturn = lastWindow.length
        ? lastWindow.reduce((s, d) => s + (d.ret || 0), 0) / lastWindow.length
        : null;
    const riskVol = (() => {
        if (!lastWindow.length) return null;
        const mean = lastWindow.reduce((s, d) => s + (d.ret || 0), 0) / lastWindow.length;
        const variance = lastWindow.reduce((s, d) => s + Math.pow((d.ret || 0) - mean, 2), 0) / lastWindow.length;
        return Math.sqrt(variance);
    })();

    const regimeBuckets = useMemo(() => {
        let bull = 0; let bear = 0; let side = 0;
        historyWithRet.forEach((d, idx) => {
            if (idx === 0) return;
            if (d.ret >= 0.002) bull += 1;
            else if (d.ret <= -0.002) bear += 1;
            else side += 1;
        });
        return [
            { name: 'Bull', value: bull },
            { name: 'Sideway', value: side },
            { name: 'Bear', value: bear },
        ];
    }, [historyWithRet]);

    const latestRegime = (() => {
        const last = historyWithRet[historyWithRet.length - 1];
        if (!last) return { label: 'N/A', color: 'text-gray-400' };
        if (last.ret >= 0.002) return { label: 'BULL', color: 'text-green-500' };
        if (last.ret <= -0.002) return { label: 'BEAR', color: 'text-red-500' };
        return { label: 'SIDEWAY', color: 'text-yellow-400' };
    })();

    const priceChartData = useMemo(() => {
        return historyWithRet.map((d) => ({
            date: d.date,
            close: d.close,
            volumeM: d.volume / 1_000_000,
            retPct: (d.ret || 0) * 100,
        }));
    }, [historyWithRet]);

    const volTrend = useMemo(() => {
        return historyWithRet.map((d, idx, arr) => {
            const slice = arr.slice(Math.max(0, idx - 20), idx + 1);
            if (!slice.length) return { date: d.date, vol: 0 };
            const mean = slice.reduce((s, x) => s + (x.ret || 0), 0) / slice.length;
            const variance = slice.reduce((s, x) => s + Math.pow((x.ret || 0) - mean, 2), 0) / slice.length;
            return { date: d.date, vol: Math.sqrt(variance) };
        });
    }, [historyWithRet]);

    const formatPct = (v, digits = 2) => {
        if (v === null || v === undefined || Number.isNaN(v)) return '–';
        return `${(v * 100).toFixed(digits)}%`;
    };

    if (loading) return <div className="p-8 text-gray-500 animate-pulse">Đang tải dữ liệu dashboard...</div>;
    if (!summary) return <div className="p-8 text-red-400">Không lấy được dữ liệu thị trường.</div>;

    return (
        <div className="p-8 space-y-8">
            <div>
                <h1 className="text-2xl font-bold text-white">Banking Market Dashboard</h1>
                <p className="text-gray-400">Bức tranh lớn: lợi suất kỳ vọng, rủi ro trung bình, phân bố regime và biến động nổi bật.</p>
            </div>

            {/* Top Stats Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6">
                <StatCard
                    title="Lợi suất kỳ vọng (21D)"
                    value={formatPct(expectedReturn)}
                    change={expectedReturn ? (expectedReturn * 100).toFixed(2) : null}
                    isPositive={(expectedReturn ?? 0) >= 0}
                    icon={LineChart}
                />
                <StatCard
                    title="Rủi ro trung bình"
                    value={formatPct(riskVol)}
                    change={riskVol ? (riskVol * 100).toFixed(2) : null}
                    isPositive={false}
                    icon={Waves}
                />
                <StatCard
                    title="Regime hiện tại"
                    value={latestRegime.label}
                    icon={Activity}
                    isPositive={latestRegime.label === 'BULL'}
                />
                <StatCard
                    title="Tổng khối lượng"
                    value={summary.total_volume.toLocaleString()}
                    icon={BarChart2}
                    isPositive={true}
                />
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Main Chart Area */}
                <div className="xl:col-span-2 bg-gray-900 border border-gray-800 rounded-lg p-6 min-h-[420px]">
                    <h2 className="text-lg font-bold mb-4 flex items-center gap-2 text-gray-100">
                        <LineChart className="text-blue-400" size={20} />
                        Chỉ số ngành (ALL) - Giá & Volume
                    </h2>
                    <div className="h-[340px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={priceChartData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                                <defs>
                                    <linearGradient id="priceArea" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                                <XAxis dataKey="date" tickFormatter={(v) => (v?.length >= 10 ? v.slice(5) : v)} stroke="#d1d5db" />
                                <YAxis yAxisId="left" stroke="#d1d5db" />
                                <YAxis yAxisId="right" orientation="right" stroke="#d1d5db" />
                                <Tooltip contentStyle={{ background: '#0f172a', border: '1px solid #1f2937', color: '#e5e7eb' }} />
                                <Area yAxisId="left" type="monotone" dataKey="close" stroke="#3b82f6" strokeWidth={2} fill="url(#priceArea)" dot={false} />
                                <Bar yAxisId="right" dataKey="volumeM" barSize={10} fill="#9ca3af" opacity={0.5} />
                                <Brush dataKey="date" height={18} stroke="#3b82f6" />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Regime Distribution */}
                <div className="bg-gray-900 border border-gray-800 rounded-lg p-6 space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-sm text-gray-400">Phân bố trạng thái</h3>
                            <div className="flex items-center gap-2 font-semibold text-gray-100">
                                <PieChartIcon size={18} className="text-blue-400" />
                                3 tháng gần nhất
                            </div>
                        </div>
                    </div>
                    <div className="h-64">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={regimeBuckets}
                                    dataKey="value"
                                    nameKey="name"
                                    innerRadius={50}
                                    outerRadius={80}
                                    paddingAngle={4}
                                    label={(d) => `${d.name} (${d.value})`}
                                >
                                    {regimeBuckets.map((entry, idx) => {
                                        const colors = ['#10b981', '#fbbf24', '#ef4444'];
                                        return <Cell key={`cell-${idx}`} fill={colors[idx]} />;
                                    })}
                                </Pie>
                                <Legend />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                    <div className={`text-sm font-semibold ${latestRegime.color}`}>
                        Regime hiện tại: {latestRegime.label}
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Risk Trend */}
                <div className="xl:col-span-2 bg-gray-900 border border-gray-800 rounded-lg p-6 min-h-[360px]">
                    <h2 className="text-lg font-bold mb-4 flex items-center gap-2 text-gray-100">
                        <Waves className="text-blue-400" size={20} />
                        Xu hướng rủi ro (Rolling 21D vol)
                    </h2>
                    <div className="h-[280px]">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={volTrend} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
                                <XAxis dataKey="date" tickFormatter={(v) => (v?.length >= 10 ? v.slice(5) : v)} stroke="#d1d5db" />
                                <YAxis stroke="#d1d5db" tickFormatter={(v) => `${(v * 100).toFixed(2)}%`} />
                                <Tooltip formatter={(v) => `${(v * 100).toFixed(2)}%`} contentStyle={{ background: '#0f172a', border: '1px solid #1f2937', color: '#e5e7eb' }} />
                                <Area type="monotone" dataKey="vol" stroke="#f59e0b" fill="#f59e0b33" strokeWidth={2} dot={false} />
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Top Movers Column */}
                <div className="space-y-6">
                    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                        <h2 className="text-sm font-bold text-green-500 uppercase tracking-wider mb-4 border-b border-gray-800 pb-2">Top Gainers</h2>
                        <div className="space-y-3">
                            {summary.top_gainers.map((s, i) => (
                                <div key={i} className="flex justify-between items-center group cursor-pointer hover:bg-gray-800 p-2 rounded transition-colors">
                                    <span className="font-bold text-gray-100">{s.symbol}</span>
                                    <span className="text-green-400 font-mono font-bold bg-green-500/10 px-2 py-1 rounded">
                                        {s.change >= 0 ? '+' : ''}{s.change}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="bg-gray-900 border border-gray-800 rounded-lg p-6">
                        <h2 className="text-sm font-bold text-red-500 uppercase tracking-wider mb-4 border-b border-gray-800 pb-2">Top Losers</h2>
                        <div className="space-y-3">
                            {summary.top_losers.map((s, i) => (
                                <div key={i} className="flex justify-between items-center group cursor-pointer hover:bg-gray-800 p-2 rounded transition-colors">
                                    <span className="font-bold text-gray-100">{s.symbol}</span>
                                    <span className="text-red-400 font-mono font-bold bg-red-500/10 px-2 py-1 rounded">
                                        {s.change}%
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
