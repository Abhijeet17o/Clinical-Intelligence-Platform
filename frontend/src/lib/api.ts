// Use direct backend URL to avoid Next.js proxy timeouts for heavy AI operations
// and enable direct communication now that CORS is enabled on Flask.
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:5000';

// Type definitions
export interface Patient {
    patient_id: string;
    full_name: string;
    date_of_birth?: string;
    gender?: string;
    contact_info?: string;
    insurance_info?: string;
    ehr_data?: string;
}

export interface Medicine {
    id: number;
    name: string;
    description: string;
    stock_level: number;
}

export interface LearningStats {
    total_learnings: number;
    today_count: number;
    learning_rate_per_hour: number;
    last_learning?: string;
}

// API Functions
export const api = {
    // Patient APIs
    async getPatients(): Promise<Patient[]> {
        const res = await fetch(`${API_BASE}/api/patients`);
        if (!res.ok) throw new Error('Failed to fetch patients');
        const data = await res.json();
        return data.patients || [];
    },

    async getPatient(patientId: string): Promise<Patient> {
        const res = await fetch(`${API_BASE}/api/patient/${patientId}`);
        if (!res.ok) throw new Error('Failed to fetch patient');
        return res.json();
    },

    async createPatient(data: Partial<Patient>): Promise<{ success: boolean; patient_id?: string; error?: string }> {
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => {
            if (value) formData.append(key, String(value));
        });

        const res = await fetch(`${API_BASE}/new_patient`, {
            method: 'POST',
            body: formData,
        });
        return res.json();
    },

    async updatePatient(patientId: string, data: Partial<Patient>): Promise<{ success: boolean; error?: string }> {
        const res = await fetch(`${API_BASE}/update_patient/${patientId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },

    // Medicine/Pharmacy APIs
    async getMedicines(): Promise<Medicine[]> {
        const res = await fetch(`${API_BASE}/api/medicines`);
        if (!res.ok) throw new Error('Failed to fetch medicines');
        const data = await res.json();
        return data.medicines || [];
    },

    async searchMedicine(query: string): Promise<Medicine[]> {
        const res = await fetch(`${API_BASE}/search_medicine?q=${encodeURIComponent(query)}`);
        if (!res.ok) throw new Error('Failed to search medicines');
        const data = await res.json();
        return data.results || [];
    },

    async addMedicine(data: Partial<Medicine>): Promise<{ success: boolean; error?: string }> {
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined) formData.append(key, String(value));
        });

        const res = await fetch(`${API_BASE}/add_medicine`, {
            method: 'POST',
            body: formData,
        });
        return res.json();
    },

    async updateMedicine(id: number, data: Partial<Medicine>): Promise<{ success: boolean; error?: string }> {
        const formData = new FormData();
        Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined) formData.append(key, String(value));
        });

        const res = await fetch(`${API_BASE}/update_medicine/${id}`, {
            method: 'POST',
            body: formData,
        });
        return res.json();
    },

    async deleteMedicine(id: number): Promise<{ success: boolean; error?: string }> {
        const res = await fetch(`${API_BASE}/delete_medicine/${id}`, {
            method: 'POST',
        });
        return res.json();
    },

    // Consultation APIs
    async processConsultation(patientId: string, formData: FormData): Promise<any> {
        // Use the V2 API which may process asynchronously and return 202 + consultation_id
        const res = await fetch(`${API_BASE}/api/process_consultation_v2/${patientId}`, {
            method: 'POST',
            body: formData,
        });

        // If server returned an immediate error (not accepted)
        if (!res.ok && res.status !== 202) {
            const text = await res.text();
            throw new Error(text || 'Failed to process consultation');
        }

        const data = await res.json();

        // If background processing, return early and let the client poll for updates
        if (data.processing) {
            return { success: true, processing: true, consultation_id: data.consultation_id };
        }

        // Immediate response with recommendations (fallback)
        return data;
    },

    async savePrescription(patientId: string, data: any): Promise<{ success: boolean; error?: string }> {
        const res = await fetch(`${API_BASE}/save_prescription/${patientId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });
        return res.json();
    },

    // EHR APIs
    async getEHRReport(patientId: string): Promise<any> {
        const res = await fetch(`${API_BASE}/api/ehr/${patientId}`);
        if (!res.ok) throw new Error('Failed to fetch EHR');
        return res.json();
    },

    async addEHRData(patientId: string, section: string, data: any): Promise<{ success: boolean; error?: string }> {
        const res = await fetch(`${API_BASE}/api/ehr/${patientId}/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ section, data }),
        });
        return res.json();
    },

    // Federated Learning APIs
    async getLearningStats(): Promise<{ success: boolean; stats: LearningStats; recent_events?: any[] }> {
        const res = await fetch(`${API_BASE}/api/fl/learning-stats`);
        if (!res.ok) throw new Error('Failed to fetch learning stats');
        return res.json();
    },

    async getLearningHistory(limit = 50): Promise<{ success: boolean; events: any[] }> {
        const res = await fetch(`${API_BASE}/api/fl/learning-history?limit=${limit}`);
        if (!res.ok) throw new Error('Failed to fetch learning history');
        return res.json();
    },

    async getEnsembleStatus(): Promise<any> {
        const res = await fetch(`${API_BASE}/api/ensemble/status`);
        if (!res.ok) throw new Error('Failed to fetch ensemble status');
        return res.json();
    },
};
