"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import MainLayout from "@/components/layout/MainLayout";
import { api, Patient } from "@/lib/api";
import { PharmacyIcon, PlusIcon, UsersIcon, ClipboardIcon, LabIcon, WarningIcon, RefreshIcon, ChartIcon, CalendarIcon, PhoneIcon } from "@/components/icons/Icons";

export default function Dashboard() {
  const [patients, setPatients] = useState<Patient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPatients();
  }, []);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const data = await api.getPatients();
      setPatients(data);
    } catch (err) {
      console.error('Failed to load patients:', err);
      setError('Failed to load patients. Make sure the Flask backend is running.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <MainLayout
      title="Patient Dashboard"
      actions={
        <div style={{ display: "flex", gap: "1rem" }}>
          <Link href="/pharmacy" className="btn btn-secondary">
            <PharmacyIcon className="inline mr-2" /> Pharmacy
          </Link>
          <Link href="/patient/new" className="btn btn-primary">
            <PlusIcon className="inline mr-2" /> Add Patient
          </Link>
        </div>
      }
    >
      {/* Stats Section */}
      <div className="stats-grid" style={{ marginBottom: "2rem" }}>
        <div className="stat-card">
          <div className="stat-icon emerald"><UsersIcon /></div>
          <div>
            <div className="stat-value">{patients.length}</div>
            <div className="stat-label">Total Patients</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon emerald"><ClipboardIcon /></div>
          <div>
            <div className="stat-value">
              {patients.filter(p => p.ehr_data && p.ehr_data !== '{}').length}
            </div>
            <div className="stat-label">With EHR Data</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon emerald"><LabIcon /></div>
          <div>
            <div className="stat-value">Active</div>
            <div className="stat-label">AI Learning Status</div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="empty-state">
          <div className="spinner" style={{ margin: "0 auto" }}></div>
          <p style={{ marginTop: "1rem" }}>Loading patients...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="card" style={{ borderColor: "var(--error)", marginBottom: "1.5rem" }}>
          <p style={{ color: "var(--error)", display: "flex", gap: "0.5rem", alignItems: "center" }}><WarningIcon />{error}</p>
          <button onClick={loadPatients} className="btn btn-secondary" style={{ marginTop: "1rem" }}>
            <RefreshIcon className="inline mr-2" /> Retry
          </button>
        </div>
      )}

      {/* Patient Grid */}
      {!loading && !error && patients.length > 0 && (
        <>
          <div style={{ marginBottom: "1rem", color: "var(--text-secondary)", display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <ChartIcon /> Showing <strong style={{ color: "var(--emerald-400)" }}>{patients.length}</strong> registered patients
          </div>
          <div className="patient-grid">
            {patients.map((patient) => (
              <Link
                key={patient.patient_id}
                href={`/appointment/${patient.patient_id}`}
                style={{ textDecoration: "none" }}
              >
                <div className="patient-card">
                  <div className="patient-name">{patient.full_name}</div>
                  <div className="patient-id">ID: {patient.patient_id}</div>
                  <div className="patient-info-row">
                    <CalendarIcon />
                    <span>{patient.date_of_birth || "DOB not recorded"}</span>
                  </div>
                  {patient.contact_info && (
                    <div className="patient-info-row">
                      <PhoneIcon />
                      <span>{patient.contact_info}</span>
                    </div>
                  )}
                  <div style={{ marginTop: "1rem" }}>
                    <span className="badge badge-emerald">View Records →</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </>
      )}

      {/* Empty State */}
      {!loading && !error && patients.length === 0 && (
        <div className="empty-state">
          <div className="empty-state-icon"><UsersIcon /></div>
          <div className="empty-state-title">No Patients Found</div>
          <div className="empty-state-text">
            The patient database is currently empty.
          </div>
          <Link href="/patient/new" className="btn btn-primary" style={{ marginTop: "1.5rem" }}>
            <PlusIcon className="inline mr-2" /> Add Your First Patient
          </Link>
        </div>
      )}
    </MainLayout>
  );
}
