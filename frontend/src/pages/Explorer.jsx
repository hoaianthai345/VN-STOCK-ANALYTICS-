import React, { useState, useEffect, useMemo } from 'react';
import { getBankHistory, getBankFinancials, getSymbols } from '../services/api';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from 'recharts';
import Chart from 'react-apexcharts';
import { Search, TrendingUp, Calendar, Info, DollarSign, PieChart, Clock } from 'lucide-react';

const Explorer = () => {
    const [symbol, setSymbol] = useState('');
    const [data, setData] = useState([]);
    const [financials, setFinancials] = useState([]);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('price'); // 'price', 'volume', 'financials'
    const [availableSymbols, setAvailableSymbols] = useState([]);
    const [timeRange, setTimeRange] = useState('1Y'); // 1W, 1M, 3M, 6M, 1Y, ALL

    useEffect(() => {
        const fetchSymbols = async () => {
            try {
                const res = await getSymbols();
                setAvailableSymbols(res.data);
            } catch (err) {
                console.error("Failed to fetch symbols", err);
            }
        };
        fetchSymbols();
    }, []);

    const handleSearch = async (e) => {
        if (e) e.preventDefault();
        if (!symbol) return;
        setLoading(true);
        try {
            const querySymbol = symbol.toUpperCase();

            // Parallel fetch
            const [histRes, finRes] = await Promise.all([
                getBankHistory(querySymbol),
                getBankFinancials(querySymbol)
            ]);

            setData(histRes.data);
            setFinancials(finRes.data);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        if (symbol) {
            handleSearch();
        }
    }, [symbol]);

    // Filter Data based on TimeRange
    const filteredData = useMemo(() => {
        if (!data.length) return [];
        if (timeRange === 'ALL') return data;

        const now = new Date();
        const cutoff = new Date();

        switch (timeRange) {
            case '1W': cutoff.setDate(now.getDate() - 7); break;
            case '1M': cutoff.setMonth(now.getMonth() - 1); break;
            case '3M': cutoff.setMonth(now.getMonth() - 3); break;
            case '6M': cutoff.setMonth(now.getMonth() - 6); break;
            case '1Y': cutoff.setFullYear(now.getFullYear() - 1); break;
            case 'YTD': cutoff.setMonth(0, 1); break; // Jan 1st
            default: return data;
        }

        return data.filter(item => new Date(item.date) >= cutoff);
    }, [data, timeRange]);

    // Prepare ApexCharts Series
    const candleSeries = useMemo(() => {
        if (!filteredData.length) return [];
        return [{
            data: filteredData.map(item => ({
                x: new Date(item.date),
                y: [item.open, item.high, item.low, item.close]
            }))
        }];
    }, [filteredData]);

    const candleOptions = {
        chart: {
            type: 'candlestick',
            height: 350,
            background: '#ffffff', // White background
            toolbar: {
                show: true,
                tools: {
                    download: true,
                    selection: true,
                    zoom: true,
                    zoomin: true,
                    zoomout: true,
                    pan: true,
                    reset: true
                }
            }
        },
        title: {
            text: `${symbol} Price Action`,
            align: 'left',
            style: { color: '#333' }
        },
        xaxis: {
            type: 'datetime',
            labels: { style: { colors: '#333' } }
        },
        yaxis: {
            tooltip: { enabled: true },
            labels: {
                style: { colors: '#333' },
                formatter: (val) => val.toLocaleString()
            }
        },
        grid: {
            borderColor: '#f1f1f1'
        },
        plotOptions: {
            candlestick: {
                colors: {
                    upward: '#22c55e', // Green
                    downward: '#ef4444' // Red
                }
            }
        },
        theme: {
            mode: 'light'
        }
    };

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="bg-gray-900 border border-gray-700 p-4 rounded shadow-xl text-xs">
                    <p className="font-bold text-gray-300 mb-2">{label}</p>
                    {payload.map((entry, index) => (
                        <p key={index} style={{ color: entry.color }} className="flex justify-between gap-4 font-mono">
                            <span>{entry.name}:</span>
                            <span className="font-bold">
                                {typeof entry.value === 'number' ? entry.value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : entry.value}
                            </span>
                        </p>
                    ))}
                </div>
            );
        }
        return null;
    };

    const ranges = ['1W', '1M', '3M', '6M', 'YTD', '1Y', 'ALL'];

    return (
        <div className="flex h-[calc(100vh-4rem)]">
            {/* Search Sidebar */}
            <div className="w-80 bg-gray-900 border-r border-gray-800 p-6 flex flex-col gap-6 overflow-y-auto">
                <div>
                    <h2 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4">Instrument</h2>
                    <div className="relative mb-4">
                        <select
                            value={symbol}
                            onChange={(e) => setSymbol(e.target.value)}
                            className="w-full bg-gray-950 border border-gray-700 text-white pl-4 pr-10 py-2.5 rounded focus:border-blue-500 focus:outline-none transition-colors appearance-none cursor-pointer"
                        >
                            <option value="" disabled>Select Bank</option>
                            <option value="ALL">ALL (Industry Average)</option>
                            {availableSymbols.map((s) => (
                                <option key={s} value={s}>{s}</option>
                            ))}
                        </select>
                        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none text-gray-500">
                            <Search size={16} />
                        </div>
                    </div>
                </div>

                {data.length > 0 && (
                    <div className="space-y-4">
                        <div className="p-4 bg-gray-950 rounded border border-gray-800">
                            <div className="text-gray-500 text-xs mb-1">{symbol === 'ALL' ? 'Avg Close Price' : 'Last Close'}</div>
                            <div className="text-2xl font-bold font-mono">
                                {data[data.length - 1].close.toLocaleString(undefined, { maximumFractionDigits: 0 })} <span className="text-sm text-gray-500">VND</span>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-wider mt-6 mb-2">Analysis View</h3>
                            <button
                                onClick={() => setActiveTab('price')}
                                className={`w-full text-left px-4 py-2 rounded text-sm font-medium transition-colors ${activeTab === 'price' ? 'bg-blue-600/20 text-blue-400 border border-blue-600/50' : 'text-gray-400 hover:bg-gray-800'}`}
                            >
                                <div className="flex items-center gap-2">
                                    <TrendingUp size={16} />
                                    Price Action (Candles)
                                </div>
                            </button>
                            <button
                                onClick={() => setActiveTab('volume')}
                                className={`w-full text-left px-4 py-2 rounded text-sm font-medium transition-colors ${activeTab === 'volume' ? 'bg-blue-600/20 text-blue-400 border border-blue-600/50' : 'text-gray-400 hover:bg-gray-800'}`}
                            >
                                <div className="flex items-center gap-2">
                                    <TrendingUp size={16} />
                                    Volume Analysis
                                </div>
                            </button>
                            <button
                                onClick={() => setActiveTab('financials')}
                                className={`w-full text-left px-4 py-2 rounded text-sm font-medium transition-colors ${activeTab === 'financials' ? 'bg-green-600/20 text-green-400 border border-green-600/50' : 'text-gray-400 hover:bg-gray-800'}`}
                            >
                                <div className="flex items-center gap-2">
                                    <DollarSign size={16} />
                                    Financials (Quarterly)
                                </div>
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Main Chart Area */}
            <div className="flex-1 overflow-hidden flex flex-col bg-gray-950 relative">
                {!data.length && !loading ? (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-600 gap-4">
                        <TrendingUp size={48} className="opacity-20" />
                        <p>Enter a symbol or select "All Industry" to start analysis</p>
                    </div>
                ) : (
                    <div className="flex-1 p-6 flex flex-col">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-lg font-bold flex items-center gap-2">
                                <span className="text-white bg-blue-600 px-2 py-0.5 rounded text-sm">{symbol.toUpperCase()}</span>
                                <span className="text-gray-400 text-sm font-normal">
                                    {activeTab === 'price' && 'Daily Candlestick'}
                                    {activeTab === 'volume' && 'Daily Volume'}
                                    {activeTab === 'financials' && 'Key Financial Metrics'}
                                </span>
                            </h2>

                            {/* Timeline Controls */}
                            <div className="flex bg-gray-900 rounded p-1 border border-gray-800">
                                {ranges.map(r => (
                                    <button
                                        key={r}
                                        onClick={() => setTimeRange(r)}
                                        className={`px-3 py-1 text-xs rounded font-medium transition-all ${timeRange === r ? 'bg-blue-600 text-white shadow' : 'text-gray-400 hover:text-white'}`}
                                    >
                                        {r}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Chart Container */}
                        <div className={`flex-1 w-full rounded-lg border border-gray-800 p-4 relative shadow-inner ${activeTab === 'price' ? 'bg-white' : 'bg-gray-900/50'}`}>

                            {activeTab === 'price' && (
                                <div className="h-full w-full text-black">
                                    <Chart
                                        options={candleOptions}
                                        series={candleSeries}
                                        type="candlestick"
                                        height="100%"
                                        width="100%"
                                    />
                                </div>
                            )}

                            {activeTab === 'volume' && (
                                <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart data={filteredData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                                        <XAxis dataKey="date" stroke="#4b5563" tick={{ fontSize: 10 }} tickMargin={10} tickFormatter={val => val.slice(0, 10)} />
                                        <YAxis stroke="#4b5563" orientation="right" tick={{ fontSize: 10 }} />
                                        <RechartsTooltip content={<CustomTooltip />} />
                                        <Area type="monotone" dataKey="volume" stroke="#10b981" fill="#10b981" fillOpacity={0.3} name="Volume" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            )}

                            {activeTab === 'financials' && financials.length > 0 && (
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={financials}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                                        <XAxis dataKey="quarter_date" stroke="#4b5563" tick={{ fontSize: 10 }} tickMargin={10} tickFormatter={val => val.slice(0, 7)} />
                                        <YAxis stroke="#4b5563" orientation="right" tick={{ fontSize: 10 }} />
                                        <RechartsTooltip content={<CustomTooltip />} />
                                        <Legend />
                                        <Bar dataKey="ROE" fill="#8884d8" name="ROE (%)" stackId="a" />
                                        <Bar dataKey="ROA" fill="#82ca9d" name="ROA (%)" stackId="b" />
                                        <Bar dataKey="P_B" fill="#ffc658" name="P/B Ratio" />
                                    </BarChart>
                                </ResponsiveContainer>
                            )}

                            {activeTab === 'financials' && financials.length === 0 && (
                                <div className="absolute inset-0 flex items-center justify-center text-gray-500">
                                    No financial data available for this selection.
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Explorer;
