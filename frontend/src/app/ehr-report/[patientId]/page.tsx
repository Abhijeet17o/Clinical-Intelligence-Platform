"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { api, Patient } from "@/lib/api";
import { WarningIcon, PrintIcon, HeartIcon, NoteIcon, HospitalIcon, MedicineIcon, LabIcon, VaccineIcon, ClipboardIcon } from "@/components/icons/Icons";

interface EHRData {
    vital_signs?: any[];
    clinical_notes?: any[];
    diagnoses?: any[];
    medications?: any[];
    lab_results?: any[];
    procedures?: any[];
    immunizations?: any[];
    prescriptions?: any[];
}

export default function EHRReportPage() {
    const params = useParams();
    const patientId = params.patientId as string;

    const [patient, setPatient] = useState<Patient | null>(null);
    const [ehrData, setEhrData] = useState<EHRData>({});
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadData();
    }, [patientId]);

    const loadData = async () => {
        try {
            setLoading(true);
            const patientData = await api.getPatient(patientId);
            setPatient(patientData);

            // Parse EHR data
            if (patientData.ehr_data) {
                try {
                    const parsed = JSON.parse(patientData.ehr_data);
                    setEhrData(parsed);
                } catch {
                    setEhrData({});
                }
            }
        } catch (err) {
            setError("Failed to load EHR data");
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <MainLayout title="Loading EHR Report...">
                <div className="empty-state">
                    <div className="spinner" style={{ margin: "0 auto" }}></div>
                </div>
            </MainLayout>
        );
    }

    if (error || !patient) {
        return (
            <MainLayout title="Error">
                <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
                    <p style={{ color: "var(--error)", display: "flex", gap: "0.5rem", alignItems: "center" }}><WarningIcon />{error || "Patient not found"}</p>
                    <Link href="/" className="btn btn-primary" style={{ marginTop: "1rem" }}>
                        ← Back to Dashboard
                    </Link>
                </div>
            </MainLayout>
        );
    }

    // Calculate age from DOB
    const calculateAge = (dob: string) => {
        if (!dob) return "N/A";
        const birth = new Date(dob);
        const today = new Date();
        let age = today.getFullYear() - birth.getFullYear();
        const m = today.getMonth() - birth.getMonth();
        if (m < 0 || (m === 0 && today.getDate() < birth.getDate())) age--;
        return `${age} years`;
    };

    return (
        <MainLayout
            title={`Electronic Health Record`}
            actions={
                <div style={{ display: "flex", gap: "1rem" }}>
                    <button onClick={() => window.print()} className="btn btn-primary">
                        <PrintIcon className="inline" /> Print
                    </button>
                    <Link href={`/appointment/${patientId}`} className="btn btn-secondary">
                        ← Back
                    </Link>
                </div>
            }
        >
            {/* Patient Header */}
            <div
                className="card"
                style={{
                    background: "var(--gradient-emerald)",
                    marginBottom: "2rem",
                    color: "white",
                }}
            >
                <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: "1.5rem" }}>
                    <div>
                        <div style={{ fontSize: "0.875rem", opacity: 0.9 }}>Patient Name</div>
                        <div style={{ fontSize: "1.25rem", fontWeight: 700 }}>{patient.full_name}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: "0.875rem", opacity: 0.9 }}>Patient ID</div>
                        <div style={{ fontWeight: 600 }}>{patient.patient_id}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: "0.875rem", opacity: 0.9 }}>Date of Birth</div>
                        <div>{patient.date_of_birth || "Not recorded"}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: "0.875rem", opacity: 0.9 }}>Age</div>
                        <div>{calculateAge(patient.date_of_birth || "")}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: "0.875rem", opacity: 0.9 }}>Gender</div>
                        <div>{patient.gender || "Not recorded"}</div>
                    </div>
                    <div>
                        <div style={{ fontSize: "0.875rem", opacity: 0.9 }}>Contact</div>
                        <div>{patient.contact_info || "Not recorded"}</div>
                    </div>
                </div>
            </div>

            {/* EHR Sections */}
            <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
                {/* Vital Signs */}
                <EHRSection title={<><HeartIcon className="inline mr-2" />Vital Signs</>} items={ehrData.vital_signs} columns={["date", "blood_pressure", "pulse_rate", "temperature", "weight"]} />

                {/* Clinical Notes */}
                <EHRSection title={<><NoteIcon className="inline mr-2" />Clinical Notes</>} items={ehrData.clinical_notes} columns={["date", "type", "subjective", "assessment"]} />

                {/* Diagnoses */}
                <EHRSection title={<><HospitalIcon className="inline mr-2" />Diagnoses & Problem List</>} items={ehrData.diagnoses} columns={["date", "condition", "status", "notes"]} />

                {/* Medications */}
                <EHRSection title={<><MedicineIcon className="inline mr-2" />Current Medications</>} items={ehrData.medications} columns={["name", "dosage", "frequency", "start_date", "status"]} />

                {/* Lab Results */}
                <EHRSection title={<><LabIcon className="inline mr-2" />Laboratory Results</>} items={ehrData.lab_results} columns={["date", "test_name", "result", "unit", "reference_range"]} />

                {/* Procedures */}
                <EHRSection title={<>Procedures</>} items={ehrData.procedures} columns={["date", "name", "performed_by", "notes"]} />

                {/* Immunizations */}
                <EHRSection title={<><VaccineIcon className="inline mr-2" />Immunization History</>} items={ehrData.immunizations} columns={["date", "vaccine", "dose", "administered_by"]} />

                {/* Prescription History */}
                <EHRSection title={<><ClipboardIcon className="inline mr-2" />Prescription History</>} items={ehrData.prescriptions} columns={["date", "medicines"]} />
            </div>
        </MainLayout>
    );
}

// EHR Section Component
function EHRSection({ title, items, columns }: { title: React.ReactNode; items?: any[]; columns: string[] }) {
    const hasData = items && items.length > 0;

    return (
        <div className="card" style={{ borderLeft: "4px solid var(--emerald-500)" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <h3 style={{ margin: 0 }}>{title}</h3>
                <button className="btn btn-outline" style={{ padding: "0.5rem 1rem", fontSize: "0.875rem" }}>
                    + Add
                </button>
            </div>

            {hasData ? (
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                {columns.map((col) => (
                                    <th key={col}>{col.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}</th>
                                ))}
                            </tr>
                        </thead>
                        <tbody>
                            {items.map((item, idx) => (
                                <tr key={idx}>
                                    {columns.map((col) => (
                                        <td key={col}>
                                            {Array.isArray(item[col])
                                                ? item[col].join(", ")
                                                : item[col] || "-"}
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            ) : (
                <div style={{ textAlign: "center", color: "var(--text-muted)", padding: "2rem", fontStyle: "italic" }}>
                    No records yet
                </div>
            )}
        </div>
    );
}
