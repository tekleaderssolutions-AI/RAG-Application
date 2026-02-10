
import React, { useState, useRef, useEffect } from 'react';
import { Send, Database, FileText, BarChart3, Bot, User, Zap, AlertCircle, Wifi, WifiOff, RefreshCcw } from 'lucide-react';
import axios from 'axios';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import {
    LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    ScatterChart, Scatter, LabelList, ComposedChart
} from 'recharts';

// IMPORTANT: Update this URL whenever your ngrok session restarts in Colab
const BASE_URL = 'https://excellently-unstaunchable-fabiola.ngrok-free.dev';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d'];

const App = () => {
    const [activeTab, setActiveTab] = useState('chat');
    const [dashboardData, setDashboardData] = useState(null);
    const [reportingData, setReportingData] = useState([]);
    const [currentQueryData, setCurrentQueryData] = useState(null);
    const [vizTitle, setVizTitle] = useState('Revenue Insights');
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
            // Don't overwrite currentQueryData here to keep user's query active
            // if (!currentQueryData && res.data.top_plants) setCurrentQueryData(res.data.top_plants);
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
            setCurrentQueryData(null); // Reset dynamic view
        } catch (e) {
            console.error(e);
        }
    };

    const downloadPDF = async () => {
        const reportElement = document.getElementById('pdf-report-template');
        if (!reportElement) {
            alert('No report to download. Please ask a question first.');
            return;
        }

        try {
            const canvas = await html2canvas(reportElement, {
                scale: 2,
                backgroundColor: '#ffffff',
                logging: false,
                useCORS: true
            });

            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();
            const imgWidth = canvas.width;
            const imgHeight = canvas.height;
            const ratio = Math.min(pdfWidth / imgWidth, pdfHeight / imgHeight);
            const imgX = (pdfWidth - imgWidth * ratio) / 2;
            const imgY = 10;

            pdf.addImage(imgData, 'PNG', imgX, imgY, imgWidth * ratio, imgHeight * ratio);
            pdf.save(`SAP_COPA_Report_${new Date().toISOString().split('T')[0]}.pdf`);
        } catch (error) {
            console.error('PDF generation error:', error);
            alert('Failed to generate PDF. Please try again.');
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

            if (!response.body) throw new Error('ReadableStream not supported');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop();

                for (const line of lines) {
                    if (line.trim() === '') continue;
                    try {
                        const update = JSON.parse(line);
                        if (update.type === 'progress') {
                            setProgressStep(update.step);
                        } else if (update.type === 'result') {
                            const data = update.payload;

                            // Essential: Update Dashboard/Reporting with new data
                            if (data.data && Array.isArray(data.data)) {
                                setCurrentQueryData(data.data);
                                setVizTitle(prompt);
                            } else if (Array.isArray(data)) {
                                setCurrentQueryData(data);
                                setVizTitle(prompt);
                            }

                            if (data.error) {
                                setMessages(prev => [...prev, {
                                    role: 'ai',
                                    content: data.error,
                                    error: true
                                }]);
                            } else {
                                setMessages(prev => [...prev, {
                                    role: 'ai',
                                    content: data.summary,
                                    data: data.data // Store for chat SmartChart
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
                <div style={{ marginBottom: '40px', display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{ width: '40px', height: '40px', background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 20px rgba(59, 130, 246, 0.3)' }}>
                        <Zap size={24} color="#fff" fill="#fff" />
                    </div>
                    <div>
                        <h1 style={{ fontSize: '20px', fontWeight: 'bold', letterSpacing: '-0.5px' }}>SAP AI Agent</h1>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            {isConnected ? <Wifi size={12} color="#4ade80" /> : <WifiOff size={12} color="#ef4444" />}
                            <span style={{ fontSize: '11px', color: isConnected ? '#4ade80' : '#ef4444', fontWeight: '600' }}>
                                {isConnected ? 'SYSTEM ONLINE' : 'DISCONNECTED'}
                            </span>
                        </div>
                    </div>
                </div>

                <nav style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <SidebarItem icon={<Bot size={18} />} label="AI Copilot" active={activeTab === 'chat'} onClick={() => setActiveTab('chat')} />
                    <SidebarItem icon={<Database size={18} />} label="Reporting" active={activeTab === 'reports'} onClick={() => setActiveTab('reports')} />
                    <SidebarItem icon={<BarChart3 size={18} />} label="Dashboard" active={activeTab === 'dashboard'} onClick={() => setActiveTab('dashboard')} />
                </nav>
            </aside>

            <main className="main-content">
                {activeTab === 'chat' && (
                    <>
                        <div className="chat-window" style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                            {messages.map((m, i) => (
                                <div key={i} className={`message-wrapper ${m.role}`} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                                    <div className="bubble" style={{ maxWidth: '80%', padding: m.role === 'user' ? '16px' : '0 16px 16px 0', borderRadius: '16px', background: m.role === 'user' ? '#3b82f6' : 'transparent' }}>
                                        <div style={{ fontWeight: 'bold', fontSize: '12px', marginBottom: '8px', color: m.role === 'user' ? '#fff' : '#94a3b8' }}>
                                            {m.role === 'ai' ? 'SAP Assistant' : 'Finance Manager'}
                                        </div>
                                        <div style={{ fontSize: '15px', color: '#fff' }}>{m.content}</div>
                                        {m.data && (
                                            <div style={{ marginTop: '16px' }}>
                                                {/* Simple Table for Chat to avoid clutter */}
                                                <div style={{ overflowX: 'auto', background: 'rgba(255,255,255,0.02)', borderRadius: '12px', padding: '10px' }}>
                                                    <table style={{ width: '100%', fontSize: '12px', borderCollapse: 'collapse' }}>
                                                        <thead>
                                                            <tr style={{ borderBottom: '1px solid #334155' }}>
                                                                {Object.keys(m.data[0]).map(k => <th key={k} style={{ padding: '8px', textAlign: 'left', color: '#94a3b8' }}>{k}</th>)}
                                                            </tr>
                                                        </thead>
                                                        <tbody>
                                                            {m.data.slice(0, 5).map((r, idx) => (
                                                                <tr key={idx} style={{ borderBottom: '1px solid #1e293b' }}>
                                                                    {Object.values(r).map((v, c) => <td key={c} style={{ padding: '8px', color: '#e2e8f0' }}>{v}</td>)}
                                                                </tr>
                                                            ))}
                                                        </tbody>
                                                    </table>
                                                </div>
                                            </div>
                                        )}
                                        {m.error && <div style={{ color: '#ef4444', marginTop: '10px' }}><AlertCircle size={14} /> Error</div>}
                                    </div>
                                </div>
                            ))}
                            {loading && (
                                <div style={{ display: 'flex', gap: '4px', padding: '12px', background: 'rgba(255,255,255,0.05)', borderRadius: '16px', width: 'fit-content', marginLeft: '16px' }}>
                                    <div className="dot-typing" style={{ animationDelay: '0s' }}></div>
                                    <div className="dot-typing" style={{ animationDelay: '0.2s' }}></div>
                                    <div className="dot-typing" style={{ animationDelay: '0.4s' }}></div>
                                </div>
                            )}
                            <div ref={chatEndRef} />
                        </div>
                        <form className="input-area" onSubmit={handleSubmit} style={{ padding: '20px', display: 'flex', gap: '12px', background: 'rgba(0,0,0,0.2)' }}>
                            <input type="text" placeholder="Ask about revenue..." value={input} onChange={(e) => setInput(e.target.value)} style={{ flex: 1, background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', padding: '12px', borderRadius: '12px', color: '#fff' }} />
                            <button type="submit" disabled={loading} style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '12px 24px', borderRadius: '12px' }}><Send size={18} /></button>
                        </form>
                    </>
                )}

                {activeTab === 'dashboard' && (
                    <div className="dashboard-container" style={{ padding: '24px', overflowY: 'auto', height: '100%' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '32px' }}>
                            <div>
                                <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>{currentQueryData ? vizTitle : 'Executive Dashboard'}</h1>
                                <p style={{ color: '#94a3b8' }}>{currentQueryData ? 'Dynamic Visualization from Query' : 'Consolidated profitability metrics'}</p>
                            </div>
                            <button onClick={clearCache} style={{ background: 'rgba(255,255,255,0.05)', padding: '8px 16px', borderRadius: '8px', color: '#94a3b8', border: 'none', cursor: 'pointer' }}>Clear View</button>
                        </div>

                        {/* Render Charts if Data Exists */}
                        {(() => {
                            const chartData = currentQueryData || dashboardData?.top_plants;
                            if (!chartData || chartData.length === 0) return (
                                <div style={{ padding: '100px', textAlign: 'center', opacity: 0.5 }}>
                                    <BarChart3 size={48} style={{ marginBottom: '16px' }} />
                                    <p>Ask a question in AI Copilot to generate visualizations.</p>
                                </div>
                            );

                            const keys = Object.keys(chartData[0]);
                            const labelKey = keys.find(k => typeof chartData[0][k] === 'string') || keys[0];
                            const valKey = keys.find(k => typeof chartData[0][k] === 'number') || keys[1];

                            return (
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                                    <div style={{ background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '20px', height: '400px' }}>
                                        <ResponsiveContainer>
                                            <BarChart data={chartData} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                                                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                                <XAxis
                                                    dataKey={labelKey}
                                                    stroke="#94a3b8"
                                                    tick={{ fontSize: 11 }}
                                                    tickFormatter={(val) => val.length > 15 ? val.substring(0, 15) + '...' : val}
                                                />
                                                <YAxis
                                                    stroke="#94a3b8"
                                                    tick={{ fontSize: 11 }}
                                                    tickFormatter={(val) => val >= 1000000 ? (val / 1000000).toFixed(1) + 'M' : val >= 1000 ? (val / 1000).toFixed(1) + 'k' : val}
                                                    width={45}
                                                />
                                                <Tooltip
                                                    contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px' }}
                                                    formatter={(value) => [value.toLocaleString(), valKey]}
                                                />
                                                <Bar dataKey={valKey} fill="#3b82f6" radius={[4, 4, 0, 0]} barSize={40} />
                                            </BarChart>
                                        </ResponsiveContainer>
                                    </div>
                                    <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
                                        <div style={{ flex: 1, minWidth: '300px', height: '300px', background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '20px' }}>
                                            <ResponsiveContainer>
                                                <LineChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                                                    <XAxis
                                                        dataKey={labelKey}
                                                        stroke="#94a3b8"
                                                        tick={{ fontSize: 10 }}
                                                        tickFormatter={(val) => val.length > 10 ? val.substring(0, 8) + '...' : val}
                                                        interval="preserveStartEnd"
                                                    />
                                                    <YAxis
                                                        stroke="#94a3b8"
                                                        tick={{ fontSize: 10 }}
                                                        tickFormatter={(val) => val >= 1000000 ? (val / 1000000).toFixed(1) + 'M' : val >= 1000 ? (val / 1000).toFixed(1) + 'k' : val}
                                                        width={35}
                                                    />
                                                    <Tooltip
                                                        contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px', fontSize: '12px' }}
                                                        formatter={(value) => [value.toLocaleString(), valKey]}
                                                    />
                                                    <Line type="monotone" dataKey={valKey} stroke="#82ca9d" strokeWidth={3} dot={{ r: 3 }} activeDot={{ r: 5 }} />
                                                </LineChart>
                                            </ResponsiveContainer>
                                        </div>
                                        <div style={{ flex: 1, minWidth: '300px', height: '300px', background: 'rgba(255,255,255,0.02)', padding: '24px', borderRadius: '20px' }}>
                                            <ResponsiveContainer>
                                                <PieChart>
                                                    <Pie
                                                        data={chartData.slice(0, 10)}
                                                        dataKey={valKey}
                                                        nameKey={labelKey}
                                                        cx="40%"
                                                        cy="50%"
                                                        innerRadius={30}
                                                        outerRadius={60}
                                                        paddingAngle={2}
                                                    >
                                                        {chartData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                                                    </Pie>
                                                    <Tooltip contentStyle={{ background: '#1e293b', border: 'none' }} />
                                                    <Legend
                                                        layout="vertical"
                                                        verticalAlign="middle"
                                                        align="right"
                                                        wrapperStyle={{ fontSize: '11px', width: '40%' }}
                                                    />
                                                </PieChart>
                                            </ResponsiveContainer>
                                        </div>
                                    </div>
                                </div>
                            );
                        })()}
                    </div>
                )}

                {activeTab === 'reports' && (
                    <div className="reporting-container" style={{ padding: '24px', height: '100%', overflow: 'auto' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px' }}>
                            <div>
                                <h1 style={{ fontSize: '24px', fontWeight: 'bold' }}>PDF Report Generator</h1>
                                <p style={{ color: '#94a3b8' }}>Download professional reports</p>
                            </div>
                            {currentQueryData && currentQueryData.length > 0 && (
                                <button onClick={downloadPDF} style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '10px 20px', borderRadius: '10px', cursor: 'pointer', display: 'flex', items: 'center', gap: '8px' }}>
                                    <FileText size={18} /> Download PDF
                                </button>
                            )}
                        </div>

                        {currentQueryData && Array.isArray(currentQueryData) && currentQueryData.length > 0 && currentQueryData[0] ? (
                            <div id="pdf-report-template" style={{ background: '#fff', color: '#000', padding: '40px', borderRadius: '16px', maxWidth: '1000px', margin: '0 auto' }}>
                                <div style={{ borderBottom: '2px solid #3b82f6', paddingBottom: '20px', marginBottom: '30px' }}>
                                    <h1 style={{ fontSize: '28px', color: '#1e293b', fontWeight: 'bold' }}>SAP CO-PA Analytics Report</h1>
                                    <p style={{ color: '#64748b' }}>Generated on {new Date().toLocaleDateString()}</p>
                                </div>
                                <div style={{ background: '#f8fafc', padding: '20px', borderRadius: '12px', borderLeft: '4px solid #3b82f6', marginBottom: '30px' }}>
                                    <h3 style={{ fontSize: '14px', color: '#64748b', textTransform: 'uppercase' }}>Query</h3>
                                    <p style={{ fontSize: '18px', fontWeight: '500' }}>{vizTitle}</p>
                                </div>
                                <div style={{ marginBottom: '30px' }}>
                                    <h3 style={{ fontSize: '14px', color: '#64748b', textTransform: 'uppercase', marginBottom: '12px' }}>Data Summary</h3>
                                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                                        <thead>
                                            <tr style={{ background: '#f1f5f9' }}>
                                                {Object.keys(currentQueryData[0]).map(k => <th key={k} style={{ padding: '10px', textAlign: 'left', color: '#475569' }}>{k}</th>)}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {currentQueryData.slice(0, 10).map((r, i) => (
                                                <tr key={i} style={{ borderBottom: '1px solid #e2e8f0' }}>
                                                    {Object.values(r).map((v, j) => <td key={j} style={{ padding: '10px', color: '#334155' }}>{v}</td>)}
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                                {/* Visualizations for PDF */}
                                {(() => {
                                    const chartData = currentQueryData;
                                    const keys = Object.keys(chartData[0]);
                                    const labelKey = keys.find(k => typeof chartData[0][k] === 'string') || keys[0];
                                    const valKey = keys.find(k => typeof chartData[0][k] === 'number') || keys[1];
                                    return (
                                        <div style={{ marginBottom: '30px' }}>
                                            <h3 style={{ fontSize: '14px', color: '#64748b', textTransform: 'uppercase', marginBottom: '20px' }}>Visual Analysis</h3>

                                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
                                                {/* Horizontal Bar Chart */}
                                                <div style={{ flex: '1 1 100%', height: '350px', background: '#f8fafc', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                                                    <h4 style={{ fontSize: '12px', color: '#64748b', marginBottom: '15px', textTransform: 'uppercase', fontWeight: 'bold' }}>{valKey.replace(/_/g, ' ')} Distribution</h4>
                                                    <ResponsiveContainer>
                                                        <BarChart layout="vertical" data={chartData.slice(0, 10)} margin={{ left: 20, right: 30, top: 10, bottom: 10 }}>
                                                            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                                                            <XAxis type="number" tick={{ fontSize: 10 }} />
                                                            <YAxis type="category" dataKey={labelKey} tick={{ fontSize: 10 }} width={100} />
                                                            <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ fontSize: '12px' }} />
                                                            <Bar dataKey={valKey} fill="#3b82f6" radius={[0, 4, 4, 0]} barSize={24}>
                                                                <LabelList dataKey={valKey} position="right" fontSize={10} formatter={(v) => typeof v === 'number' ? v.toLocaleString() : v} />
                                                            </Bar>
                                                        </BarChart>
                                                    </ResponsiveContainer>
                                                </div>

                                                {/* Line Chart (Trend) */}
                                                <div style={{ flex: '1 1 45%', minWidth: '300px', height: '300px', background: '#f8fafc', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                                                    <h4 style={{ fontSize: '12px', color: '#64748b', marginBottom: '15px', textTransform: 'uppercase', fontWeight: 'bold' }}>Trend Analysis</h4>
                                                    <ResponsiveContainer>
                                                        <LineChart data={chartData.slice(0, 15)} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                                            <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                                            <XAxis dataKey={labelKey} tick={{ fontSize: 10 }} />
                                                            <YAxis tick={{ fontSize: 10 }} />
                                                            <Tooltip contentStyle={{ fontSize: '12px' }} />
                                                            <Line type="monotone" dataKey={valKey} stroke="#8884d8" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                                                        </LineChart>
                                                    </ResponsiveContainer>
                                                </div>

                                                {/* Pie Chart (Share) */}
                                                <div style={{ flex: '1 1 45%', minWidth: '300px', height: '300px', background: '#f8fafc', padding: '20px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                                                    <h4 style={{ fontSize: '12px', color: '#64748b', marginBottom: '15px', textTransform: 'uppercase', fontWeight: 'bold' }}>Share Distribution</h4>
                                                    <ResponsiveContainer>
                                                        <PieChart>
                                                            <Pie
                                                                data={chartData.slice(0, 10)}
                                                                dataKey={valKey}
                                                                nameKey={labelKey}
                                                                cx="35%"
                                                                cy="50%"
                                                                innerRadius={30}
                                                                outerRadius={60}
                                                                paddingAngle={2}
                                                            >
                                                                {chartData.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                                                            </Pie>
                                                            <Tooltip contentStyle={{ fontSize: '12px' }} />
                                                            <Legend
                                                                layout="vertical"
                                                                verticalAlign="middle"
                                                                align="right"
                                                                wrapperStyle={{ fontSize: '9px', width: '45%', lineHeight: '14px' }}
                                                            />
                                                        </PieChart>
                                                    </ResponsiveContainer>
                                                </div>
                                            </div>
                                        </div>
                                    );
                                })()}
                                <div style={{ textAlign: 'center', marginTop: '40px', borderTop: '1px solid #e2e8f0', paddingTop: '20px' }}>
                                    <p style={{ fontSize: '12px', color: '#94a3b8' }}>Confidential - Generated by SAP AI Agent</p>
                                </div>
                            </div>
                        ) : (
                            <div style={{ textAlign: 'center', padding: '60px', opacity: 0.5 }}>
                                <FileText size={48} style={{ marginBottom: '16px' }} />
                                <p>No report available. Ask a question in Chat first.</p>
                            </div>
                        )}
                    </div>
                )}
            </main>
            <style>{`
                .app-container { display: flex; height: 100vh; background: #0f172a; color: #fff; font-family: 'Inter', sans-serif; overflow: hidden; }
                .sidebar { width: 280px; padding: 32px 24px; background: #020617; border-right: 1px solid rgba(255,255,255,0.1); display: flex; flexDirection: column; }
                .main-content { flex: 1; display: flex; flexDirection: column; height: 100vh; background: radial-gradient(circle at 50% 50%, #1e293b 0%, #0f172a 100%); }
                .dot-typing { width: 8px; height: 8px; background: #3b82f6; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
                @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
                ::-webkit-scrollbar { width: 6px; }
                ::-webkit-scrollbar-track { background: transparent; }
                ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); borderRadius: 10px; }
            `}</style>
        </div>
    );
};

const SidebarItem = ({ icon, label, active, onClick }) => (
    <div onClick={onClick} style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '12px 16px', borderRadius: '12px', background: active ? 'rgba(59, 130, 246, 0.1)' : 'transparent', color: active ? '#3b82f6' : '#94a3b8', cursor: 'pointer', transition: 'all 0.2s' }}>
        {icon}
        <span style={{ fontWeight: active ? '600' : '400' }}>{label}</span>
    </div>
);

export default App;
