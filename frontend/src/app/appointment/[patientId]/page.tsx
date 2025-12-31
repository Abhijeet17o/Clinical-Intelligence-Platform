"use client";

import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { api, Patient } from "@/lib/api";
import { RecordDotIcon, StopIcon, RobotIcon, ClipboardIcon, UsersIcon, SearchIcon, PlusIcon, SaveIcon, NoteIcon } from "@/components/icons/Icons";

type Recommendation = {
    name: string;
    description: string;
    similarity_score: number;
    final_score: number;
    voting?: Record<string, number>;
    explanation?: any;
    stock_level?: number;
};

// Helper: Progress Bar Component
const ProgressBar = ({ label, value, colorClass = "bg-emerald-500", formatValue }: { label: string, value: number, colorClass?: string, formatValue?: (v: number) => string }) => (
    <div style={{ marginBottom: "0.5rem" }}>
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.75rem", marginBottom: "0.25rem", color: "var(--text-secondary)" }}>
            <span>{label}</span>
            <span>{formatValue ? formatValue(value) : `${Math.round(value * 100)}%`}</span>
        </div>
        <div style={{ width: "100%", height: "6px", background: "rgba(255,255,255,0.1)", borderRadius: "3px", overflow: "hidden" }}>
            <div
                className={colorClass}
                style={{ width: `${Math.min(Math.max(value * 100, 0), 100)}%`, height: "100%", transition: "width 0.5s ease" }}
            ></div>
        </div>
    </div>
);

export default function AppointmentPage() {
    const params = useParams();
    const patientId = params.patientId as string;

    const [patient, setPatient] = useState<Patient | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Consultation state
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const [recordingStatus, setRecordingStatus] = useState("Ready to start consultation");
    const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
    const [prescriptionText, setPrescriptionText] = useState("");
    const [isProcessing, setIsProcessing] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // Audio recording refs
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const audioChunksRef = useRef<Blob[]>([]);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    // Search state
    const [searchQuery, setSearchQuery] = useState("");
    const [searchResults, setSearchResults] = useState<any[]>([]);

    useEffect(() => {
        loadPatient();
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [patientId]);

    const loadPatient = async () => {
        try {
            setLoading(true);
            const data = await api.getPatient(patientId);
            setPatient(data);
        } catch (err) {
            setError("Failed to load patient data");
        } finally {
            setLoading(false);
        }
    };

    const handleStartRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            audioChunksRef.current = [];

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    audioChunksRef.current.push(event.data);
                }
            };

            mediaRecorder.start();
            setIsRecording(true);
            setRecordingStatus("Recording... Speak clearly");
            setRecordingTime(0);

            timerRef.current = setInterval(() => {
                setRecordingTime((prev) => prev + 1);
            }, 1000);

        } catch (err) {
            console.error("Error accessing microphone:", err);
            alert("Error accessing microphone. Please ensure permissions are granted.");
        }
    };

    const handleStopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);

            if (timerRef.current) {
                clearInterval(timerRef.current);
                timerRef.current = null;
            }

            setRecordingStatus("Processing recording...");
            setIsProcessing(true);

            mediaRecorderRef.current.onstop = async () => {
                const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
                await processConsultation(audioBlob);
            };
        }
    };

    const processConsultation = async (audioBlob: Blob) => {
        try {
            const formData = new FormData();
            formData.append("audio", audioBlob, "consultation.wav");

            const result = await api.processConsultation(patientId, formData);

            if (result.success) {
                // If the backend accepted the job and is processing asynchronously
                if (result.processing) {
                    setRecordingStatus("⏳ Processing in background...");
                    setIsProcessing(true);

                    const pollStatus = async () => {
                        try {
                            const r = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000'}/api/consultation_status/${patientId}`);
                            if (!r.ok) throw new Error('Status fetch failed');
                            const js = await r.json();
                            if (js.success && js.consultation) {
                                if (!js.consultation.processing) {
                                    const recs = js.consultation.recommendations || [];
                                    setRecommendations(recs);
                                    setRecordingStatus("✓ Processing complete! Recommendations generated");
                                    loadPatient();
                                    setIsProcessing(false);
                                    return;
                                }
                            }
                        } catch (err) {
                            console.error('Polling error:', err);
                        }
                        setTimeout(pollStatus, 1500);
                    };

                    pollStatus();
                } else {
                    // Immediate response with recommendations
                    setRecommendations(result.recommendations || []);
                    setRecordingStatus("Consultation processed");
                    loadPatient();
                }
            } else {
                setRecordingStatus("Processing failed: " + (result.error || "Unknown error"));
                alert("Processing failed: " + (result.error || "Unknown error"));
                setIsProcessing(false);
            }
        } catch (err) {
            console.error("API Error:", err);
            setRecordingStatus("Network error processing consultation");
            alert("Failed to communicate with backend. Check if Flask server is running.");
            setIsProcessing(false);
        }
    };

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${secs.toString().padStart(2, "0")}`;
    };

    const handleAddToPrescription = (medicine: string) => {
        setPrescriptionText((prev) => {
            const lines = prev.split("\n").filter(Boolean);
            if (!lines.includes(medicine)) {
                return [...lines, medicine].join("\n");
            }
            return prev;
        });
    };

    const handleSearchMedicine = async () => {
        if (!searchQuery.trim()) return;
        try {
            const results = await api.searchMedicine(searchQuery);
            setSearchResults(results);
        } catch (err) {
            console.error("Search failed:", err);
        }
    };

    const handleSavePrescription = async () => {
        if (!prescriptionText.trim()) {
            alert("Please add medicines to the prescription");
            return;
        }

        setIsSaving(true);
        try {
            const medicines = prescriptionText.split("\n").filter(Boolean);
            await api.savePrescription(patientId, { prescription: prescriptionText, medicines });
            alert("Prescription saved successfully!");
            setPrescriptionText("");
        } catch (err) {
            alert("Failed to save prescription");
        } finally {
            setIsSaving(false);
        }
    };

    // Helper to parse explanation object or string
    const getExplanationData = (explanation: any) => {
        if (!explanation) return null;
        if (typeof explanation === 'string') {
            try {
                return JSON.parse(explanation);
            } catch {
                return null;
            }
        }
        return explanation;
    };

    if (loading) return <MainLayout title="Loading..."><div className="spinner" style={{ margin: "0 auto" }}></div></MainLayout>;
    if (error || !patient) return <MainLayout title="Error"><div className="card p-6 text-center text-error">{error || "Patient not found"}</div></MainLayout>;

    return (
        <MainLayout
            title={`Consultation - ${patient.full_name}`}
            actions={<Link href="/" className="btn btn-secondary">← Back to Dashboard</Link>}
        >
            {/* Grid Layout - Responsive: Stack on mobile, Side-by-side on desktop */}
            <div className="grid-layout-consultation">
                <style jsx>{`
          .grid-layout-consultation {
            display: grid;
            grid-template-columns: 1fr;
            gap: 1.5rem;
            max-width: 100%;
            overflow-x: hidden;
          }
          @media (min-width: 1024px) {
            .grid-layout-consultation {
              grid-template-columns: 320px 1fr;
            }
          }
          .animate-pulse {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
          }
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: .5; }
          }
        `}</style>

                {/* Left Column - Patient Info */}
                <div style={{ minWidth: 0 }}> {/* minWidth 0 prevents grid blowout */}
                    <div className="card" style={{ borderLeft: "4px solid var(--emerald-500)" }}>
                        <h3 style={{ marginBottom: "1.5rem", display: "flex", alignItems: "center", gap: "0.5rem" }}>
                            <UsersIcon /> Patient Info
                        </h3>
                        <div className="space-y-4">
                            <div><label className="text-sm text-muted">Full Name</label><div className="font-semibold text-lg">{patient.full_name}</div></div>
                            <div><label className="text-sm text-muted">ID</label><div>{patient.patient_id}</div></div>
                            <div><label className="text-sm text-muted">DOB</label><div>{patient.date_of_birth || "N/A"}</div></div>
                            <div><label className="text-sm text-muted">Gender</label><div>{patient.gender || "N/A"}</div></div>
                            <div><label className="text-sm text-muted">Insurance</label><div>{patient.insurance_info || "N/A"}</div></div>
                        </div>
                        <Link href={`/ehr-report/${patientId}`} className="btn btn-primary w-full mt-4"><ClipboardIcon className="inline mr-2" /> View Full EHR</Link>
                    </div>

                    {/* EHR Preview */}
                    <div className="card mt-4">
                        <h4 style={{ marginBottom: "1rem" }}><ClipboardIcon className="inline mr-2" />EHR Data Preview</h4>
                        <div className="bg-tertiary border border-dashed border-gray-700 rounded p-4 text-xs font-mono text-muted overflow-auto max-h-60">
                            {patient.ehr_data && patient.ehr_data !== "{}" ? (
                                <div style={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}>
                                    {(() => {
                                        try {
                                            const parsed = JSON.parse(patient.ehr_data);
                                            return Object.entries(parsed).map(([k, v]) => (
                                                <div key={k} className="mb-2">
                                                    <strong className="text-emerald-400 capitalize">{k.replace(/_/g, ' ')}:</strong>
                                                    <div className="pl-2">{typeof v === 'object' ? JSON.stringify(v).substring(0, 100) + '...' : String(v)}</div>
                                                </div>
                                            ));
                                        } catch {
                                            return patient.ehr_data;
                                        }
                                    })()}
                                </div>
                            ) : <div className="text-center italic">No data</div>}
                        </div>
                    </div>
                </div>

                {/* Right Column - Consultation */}
                <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem", minWidth: 0 }}>
                    {/* Recording Controls */}
                    <div className="card">
                        <h3 style={{ marginBottom: "1rem" }}><RecordDotIcon className="inline mr-2" /> Consultation Recording</h3>
                        <div className="flex items-center justify-between p-4 bg-emerald-900/10 border border-emerald-500/20 rounded-lg mb-4">
                            <span className="font-medium">Status: <span className="text-emerald-400">{recordingStatus}</span></span>
                            {isRecording && <span className="badge badge-error animate-pulse">{formatTime(recordingTime)}</span>}
                        </div>
                        {!isRecording && !isProcessing ? (
                            <button onClick={handleStartRecording} className="btn btn-primary w-full py-4 text-lg"><RecordDotIcon className="inline mr-2" /> Start Recording</button>
                        ) : isRecording ? (
                            <button onClick={handleStopRecording} className="btn btn-danger w-full py-4 text-lg"><StopIcon className="inline mr-2" /> Stop & Process</button>
                        ) : (
                            <button disabled className="btn btn-secondary w-full py-4 opacity-75 cursor-wait">
                                <span className="spinner w-5 h-5 mr-3 inline-block"></span> Processing...
                            </button>
                        )}
                    </div>

                    {/* AI Recommendations */}
                    <div className="card">
                        <h3 style={{ marginBottom: "1rem" }}><RobotIcon className="inline mr-2" /> AI Recommendations</h3>
                        {recommendations.length > 0 ? (
                            <div className="grid gap-4">
                                {recommendations.map((rec, idx) => {
                                    const explanationData = getExplanationData(rec.explanation);
                                    return (
                                        <div key={idx} className="bg-tertiary border border-gray-800 rounded-lg p-4 hover:border-emerald-500/30 transition-colors">
                                            <div className="flex justify-between items-start mb-3">
                                                <div>
                                                    <h4 className="text-xl font-bold text-emerald-400">{rec.name}</h4>
                                                    <p className="text-sm text-gray-400 mt-1">{rec.description}</p>
                                                </div>
                                                <div className="bg-emerald-900/30 text-emerald-400 px-3 py-1 rounded-full text-sm font-bold border border-emerald-500/20">
                                                    {(() => {
                                                        const score = rec.similarity_score !== undefined && rec.similarity_score !== null
                                                            ? rec.similarity_score
                                                            : Math.round((rec.final_score || 0) * 1000) / 10;
                                                        return `${score}% Match`;
                                                    })()}
                                                </div>
                                            </div>

                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                                                {/* Ensemble Voting Progress Bars */}
                                                {rec.voting && (
                                                    <div className="bg-black/20 p-3 rounded-lg">
                                                        <div className="text-xs text-gray-500 uppercase font-bold mb-2">Model Confidence Voting</div>
                                                        {Object.entries(rec.voting).map(([model, score]) => (
                                                            <ProgressBar
                                                                key={model}
                                                                label={model.replace(/_/g, ' ')}
                                                                value={score}
                                                                colorClass={model === 'collaborative' ? 'bg-purple-500' : model === 'knowledge' ? 'bg-blue-500' : 'bg-emerald-500'}
                                                            />
                                                        ))}
                                                    </div>
                                                )}

                                                {/* LIME Explanation Progress Bars */}
                                                {explanationData ? (
                                                    <div className="bg-black/20 p-3 rounded-lg">
                                                        <div className="text-xs text-gray-500 uppercase font-bold mb-2">Explainability (LIME Features)</div>

                                                        {/* Show Primary Reason specific text if available */}
                                                        {explanationData.primary_reason && (
                                                            <div className="text-xs text-emerald-300 mb-2 italic">"{explanationData.primary_reason}"</div>
                                                        )}

                                                        {/* Render Feature Importance Bars */}
                                                        {explanationData.feature_importance ? (
                                                            Object.entries(explanationData.feature_importance).map(([feature, score]: [string, any]) => (
                                                                <ProgressBar
                                                                    key={feature}
                                                                    label={feature}
                                                                    value={typeof score === 'number' ? score * 5 : 0.5} // Scale up LIME scores for visibility as they are often small
                                                                    formatValue={(v) => typeof score === 'number' ? score.toFixed(4) : String(score)}
                                                                    colorClass="bg-yellow-500"
                                                                />
                                                            ))
                                                        ) : (
                                                            <div className="text-xs text-gray-500">No feature details available</div>
                                                        )}
                                                    </div>
                                                ) : null}
                                            </div>

                                            {/* Natural Language Explanation if available */}
                                            {explanationData && explanationData.natural_language && (
                                                <div className="mt-3 text-sm text-gray-300 bg-gray-900/50 p-3 rounded border-l-2 border-emerald-500">
                                                    AI Reasoning: {explanationData.natural_language}
                                                </div>
                                            )}

                                            <button onClick={() => handleAddToPrescription(rec.name)} className="btn btn-primary w-full mt-4 py-2">
                                                <PlusIcon className="inline mr-2" /> Add to Prescription
                                            </button>
                                        </div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="text-center text-gray-500 py-8 border-2 border-dashed border-gray-800 rounded-lg">
                                Record a consultation to generate AI recommendations
                            </div>
                        )}
                    </div>

                    {/* Manual Search & Prescription - Side by Side on large screens */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Search */}
                        <div className="card">
                            <h3 className="mb-3 font-bold"><SearchIcon className="inline mr-2"/> Medicine Search</h3>
                            <div className="flex gap-2">
                                <input type="text" className="input flex-1" placeholder="Search..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyPress={(e) => e.key === "Enter" && handleSearchMedicine()} />
                                <button onClick={handleSearchMedicine} className="btn btn-primary">Go</button>
                            </div>
                            {searchResults.length > 0 && (
                                <div className="mt-3 divide-y divide-gray-800 border-t border-gray-800 max-h-40 overflow-auto">
                                    {searchResults.map((m, i) => (
                                        <div key={i} className="flex justify-between items-center py-2 text-sm">
                                            <span>{m.name}</span>
                                            <button onClick={() => handleAddToPrescription(m.name)} className="text-emerald-500 hover:text-emerald-400 font-bold"><PlusIcon /></button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Prescription Pad */}
                        <div className="card flex flex-col h-full">
                            <h3 className="mb-3 font-bold"><NoteIcon className="inline mr-2" /> Prescription</h3>
                            <textarea
                                className="input flex-1 font-mono text-sm resize-none mb-3"
                                placeholder="Prescription list..."
                                value={prescriptionText}
                                onChange={(e) => setPrescriptionText(e.target.value)}
                            />
                            <button onClick={handleSavePrescription} disabled={isSaving} className="btn btn-primary w-full">
                                {isSaving ? "Saving..." : <><SaveIcon className="inline mr-2"/> Save & Learn</>}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </MainLayout>
    );
}
