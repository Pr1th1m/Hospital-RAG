import { useState, useEffect } from 'react';
import { addHospital, addDepartment, addDoctor, getHospitals, getDepartments } from '../utils/api';
import { ToastContainer, useToast } from '../components/Toast';
import { useNavigate } from 'react-router-dom';
import { Building2, LayoutGrid, UserPlus, LogOut, Plus } from 'lucide-react';

export default function AdminDashboard() {
    const [tab, setTab] = useState('hospital');
    const { toasts, addToast, removeToast } = useToast();
    const navigate = useNavigate();

    // Dropdown data
    const [hospitals, setHospitals] = useState([]);
    const [departments, setDepartments] = useState([]);

    useEffect(() => {
        loadDropdownData();
    }, []);

    const loadDropdownData = async () => {
        try {
            const h = await getHospitals();
            setHospitals(h);
            const d = await getDepartments();
            setDepartments(d);
        } catch (err) {
            console.error('Failed to load dropdown data');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('admin_token');
        navigate('/admin/login');
    };

    const tabItems = [
        { key: 'hospital', icon: <Building2 />, label: 'Hospital' },
        { key: 'department', icon: <LayoutGrid />, label: 'Department' },
        { key: 'doctor', icon: <UserPlus />, label: 'Doctor' },
    ];

    return (
        <div className="admin-container">
            <ToastContainer toasts={toasts} removeToast={removeToast} />

            <div className="page-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                    <h1>Admin Dashboard</h1>
                    <p>Manage hospitals, departments, and doctors.</p>
                </div>
                <button className="btn btn-ghost" onClick={handleLogout}>
                    <LogOut /> Logout
                </button>
            </div>

            <div className="tabs">
                {tabItems.map((t) => (
                    <button
                        key={t.key}
                        className={`tab ${tab === t.key ? 'active' : ''}`}
                        onClick={() => setTab(t.key)}
                    >
                        {t.icon} {t.label}
                    </button>
                ))}
            </div>

            {tab === 'hospital' && (
                <HospitalForm addToast={addToast} onSuccess={loadDropdownData} />
            )}
            {tab === 'department' && (
                <DepartmentForm addToast={addToast} hospitals={hospitals} onSuccess={loadDropdownData} />
            )}
            {tab === 'doctor' && (
                <DoctorForm addToast={addToast} hospitals={hospitals} departments={departments} />
            )}
        </div>
    );
}

function HospitalForm({ addToast, onSuccess }) {
    const [form, setForm] = useState({
        hospital_name: '',
        hospital_city: '',
        hospital_area: '',
        hospital_type: 'multispeciality',
        ownership: 'private',
        total_beds: '',
        icu_beds: '',
        emergency: false,
        accreditations: '',
    });
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                ...form,
                total_beds: form.total_beds ? parseInt(form.total_beds) : null,
                icu_beds: form.icu_beds ? parseInt(form.icu_beds) : null,
                hospital_area: form.hospital_area || null,
                ownership: form.ownership || null,
                accreditations: form.accreditations ? form.accreditations.split(',').map((s) => s.trim()) : [],
            };
            await addHospital(payload);
            addToast('Hospital added successfully!', 'success');
            onSuccess();
            setForm({
                hospital_name: '', hospital_city: '', hospital_area: '', hospital_type: 'multispeciality',
                ownership: 'private', total_beds: '', icu_beds: '', emergency: false, accreditations: '',
            });
        } catch (err) {
            addToast(err.message || 'Failed to add hospital', 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form className="admin-form card" onSubmit={handleSubmit}>
            <h3 className="form-section-title">Add Hospital</h3>
            <div className="form-row">
                <div className="input-group">
                    <label>Hospital Name *</label>
                    <input className="input-field" name="hospital_name" value={form.hospital_name} onChange={handleChange} required placeholder="e.g. Apollo Hospital" />
                </div>
                <div className="input-group">
                    <label>City *</label>
                    <input className="input-field" name="hospital_city" value={form.hospital_city} onChange={handleChange} required placeholder="e.g. Mumbai" />
                </div>
            </div>
            <div className="form-row">
                <div className="input-group">
                    <label>Area</label>
                    <input className="input-field" name="hospital_area" value={form.hospital_area} onChange={handleChange} placeholder="e.g. Andheri West" />
                </div>
                <div className="input-group">
                    <label>Type *</label>
                    <select className="input-field" name="hospital_type" value={form.hospital_type} onChange={handleChange}>
                        <option value="multispeciality">Multispeciality</option>
                        <option value="single speciality">Single Speciality</option>
                        <option value="super speciality">Super Speciality</option>
                    </select>
                </div>
            </div>
            <div className="form-row">
                <div className="input-group">
                    <label>Ownership</label>
                    <select className="input-field" name="ownership" value={form.ownership} onChange={handleChange}>
                        <option value="private">Private</option>
                        <option value="government">Government</option>
                        <option value="trust">Trust</option>
                    </select>
                </div>
                <div className="input-group">
                    <label>Accreditations (comma-separated)</label>
                    <input className="input-field" name="accreditations" value={form.accreditations} onChange={handleChange} placeholder="e.g. NABH, JCI" />
                </div>
            </div>
            <div className="form-row">
                <div className="input-group">
                    <label>Total Beds</label>
                    <input className="input-field" type="number" name="total_beds" value={form.total_beds} onChange={handleChange} min="0" placeholder="e.g. 500" />
                </div>
                <div className="input-group">
                    <label>ICU Beds</label>
                    <input className="input-field" type="number" name="icu_beds" value={form.icu_beds} onChange={handleChange} min="0" placeholder="e.g. 50" />
                </div>
            </div>
            <div className="input-group" style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                <input type="checkbox" name="emergency" checked={form.emergency} onChange={handleChange} id="emergency" />
                <label htmlFor="emergency" style={{ textTransform: 'none', fontSize: 14 }}>Has Emergency Services</label>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
                <Plus />
                {loading ? 'Adding...' : 'Add Hospital'}
            </button>
        </form>
    );
}

function DepartmentForm({ addToast, hospitals, onSuccess }) {
    const [form, setForm] = useState({
        hospital_id: '',
        department_name: '',
        services: '',
        icu_support: false,
    });
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        const { name, value, type, checked } = e.target;
        setForm((prev) => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                ...form,
                services: form.services ? form.services.split(',').map((s) => s.trim()) : [],
            };
            await addDepartment(payload);
            addToast('Department added successfully!', 'success');
            onSuccess();
            setForm({ hospital_id: '', department_name: '', services: '', icu_support: false });
        } catch (err) {
            addToast(err.message || 'Failed to add department', 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form className="admin-form card" onSubmit={handleSubmit}>
            <h3 className="form-section-title">Add Department</h3>
            <div className="input-group">
                <label>Hospital *</label>
                <select className="input-field" name="hospital_id" value={form.hospital_id} onChange={handleChange} required>
                    <option value="">Select a hospital...</option>
                    {hospitals.map((h) => (
                        <option key={h.hospital_id} value={h.hospital_id}>{h.hospital_name} — {h.hospital_city}</option>
                    ))}
                </select>
            </div>
            <div className="form-row">
                <div className="input-group">
                    <label>Department Name *</label>
                    <input className="input-field" name="department_name" value={form.department_name} onChange={handleChange} required placeholder="e.g. Cardiology" />
                </div>
                <div className="input-group">
                    <label>Services (comma-separated)</label>
                    <input className="input-field" name="services" value={form.services} onChange={handleChange} placeholder="e.g. ECG, Angioplasty" />
                </div>
            </div>
            <div className="input-group" style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
                <input type="checkbox" name="icu_support" checked={form.icu_support} onChange={handleChange} id="icu_support" />
                <label htmlFor="icu_support" style={{ textTransform: 'none', fontSize: 14 }}>ICU Support Available</label>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
                <Plus />
                {loading ? 'Adding...' : 'Add Department'}
            </button>
        </form>
    );
}

function DoctorForm({ addToast, hospitals, departments }) {
    const [form, setForm] = useState({
        hospital_id: '',
        department_id: '',
        doctor_name: '',
        doctor_speciality: '',
        doctor_experience: '',
        doctor_qualifications: '',
        languages: '',
        opd_timing: '',
    });
    const [loading, setLoading] = useState(false);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setForm((prev) => ({ ...prev, [name]: value }));
    };

    // Filter departments by selected hospital
    const filteredDepts = form.hospital_id
        ? departments.filter((d) => d.hospital_id === form.hospital_id)
        : departments;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            const payload = {
                ...form,
                doctor_experience: form.doctor_experience ? parseInt(form.doctor_experience) : null,
                doctor_qualifications: form.doctor_qualifications ? form.doctor_qualifications.split(',').map((s) => s.trim()) : [],
                languages: form.languages ? form.languages.split(',').map((s) => s.trim()) : [],
                opd_timing: form.opd_timing || null,
            };
            await addDoctor(payload);
            addToast('Doctor added successfully!', 'success');
            setForm({
                hospital_id: '', department_id: '', doctor_name: '', doctor_speciality: '',
                doctor_experience: '', doctor_qualifications: '', languages: '', opd_timing: '',
            });
        } catch (err) {
            addToast(err.message || 'Failed to add doctor', 'error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <form className="admin-form card" onSubmit={handleSubmit}>
            <h3 className="form-section-title">Add Doctor</h3>
            <div className="form-row">
                <div className="input-group">
                    <label>Hospital *</label>
                    <select className="input-field" name="hospital_id" value={form.hospital_id} onChange={handleChange} required>
                        <option value="">Select a hospital...</option>
                        {hospitals.map((h) => (
                            <option key={h.hospital_id} value={h.hospital_id}>{h.hospital_name}</option>
                        ))}
                    </select>
                </div>
                <div className="input-group">
                    <label>Department *</label>
                    <select className="input-field" name="department_id" value={form.department_id} onChange={handleChange} required>
                        <option value="">Select a department...</option>
                        {filteredDepts.map((d) => (
                            <option key={d.department_id} value={d.department_id}>{d.department_name}</option>
                        ))}
                    </select>
                </div>
            </div>
            <div className="form-row">
                <div className="input-group">
                    <label>Doctor Name *</label>
                    <input className="input-field" name="doctor_name" value={form.doctor_name} onChange={handleChange} required placeholder="e.g. Dr. Sharma" />
                </div>
                <div className="input-group">
                    <label>Speciality *</label>
                    <input className="input-field" name="doctor_speciality" value={form.doctor_speciality} onChange={handleChange} required placeholder="e.g. Cardiologist" />
                </div>
            </div>
            <div className="form-row">
                <div className="input-group">
                    <label>Experience (years)</label>
                    <input className="input-field" type="number" name="doctor_experience" value={form.doctor_experience} onChange={handleChange} min="0" placeholder="e.g. 15" />
                </div>
                <div className="input-group">
                    <label>OPD Timing</label>
                    <input className="input-field" name="opd_timing" value={form.opd_timing} onChange={handleChange} placeholder="e.g. Mon-Fri 9AM-5PM" />
                </div>
            </div>
            <div className="form-row">
                <div className="input-group">
                    <label>Qualifications (comma-separated)</label>
                    <input className="input-field" name="doctor_qualifications" value={form.doctor_qualifications} onChange={handleChange} placeholder="e.g. MBBS, MD, DM" />
                </div>
                <div className="input-group">
                    <label>Languages (comma-separated)</label>
                    <input className="input-field" name="languages" value={form.languages} onChange={handleChange} placeholder="e.g. English, Hindi" />
                </div>
            </div>
            <button type="submit" className="btn btn-primary" disabled={loading}>
                <Plus />
                {loading ? 'Adding...' : 'Add Doctor'}
            </button>
        </form>
    );
}
