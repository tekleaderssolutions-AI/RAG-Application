
import React, { useState, useRef, useEffect } from 'react';
import { Send, Database, FileText, BarChart3, Bot, User, Zap, AlertCircle, Wifi, WifiOff, RefreshCcw } from 'lucide-react';
import axios from 'axios';

// IMPORTANT: Update this URL whenever your ngrok session restarts in Colab
const BASE_URL = 'https://excellently-unstaunchable-fabiola.ngrok-free.dev';

const App = () => {
    const [activeTab, setActiveTab] = useState('chat');
    const [dashboardData, setDashboardData] = useState(null);
    const [reportingData, setReportingData] = useState([]);
    const [messages, setMessages] = useState([
        {
            role: 'ai',
            content: 'Hello! I am your SAP CO-PA Intelligence Assistant. You can ask me questions about profitability, cost variances, and revenue analysis in natural language.',
            summary: 'Ready to analyze CO-PA data across Revenues, Margins, and Variances.'
        }
    ]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [isConnected, setIsConnected] = useState(null);
    const [progressStep, setProgressStep] = useState('');
    const chatEndRef = useRef(null);

    const scrollToBottom = () => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    // Connection Health Check
    const checkConnection = async () => {
        try {
            await axios.get(`${BASE_URL}/health`);
            setIsConnected(true);
        } catch (e) {
            setIsConnected(false);
        }
    };

    useEffect(() => {
        checkConnection();
        const interval = setInterval(checkConnection, 10000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        if (activeTab === 'dashboard') {
            fetchDashboard();
        } else if (activeTab === 'reports') {
            fetchReporting();
        }
    }, [activeTab]);

    const fetchDashboard = async () => {
        try {
            const res = await axios.get(`${BASE_URL}/dashboard`);
            if (res.data.error) throw new Error(res.data.error);
            setDashboardData(res.data);
        } catch (e) {
            console.error(e);
            setDashboardData({ error: 'Failed to load dashboard data. Ensure backend is running.' });
        }
    };

    const fetchReporting = async () => {
        try {
            const res = await axios.get(`${BASE_URL}/reporting`);
            if (res.data.error) throw new Error(res.data.error);
            setReportingData(Array.isArray(res.data) ? res.data : []);
        } catch (e) {
            console.error(e);
            setReportingData([]);
        }
    };

    const clearCache = async () => {
        try {
            await axios.post(`${BASE_URL}/clear-cache`);
            alert("Query cache cleared successfully.");
        } catch (e) {
            console.error(e);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!input.trim() || loading) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        const prompt = input;
        setInput('');
        setLoading(true);
        setProgressStep('Initializing request...');

        try {
            const response = await fetch(`${BASE_URL}/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            if (!response.body) {
                throw new Error('ReadableStream not supported');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep the last partial line in the buffer

                for (const line of lines) {
                    if (line.trim() === '') continue;
                    try {
                        const update = JSON.parse(line);
                        if (update.type === 'progress') {
                            setProgressStep(update.step);
                        } else if (update.type === 'result') {
                            const data = update.payload;

                            // Check for error in payload
                            if (data.error) {
                                setMessages(prev => [...prev, {
                                    role: 'ai',
                                    content: data.error, // Show error message
                                    error: true
                                }]);
                            } else {
                                setMessages(prev => [...prev, {
                                    role: 'ai',
                                    content: data.summary,
                                    data: data.data
                                }]);
                            }
                        }
                    } catch (err) {
                        console.error("Stream parse error:", err);
                    }
                }
            }
        } catch (error) {
            console.error('Chat Error:', error);
            setMessages(prev => [...prev, {
                role: 'ai',
                content: 'Connection failure. Please check ngrok URL.',
                error: true
            }]);
        } finally {
            setLoading(false);
            setProgressStep('');
        }
    };

    return (
        <div className="app-container">
            <aside className="sidebar">
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px' }}>
                    <div style={{ background: '#3b82f6', padding: '8px', borderRadius: '10px' }}>
                        <Zap size={24} color="white" fill="white" />
                    </div>
                    <div>
                        <h2 style={{ fontSize: '18px', fontWeight: 'bold' }}>SAP AI Agent</h2>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                            {isConnected === null ? (
                                <RefreshCcw size={10} className="animate-spin" color="#94a3b8" />
                            ) : isConnected ? (
                                <Wifi size={10} color="#10b981" />
                            ) : (
                                <WifiOff size={10} color="#ef4444" />
                            )}
                            <span style={{ fontSize: '10px', color: isConnected ? '#10b981' : '#ef4444', fontWeight: 'bold', textTransform: 'uppercase' }}>
                                {isConnected === null ? 'Checking...' : isConnected ? 'System Online' : 'Offline'}
                            </span>
                        </div>
                    </div>
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <SidebarItem
                        icon={<Bot size={18} />}
                        label="AI Copilot"
                        active={activeTab === 'chat'}
                        onClick={() => setActiveTab('chat')}
                    />
                    <SidebarItem
                        icon={<Database size={18} />}
                        label="Reporting"
                        active={activeTab === 'reports'}
                        onClick={() => setActiveTab('reports')}
                    />
                    <SidebarItem
                        icon={<BarChart3 size={18} />}
                        label="Dashboard"
                        active={activeTab === 'dashboard'}
                        onClick={() => setActiveTab('dashboard')}
                    />
                </nav>

                {!isConnected && isConnected !== null && (
                    <div style={{ marginTop: 'auto', padding: '16px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '12px' }}>
                        <p style={{ fontSize: '12px', color: '#ef4444', fontWeight: 'bold', marginBottom: '4px' }}>Connection Error</p>
                        <p style={{ fontSize: '10px', color: '#fca5a5', lineHeight: '1.4' }}>The frontend cannot reach the backend. Please check the ngrok URL in App.jsx.</p>
                    </div>
                )}
            </aside>

            <main className="main-content">
                {activeTab === 'chat' && (
                    <>
                        <div className="chat-window" style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                            {messages.map((m, i) => (
                                <div key={i} className={`message-wrapper ${m.role}`} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                                    <div className="bubble" style={{
                                        maxWidth: '80%',
                                        padding: m.role === 'user' ? '16px' : '0 16px 16px 0',
                                        borderRadius: '16px',
                                        background: m.role === 'user' ? '#3b82f6' : 'transparent',
                                        border: 'none'
                                    }}>
                                        <div style={{ fontWeight: 'bold', fontSize: '12px', marginBottom: '8px', color: m.role === 'user' ? '#fff' : '#94a3b8' }}>
                                            {m.role === 'ai' ? 'SAP Assistant' : 'Finance Manager'}
                                        </div>
                                        <div style={{ fontSize: '15px', color: '#fff' }}>{m.content}</div>
                                        {m.data && (
                                            <div style={{ marginTop: '16px' }}>
                                                <SmartChart data={m.data} query={m.content} />
                                            </div>
                                        )}
                                        {m.error && (
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444', marginTop: '10px', fontSize: '13px' }}>
                                                <AlertCircle size={14} /> Analysis Error
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div className="message-wrapper ai" style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '8px' }}>
                                    <div className="bubble" style={{ padding: '8px 16px', background: 'transparent', border: 'none', display: 'flex', alignItems: 'center', gap: '12px' }}>
                                        <div className="dot-typing"></div>
                                        <span style={{ fontSize: '13px', color: '#94a3b8', fontStyle: 'italic' }}>{progressStep || 'Thinking...'}</span>
                                    </div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>

                        <form className="input-area" onSubmit={handleSubmit} style={{ padding: '20px', display: 'flex', gap: '12px', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                            <input
                                type="text"
                                placeholder="Ask about revenue, cost variance, or contribution margins..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                style={{ flex: 1, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', padding: '12px 16px', borderRadius: '12px', color: '#fff' }}
                            />
                            <button type="submit" disabled={loading} style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: '12px', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '8px', cursor: loading ? 'default' : 'pointer', opacity: loading ? 0.7 : 1 }}>
                                <Send size={18} /> Analyze
                            </button>
                        </form>
                    </>
                )}

                {activeTab === 'dashboard' && (
                    <div className="dashboard-container" style={{ padding: '24px', overflowY: 'auto', height: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '32px' }}>
                            <div>
                                <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>Executive Dashboard</h1>
                                <p style={{ color: '#94a3b8' }}>Consolidated profitability and cost metrics</p>
                            </div>
                            <button onClick={clearCache} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8', padding: '8px 16px', borderRadius: '8px', cursor: 'pointer' }}>Clear Cache</button>
                        </div>

                        {dashboardData?.error ? (
                            <div style={{ padding: '40px', background: 'rgba(255,255,255,0.03)', borderRadius: '20px', textAlign: 'center', border: '1px dashed rgba(255,255,255,0.1)' }}>
                                <AlertCircle size={48} color="#ef4444" style={{ marginBottom: '16px', opacity: 0.5 }} />
                                <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>Dashboard Offline</h3>
                                <p style={{ color: '#94a3b8' }}>{dashboardData.error}</p>
                            </div>
                        ) : dashboardData && dashboardData.stats ? (
                            <>
                                <div className="kpi-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px', marginBottom: '32px' }}>
                                    <KpiCard label="Total Gross Revenue" value={`$${((dashboardData.stats.total_gross_revenue || 0) / 1e6).toFixed(1)}M`} color="#3b82f6" />
                                    <KpiCard label="Total Net Revenue" value={`$${((dashboardData.stats.total_net_revenue || 0) / 1e6).toFixed(1)}M`} color="#10b981" />
                                    <KpiCard label="Avg Margin %" value={`${(dashboardData.stats.avg_margin_pct || 0).toFixed(1)}%`} color="#fbbf24" />
                                    <KpiCard label="Cost Variance" value={`$${((dashboardData.stats.total_cost_variance || 0) / 1e6).toFixed(1)}M`} color="#ef4444" />
                                </div>

                                {dashboardData.top_plants && (
                                    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '24px', borderRadius: '20px', border: '1px solid rgba(255,255,255,0.1)' }}>
                                        <h3 style={{ marginBottom: '24px', color: '#94a3b8' }}>Top 5 Plants by Revenue</h3>
                                        <div style={{ height: '200px', display: 'flex', alignItems: 'flex-end', gap: '20px' }}>
                                            {dashboardData.top_plants.map((p, i) => (
                                                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                                    <div style={{ width: '100%', height: `${(p.revenue / Math.max(...dashboardData.top_plants.map(x => x.revenue))) * 100}%`, background: '#3b82f6', borderRadius: '4px 4px 0 0' }}></div>
                                                    <span style={{ marginTop: '12px', fontSize: '11px', color: '#94a3b8' }}>{p.plant || p.Plant}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div style={{ padding: '100px', textAlign: 'center', opacity: 0.5 }}>
                                <RefreshCcw size={32} className="animate-spin" style={{ marginBottom: '16px' }} />
                                <p>Loading analytical snapshot...</p>
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'reports' && (
                    <div className="reporting-container" style={{ padding: '24px', height: '100%', display: 'flex', flexDirection: 'column' }}>
                        <div style={{ marginBottom: '24px' }}>
                            <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>Master Data Explorer</h1>
                            <p style={{ color: '#94a3b8' }}>Dimensional breakdown of CO-PA records</p>
                        </div>

                        {reportingData.length > 0 ? (
                            <div style={{ flex: 1, overflow: 'auto', background: 'rgba(255,255,255,0.02)', borderRadius: '16px', border: '1px solid rgba(255,255,255,0.1)' }}>
                                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                    <thead style={{ position: 'sticky', top: 0, background: '#1e293b' }}>
                                        <tr>
                                            {Object.keys(reportingData[0]).map(k => (
                                                <th key={k} style={{ padding: '16px', textAlign: 'left', fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase' }}>{k}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {reportingData.map((row, i) => (
                                            <tr key={i} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                                                {Object.values(row).map((v, j) => (
                                                    <td key={j} style={{ padding: '16px', fontSize: '13px', color: '#e2e8f0' }}>
                                                        {typeof v === 'number' ? v.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : String(v)}
                                                    </td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'rgba(255,255,255,0.02)', borderRadius: '16px', border: '1px dashed rgba(255,255,255,0.1)' }}>
                                <Database size={48} color="#3b82f6" style={{ marginBottom: '16px', opacity: 0.5 }} />
                                <h3 style={{ fontSize: '18px', marginBottom: '8px' }}>No Data Available</h3>
                                <p style={{ color: '#94a3b8' }}>Check your backend connection or data source.</p>
                            </div>
                        )}
                    </div>
                )}
            </main>

            <style>{`
                .app-container { display: flex; height: 100vh; background: #0f172a; color: #fff; font-family: 'Inter', sans-serif; overflow: hidden; }
                .sidebar { width: 280px; padding: 32px 24px; background: #020617; border-right: 1px solid rgba(255,255,255,0.1); display: flex; flexDirection: column; }
                .main-content { flex: 1; display: flex; flexDirection: column; height: 100vh; background: radial-gradient(circle at 50% 50%, #1e293b 0%, #0f172a 100%); }
                .dot-typing { position: relative; width: 6px; height: 6px; border-radius: 5px; background-color: #3b82f6; color: #3b82f6; animation: dotTyping 1.5s infinite linear; }
                
                @keyframes dotTyping {
                    0% { box-shadow: 12px 0 0 0 #3b82f6, 24px 0 0 0 #3b82f6, 36px 0 0 0 #3b82f6; }
                    33% { box-shadow: 12px -5px 0 0 #3b82f6, 24px 0 0 0 #3b82f6, 36px 0 0 0 #3b82f6; }
                    66% { box-shadow: 12px 0 0 0 #3b82f6, 24px -5px 0 0 #3b82f6, 36px 0 0 0 #3b82f6; }
                    100% { box-shadow: 12px 0 0 0 #3b82f6, 24px 0 0 0 #3b82f6, 36px -5px 0 0 #3b82f6; }
                }

                .animate-spin {
                    animation: spin 1s linear infinite;
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }

                /* Custom Scrollbar */
                ::-webkit-scrollbar { width: 6px; height: 6px; }
                ::-webkit-scrollbar-track { background: transparent; }
                ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); borderRadius: 10px; }
                ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
            `}</style>
        </div>
    );
};

const KpiCard = ({ label, value, color }) => (
    <div style={{ background: 'rgba(255,255,255,0.03)', padding: '24px', borderRadius: '16px', borderLeft: `4px solid ${color}` }}>
        <p style={{ color: '#94a3b8', fontSize: '13px', marginBottom: '8px' }}>{label}</p>
        <p style={{ fontSize: '24px', fontWeight: 'bold' }}>{value}</p>
    </div>
);

const SidebarItem = ({ icon, label, active, onClick }) => (
    <div onClick={onClick} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '12px', background: active ? 'rgba(59, 130, 246, 0.1)' : 'transparent', color: active ? '#3b82f6' : '#94a3b8', cursor: 'pointer', transition: 'all 0.2s' }}>
        {icon}
        <span style={{ fontWeight: active ? '600' : '400' }}>{label}</span>
    </div>
);

// --- Simple Line Chart ---
const LineChart = ({ data, labelKey, valKey }) => {
    const maxVal = Math.max(...data.map(d => d[valKey])) || 1;
    const points = data.map((d, i) => {
        const x = (i / (data.length - 1)) * 300;
        const y = 150 - (d[valKey] / maxVal) * 120;
        return `${x},${y}`;
    }).join(' ');
    return (
        <svg viewBox="0 0 300 150" style={{ width: '100%', height: '160px' }}>
            <polyline fill="none" stroke="#3b82f6" strokeWidth="3" points={points} />
            {data.map((d, i) => (
                <circle key={i} cx={(i / (data.length - 1)) * 300} cy={150 - (d[valKey] / maxVal) * 120} r="4" fill="#3b82f6" />
            ))}
        </svg>
    );
};

// --- Simple Smart Chart ---
const SmartChart = ({ data, query }) => {
    if (!data || data.length === 0) return null;

    // Use LineChart for trends
    if (query?.toLowerCase().includes('trend')) {
        const keys = Object.keys(data[0]);
        const labelKey = keys[0];
        const valKey = keys.find(k => typeof data[0][k] === 'number') || keys[1];
        return <LineChart data={data.slice(0, 20)} labelKey={labelKey} valKey={valKey} />;
    }

    // Default: Render as Table
    const headers = Object.keys(data[0]);

    return (
        <div style={{ overflowX: 'auto', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.1)', marginTop: '16px' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '13px', whiteSpace: 'nowrap' }}>
                <thead>
                    <tr style={{ background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                        {headers.map(h => (
                            <th key={h} style={{ padding: '12px 16px', textAlign: 'left', color: '#94a3b8', fontWeight: '600', textTransform: 'uppercase', fontSize: '11px', letterSpacing: '0.05em' }}>
                                {h.replace(/_/g, ' ')}
                            </th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.slice(0, 100).map((row, i) => (
                        <tr key={i} style={{ borderBottom: i === data.length - 1 ? 'none' : '1px solid rgba(255,255,255,0.05)' }}>
                            {headers.map(h => {
                                const val = row[h];
                                const isNum = typeof val === 'number';
                                return (
                                    <td key={h} style={{ padding: '12px 16px', color: '#e2e8f0' }}>
                                        {isNum ? val.toLocaleString(undefined, { maximumFractionDigits: 2 }) : val}
                                    </td>
                                );
                            })}
                        </tr>
                    ))}
                </tbody>
            </table>
            {data.length > 100 && (
                <div style={{ padding: '8px 16px', fontSize: '11px', color: '#64748b', textAlign: 'center', background: 'rgba(0,0,0,0.1)' }}>
                    Showing first 100 of {data.length} records
                </div>
            )}
        </div>
    );
};

export default App;
