"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { api } from "@/lib/api";
import { PlusIcon, WarningIcon, NoteIcon, SaveIcon } from "@/components/icons/Icons";

export default function AddPatient() {
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const [formData, setFormData] = useState({
        full_name: "",
        date_of_birth: "",
        gender: "",
        contact_info: "",
        insurance_info: "",
    });

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value,
        });
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const result = await api.createPatient(formData);
            if (result.success) {
                router.push("/");
            } else {
                setError(result.error || "Failed to create patient");
            }
        } catch (err) {
            setError("Failed to create patient. Make sure the backend is running.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <MainLayout title="Add New Patient">
            <div style={{ maxWidth: "600px", margin: "0 auto" }}>
                {/* Back Link */}
                <Link
                    href="/"
                    style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "0.5rem",
                        color: "var(--emerald-400)",
                        marginBottom: "1.5rem",
                    }}
                >
                    ← Back to Dashboard
                </Link>

                {/* Form Card */}
                <div className="card">
                    <div style={{ textAlign: "center", marginBottom: "2rem" }}>
                        <div
                            style={{
                                width: "64px",
                                height: "64px",
                                background: "var(--gradient-emerald)",
                                borderRadius: "16px",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                                fontSize: "2rem",
                                margin: "0 auto 1rem",
                            }}
                        >
                            <PlusIcon />
                        </div>
                        <h2 style={{ marginBottom: "0.5rem" }}>Register New Patient</h2>
                        <p style={{ color: "var(--text-muted)" }}>
                            Enter patient details to create a new record
                        </p>
                    </div>

                    {/* Error Message */}
                    {error && (
                        <div
                            style={{
                                background: "rgba(239, 68, 68, 0.1)",
                                border: "1px solid rgba(239, 68, 68, 0.3)",
                                borderRadius: "8px",
                                padding: "1rem",
                                marginBottom: "1.5rem",
                                color: "#f87171",
                            }}
                        >
                            <WarningIcon /> {error}
                        </div>
                    )}

                    {/* Info Box */}
                    <div
                        style={{
                            background: "rgba(16, 185, 129, 0.1)",
                            borderLeft: "4px solid var(--emerald-500)",
                            padding: "1rem",
                            borderRadius: "8px",
                            marginBottom: "1.5rem",
                        }}
                    >
                        <p style={{ color: "var(--text-secondary)", fontSize: "0.875rem" }}>
                            <strong style={{ color: "var(--emerald-400)" }}><NoteIcon className="inline mr-2"/> Note:</strong> A unique
                            Patient ID will be automatically generated when you save this record.
                        </p>
                    </div>

                    <form onSubmit={handleSubmit}>
                        {/* Full Name */}
                        <div className="form-group">
                            <label className="form-label">
                                Full Name<span className="required">*</span>
                            </label>
                            <input
                                type="text"
                                name="full_name"
                                className="input"
                                placeholder="Enter patient's full name"
                                value={formData.full_name}
                                onChange={handleChange}
                                required
                                autoFocus
                            />
                        </div>

                        {/* Date of Birth */}
                        <div className="form-group">
                            <label className="form-label">Date of Birth</label>
                            <input
                                type="date"
                                name="date_of_birth"
                                className="input"
                                value={formData.date_of_birth}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Gender */}
                        <div className="form-group">
                            <label className="form-label">Gender</label>
                            <select
                                name="gender"
                                className="input"
                                value={formData.gender}
                                onChange={handleChange}
                                style={{ cursor: "pointer" }}
                            >
                                <option value="">Select Gender</option>
                                <option value="Male">Male</option>
                                <option value="Female">Female</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>

                        {/* Contact Info */}
                        <div className="form-group">
                            <label className="form-label">Contact Information</label>
                            <input
                                type="text"
                                name="contact_info"
                                className="input"
                                placeholder="Phone number, email, or address"
                                value={formData.contact_info}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Insurance Info */}
                        <div className="form-group">
                            <label className="form-label">Insurance Information</label>
                            <input
                                type="text"
                                name="insurance_info"
                                className="input"
                                placeholder="Insurance provider and policy number"
                                value={formData.insurance_info}
                                onChange={handleChange}
                            />
                        </div>

                        {/* Buttons */}
                        <div style={{ display: "flex", gap: "1rem", marginTop: "2rem" }}>
                            <Link href="/" className="btn btn-secondary" style={{ flex: 1 }}>
                                Cancel
                            </Link>
                            <button
                                type="submit"
                                className="btn btn-primary"
                                style={{ flex: 1 }}
                                disabled={loading}
                            >
                                {loading ? (
                                    <>
                                        <span className="spinner" style={{ width: "20px", height: "20px" }}></span>
                                        Saving...
                                    </>
                                ) : (
                                    <><SaveIcon className="inline mr-2" /> Save Patient</>
                                )}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </MainLayout>
    );
}
