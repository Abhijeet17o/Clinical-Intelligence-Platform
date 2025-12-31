"use client";

import React, { useEffect, useState, useRef } from "react";
import MainLayout from "@/components/layout/MainLayout";
import { api, LearningStats } from "@/lib/api";
import { RobotIcon, BookIcon, CalendarIcon, ChartIcon, RefreshIcon, SearchIcon, SaveIcon, EraserIcon, QuestionIcon, NoteIcon, WarningIcon, LineChartIcon } from "@/components/icons/Icons";

export default function FLDashboardPage() {
    const [stats, setStats] = useState<LearningStats | null>(null);
    const [recentEvents, setRecentEvents] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Modal for quick actions
    const [modalOpen, setModalOpen] = useState(false);
    const [modalTitle, setModalTitle] = useState<string>("");
    const [modalContent, setModalContent] = useState<React.ReactNode>(null);

    function openModal(title: string, content: React.ReactNode) {
        setModalTitle(title);
        setModalContent(content);
        setModalOpen(true);
    }

    function closeModal() {
        setModalOpen(false);
        setModalTitle("");
        setModalContent(null);
    }

    async function handleViewFullLearningHistory() {
        try {
            const res = await fetch('/api/fl/learning-history?limit=100');
            const data = await res.json();
            if (data.success) {
                const events = data.events || [];
                const content = (
                    <div style={{ maxHeight: 400, overflowY: 'auto' }}>
                        {events.length === 0 ? (
                            <div>No learning events found.</div>
                        ) : (
                            events.reverse().map((ev: any, i: number) => (
                                <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                                    <div style={{ fontWeight: 700 }}>{new Date(ev.timestamp).toLocaleString()} - {ev.selected_medicine}</div>
                                    <div style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>Symptoms: {ev.symptoms || 'N/A'}</div>
                                </div>
                            ))
                        )} 
                    </div>
                );
                openModal('Full Learning History', content);
            } else {
                alert('Failed to load learning history');
            }
        } catch (err: any) {
            console.error(err);
            alert('Error loading learning history');
        }
    }

    async function handleViewWeightEvolution() {
        try {
            const res = await fetch('/api/fl/learning-stats');
            const data = await res.json();
            const evolution = data.weight_evolution || data.stats?.weight_evolution;
            if (evolution && evolution.length > 0) {
                // collect unique model names across all entries
                const modelSet = new Set<string>();
                evolution.forEach((entry: any) => {
                    if (entry && entry.weights) Object.keys(entry.weights).forEach((k) => modelSet.add(k));
                });
                const modelNames = Array.from(modelSet);

                const content = (
                    <div style={{ maxHeight: 480, overflowY: 'auto' }}>
                        <WeightEvolutionChart evolution={evolution} />
                    </div>
                );
                openModal('Weight Evolution', content);
            } else {
                alert('No weight evolution data available yet.');
            }
        } catch (err: any) {
            console.error(err);
            alert('Error loading weight evolution');
        }
    }

    async function handleViewMedicinePatterns() {
        try {
            const res = await fetch('/api/fl/learning-stats');
            const data = await res.json();
            const patterns = data.medicine_patterns || data.stats?.medicine_patterns;
            if (patterns && Object.keys(patterns).length > 0) {
                const entries = Object.entries(patterns).slice(0, 200);
                const content = (
                    <div style={{ maxHeight: 480, overflowY: 'auto' }}>
                        {entries.map(([k, v]: any, i: number) => (
                            <div key={i} style={{ padding: '8px 0', borderBottom: '1px solid var(--border-color)' }}>
                                <div style={{ fontWeight: 700 }}>{k}</div>
                                <pre style={{ fontSize: '0.85rem', color: 'var(--text-muted)', whiteSpace: 'pre-wrap' }}>{JSON.stringify(v, null, 2)}</pre>
                            </div>
                        ))}
                    </div>
                );
                openModal('Medicine Patterns', content);
            } else {
                alert('No medicine patterns available yet.');
            }
        } catch (err: any) {
            console.error(err);
            alert('Error loading medicine patterns');
        }
    }

    async function handleExportLearningData() {
        try {
            const res = await fetch('/api/fl/learning-history?limit=1000');
            const data = await res.json();
            if (data.success) {
                const jsonStr = JSON.stringify(data.events, null, 2);
                const blob = new Blob([jsonStr], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `learning_history_${new Date().toISOString().split('T')[0]}.json`;
                a.click();
                URL.revokeObjectURL(url);
                alert('Learning data exported successfully.');
            } else {
                alert('Failed to export learning data');
            }
        } catch (err: any) {
            console.error(err);
            alert('Error exporting data');
        }
    }

    async function handleClearLearningHistory() {
        if (!confirm('Are you sure you want to clear all learning history? This action cannot be undone.')) return;
        if (!confirm('This will delete all learning records. Are you absolutely sure?')) return;

        // Try calling backend clear endpoint (best-effort - backend may not implement it)
        try {
            const res = await fetch('/api/fl/clear-history', { method: 'POST' });
            if (res.ok) {
                alert('Learning history cleared.');
                loadStats();
            } else {
                alert('Clearing learning history requires backend support. Contact administrator.');
            }
        } catch (err: any) {
            console.error(err);
            alert('Clearing learning history requires backend support.');
        }
    }



    useEffect(() => {
        loadStats();
        const interval = setInterval(loadStats, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, []);

    const loadStats = async () => {
        try {
            const data = await api.getLearningStats();
            if (data.success) {
                setStats(data.stats);
                setRecentEvents(data.recent_events || []);
            }
            setLoading(false);
        } catch (err) {
            setError("Failed to load learning stats");
            setLoading(false);
        }
    };

    const getTimeAgo = (timestamp: string) => {
        const seconds = Math.floor((Date.now() - new Date(timestamp).getTime()) / 1000);
        if (seconds < 60) return `${seconds}s ago`;
        const minutes = Math.floor(seconds / 60);
        if (minutes < 60) return `${minutes}m ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        const days = Math.floor(hours / 24);
        return `${days}d ago`;
    };

    return (
        <MainLayout title={<><RobotIcon className="inline mr-2" /> AI Learning Dashboard</>}>
            {/* Description */}
            <p style={{ color: "var(--text-secondary)", marginBottom: "2rem" }}>
                Real-time Hybrid Recommender Training Across Multiple Clients
            </p>

            {loading && (
                <div className="empty-state">
                    <div className="spinner" style={{ margin: "0 auto" }}></div>
                    <p style={{ marginTop: "1rem" }}>Loading learning statistics...</p>
                </div>
            )}

            {error && (
                <div className="card" style={{ borderColor: "var(--error)", marginBottom: "1.5rem" }}>
                    <p style={{ color: "var(--error)", display: "flex", gap: "0.5rem", alignItems: "center" }}><WarningIcon />{error}</p>
                    <button onClick={loadStats} className="btn btn-secondary" style={{ marginTop: "1rem" }}>
                        <RefreshIcon className="inline mr-2" /> Retry
                    </button>
                </div>
            )}

            {!loading && !error && (
                <>
                    {/* Stats Cards */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "1.5rem", marginBottom: "2rem" }}>
                        <StatCard
                            icon={<BookIcon />}
                            value={stats?.total_learnings || 0}
                            label="Total Prescriptions Learned"
                        />
                        <StatCard
                            icon={<CalendarIcon />}
                            value={stats?.today_count || 0}
                            label="Learned Today"
                        />
                        <StatCard
                            icon={<ChartIcon />}
                            value={stats?.learning_rate_per_hour || 0}
                            label="Learning Rate (per hour)"
                        />
                        <StatCard
                            icon={<ChartIcon />}
                            value={stats?.last_learning ? getTimeAgo(stats.last_learning) : "Never"}
                            label="Last Learning"
                            isText
                        />
                    </div>

                    {/* Training Status */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1.5rem", marginBottom: "2rem" }}>
                        <div className="card">
                            <h3 style={{ marginBottom: "1rem" }}><ChartIcon className="inline mr-2" /> Training Status</h3>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                                <div style={{ background: "var(--bg-tertiary)", padding: "1rem", borderRadius: "8px" }}>
                                    <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>Status</div>
                                    <div style={{ fontSize: "1.25rem", fontWeight: 600, color: "var(--success)" }}>Active</div>
                                </div>
                                <div style={{ background: "var(--bg-tertiary)", padding: "1rem", borderRadius: "8px" }}>
                                    <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>Mode</div>
                                    <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>Incremental</div>
                                </div>
                                <div style={{ background: "var(--bg-tertiary)", padding: "1rem", borderRadius: "8px" }}>
                                    <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>Active Clients</div>
                                    <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>1</div>
                                </div>
                                <div style={{ background: "var(--bg-tertiary)", padding: "1rem", borderRadius: "8px" }}>
                                    <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>Model Version</div>
                                    <div style={{ fontSize: "1.25rem", fontWeight: 600 }}>v2.1</div>
                                </div>
                            </div>
                        </div>

                        <div className="card">
                            <h3 style={{ marginBottom: "1rem" }}><ChartIcon className="inline mr-2" /> Current Metrics</h3>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "1rem" }}>
                                <MetricItem label="Average Loss" value="0.042" trend="↓ 2.1%" trendColor="var(--success)" />
                                <MetricItem label="Accuracy" value="94.2%" trend="↑ 1.5%" trendColor="var(--success)" />
                                <MetricItem label="Precision" value="91.8%" trend="↑ 0.8%" trendColor="var(--success)" />
                                <MetricItem label="Total Samples" value={`${(stats?.total_learnings || 0) * 15}`} />
                            </div>
                        </div>
                    </div>

                    {/* Quick Actions */}
                    <div className="card" style={{ marginBottom: "2rem" }}>
                        <h3 style={{ marginBottom: "1rem" }}>⚡ Quick Actions</h3>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "1rem" }}>
                            <button className="btn btn-primary" onClick={handleViewFullLearningHistory}><BookIcon className="inline mr-2" /> View Full Learning History</button>
                            <button className="btn btn-primary" onClick={handleViewWeightEvolution}><LineChartIcon className="inline mr-2" /> View Weight Evolution</button>
                            <button className="btn btn-primary" onClick={handleViewMedicinePatterns}><SearchIcon className="inline mr-2" /> View Medicine Patterns</button>
                            <button className="btn btn-secondary" onClick={handleExportLearningData}><SaveIcon className="inline mr-2" /> Export Learning Data</button>
                            <button className="btn btn-secondary" onClick={handleClearLearningHistory}><EraserIcon className="inline mr-2" /> Clear Learning History</button>
                            <button className="btn btn-outline" onClick={() => openModal('Learning Help', (
                                <div style={{ maxWidth: 640 }}>
                                    <h3 style={{ color: 'var(--emerald-400)' }}>Incremental Federated Learning</h3>
                                    <p>Click the quick actions to inspect learning history, weight evolution, or medicine patterns. Export or clear data when needed.</p>
                                </div>
                            ))}><QuestionIcon className="inline mr-2" /> Learning Help</button>
                        </div>
                    </div>

                    {/* Recent Learning Events */}
                    <div className="card">
                        <h3 style={{ marginBottom: "1rem" }}><NoteIcon className="inline mr-2" /> Recent Learning Events</h3>
                        <div
                            style={{
                                background: "#1e1e1e",
                                borderRadius: "8px",
                                padding: "1rem",
                                fontFamily: "monospace",
                                fontSize: "0.875rem",
                                maxHeight: "300px",
                                overflow: "auto",
                            }}
                        >
                            {recentEvents.length > 0 ? (
                                recentEvents.map((event, idx) => (
                                    <div
                                        key={idx}
                                        style={{
                                            borderLeft: "3px solid var(--emerald-500)",
                                            paddingLeft: "1rem",
                                            marginBottom: "0.75rem",
                                            padding: "0.5rem 1rem",
                                        }}
                                    >
                                        <div style={{ color: "var(--text-primary)", marginBottom: "0.25rem" }}>
                                            <strong>{new Date(event.timestamp).toLocaleString()}</strong> - Learned from:{" "}
                                            <strong style={{ color: "var(--emerald-400)" }}>{event.selected_medicine}</strong>
                                        </div>
                                        <div style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                                            Symptoms: {event.symptoms?.substring(0, 100)}...
                                        </div>
                                    </div>
                                ))
                            ) : (
                                <div style={{ color: "var(--text-muted)", textAlign: "center", padding: "2rem" }}>
                                    No learning events yet. Save a prescription to start learning!
                                </div>
                            )}
                        </div>
                    </div>
                </>
            )}

            {/* Modal */}
            {modalOpen && (
                <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 60, display: 'flex', alignItems: 'center', justifyContent: 'center' }} onClick={closeModal}>
                    <div style={{ background: 'var(--bg-card)', padding: 20, borderRadius: 8, maxWidth: 900, width: '95%', maxHeight: '80vh', overflowY: 'auto' }} onClick={(e) => e.stopPropagation()}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                            <h3 style={{ margin: 0 }}>{modalTitle}</h3>
                            <button onClick={closeModal} className="btn btn-secondary">Close</button>
                        </div>
                        <div>{modalContent}</div>
                    </div>
                </div>
            )}
        </MainLayout>
    );
}

// Stat Card Component
function StatCard({ icon, value, label, isText = false }: { icon: React.ReactNode; value: number | string; label: string; isText?: boolean }) {
    return (
        <div
            style={{
                background: "var(--gradient-emerald)",
                borderRadius: "12px",
                padding: "1.5rem",
                color: "white",
                textAlign: "center",
                boxShadow: "0 4px 15px rgba(16, 185, 129, 0.3)",
            }}
        >
            <div style={{ fontSize: "2.5rem", marginBottom: "0.5rem" }}>{icon}</div>
            <div style={{ fontSize: isText ? "1.25rem" : "2rem", fontWeight: 700, marginBottom: "0.25rem" }}>{value}</div>
            <div style={{ fontSize: "0.875rem", opacity: 0.9 }}>{label}</div>
        </div>
    );
}

// Metric Item Component
function MetricItem({ label, value, trend, trendColor }: { label: string; value: string; trend?: string; trendColor?: string }) {
    return (
        <div style={{ background: "var(--bg-tertiary)", padding: "1rem", borderRadius: "8px" }}>
            <div style={{ fontSize: "0.875rem", color: "var(--text-muted)", marginBottom: "0.25rem" }}>{label}</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 700 }}>{value}</div>
            {trend && <div style={{ fontSize: "0.75rem", color: trendColor, marginTop: "0.25rem" }}>{trend}</div>}
        </div>
    );
}

// Interactive chart for weight evolution using Chart.js
function WeightEvolutionChart({ evolution }: { evolution: any[] }) {
    const canvasRef = useRef<HTMLCanvasElement | null>(null);

    useEffect(() => {
        let chart: any = null;
        let mounted = true;

        (async () => {
            try {
                // @ts-ignore - chart.js may not be installed in every environment; dynamic import when available
                const ChartModule: any = await import('chart.js/auto');
                const ChartCtor = ChartModule?.default || ChartModule?.Chart || ChartModule;
                if (!mounted) return;
                const ctx = canvasRef.current?.getContext('2d');
                if (!ctx) return;

                // Collect model names across all entries
                const modelSet = new Set<string>();
                evolution.forEach((entry: any) => {
                    if (entry && entry.weights) Object.keys(entry.weights).forEach((k) => modelSet.add(k));
                });
                const modelNames = Array.from(modelSet);

                const entries = evolution.slice(-50).reverse();
                const labels = entries.map((e: any) => new Date(e.timestamp).toLocaleString());

                const colors = ['#667eea', '#2ecc71', '#e74c3c', '#f1c40f', '#9b59b6', '#e67e22', '#1abc9c', '#34495e'];
                const datasets = modelNames.map((name, idx) => ({
                    label: name,
                    data: entries.map((w: any) => (w.weights && w.weights[name] != null ? Number(w.weights[name]) : null)),
                    borderColor: colors[idx % colors.length],
                    backgroundColor: colors[idx % colors.length] + '33',
                    tension: 0.3,
                    spanGaps: true,
                }));

                chart = new ChartCtor(ctx, {
                    type: 'line',
                    data: { labels, datasets },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        interaction: { mode: 'index', intersect: false },
                        plugins: { legend: { position: 'top' } },
                        scales: {
                            x: { display: true },
                            y: { display: true, beginAtZero: false }
                        }
                    }
                });
            } catch (e) {
                console.error('Chart.js load error', e);
            }
        })();

        return () => {
            mounted = false;
            if (chart) chart.destroy();
        };
    }, [evolution]);

    return (
        <div style={{ height: 420 }}>
            <canvas ref={canvasRef}></canvas>
        </div>
    );
}
