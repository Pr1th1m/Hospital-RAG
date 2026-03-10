const API_BASE = 'http://localhost:8000';

export async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('admin_token');
    const headers = {
        'Content-Type': 'application/json',
        ...(token && { Authorization: `Bearer ${token}` }),
        ...options.headers,
    };

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

// Chat
export const sendMessage = (message, sessionId) =>
    apiRequest('/chat', {
        method: 'POST',
        body: JSON.stringify({ message, session_id: sessionId }),
    });

// Admin
export const adminLogin = (password) =>
    apiRequest('/admin/login', {
        method: 'POST',
        body: JSON.stringify({ password }),
    });

// Hospitals
export const getHospitals = () => apiRequest('/get_hospitals');
export const addHospital = (data) =>
    apiRequest('/hospitals', { method: 'POST', body: JSON.stringify(data) });

// Departments
export const getDepartments = () => apiRequest('/get_departments');
export const addDepartment = (data) =>
    apiRequest('/departments', { method: 'POST', body: JSON.stringify(data) });

// Doctors
export const getDoctors = () => apiRequest('/get_doctors');
export const addDoctor = (data) =>
    apiRequest('/doctors', { method: 'POST', body: JSON.stringify(data) });

// Health
export const getHealth = () => apiRequest('/health');

// Transcribe audio
export const transcribeAudio = async (audioBlob) => {
    const formData = new FormData();
    formData.append('file', audioBlob, 'recording.webm');
    const response = await fetch(`${API_BASE}/transcribe`, {
        method: 'POST',
        body: formData,
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Transcription failed' }));
        throw new Error(error.detail || 'Transcription failed');
    }
    return response.json();
};
