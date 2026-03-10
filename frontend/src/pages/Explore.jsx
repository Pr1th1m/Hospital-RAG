import { useState, useEffect } from 'react';
import { getHospitals, getDepartments } from '../utils/api';

export default function Explore() {
    const [tab, setTab] = useState('hospitals');
    const [hospitals, setHospitals] = useState([]);
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchData();
    }, [tab]);

    const fetchData = async () => {
        setLoading(true);
        try {
            if (tab === 'hospitals') {
                const data = await getHospitals();
                setHospitals(data);
            } else if (tab === 'departments') {
                const data = await getDepartments();
                setDepartments(data);
            }
        } catch (err) {
            console.error('Failed to fetch:', err);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-container">
            <div className="page-header">
                <h1> Explore Healthcare Data</h1>
                <p>Browse hospitals, departments, and doctors in the system.</p>
            </div>

            <div className="tabs">
                {['hospitals', 'departments'].map((t) => (
                    <button
                        key={t}
                        className={`tab ${tab === t ? 'active' : ''}`}
                        onClick={() => setTab(t)}
                    >
                        {t === 'hospitals' ? ' Hospitals' : ' Departments'}
                    </button>
                ))}
            </div>

            {loading ? (
                <div className="spinner"></div>
            ) : (
                <div className="entity-grid">
                    {tab === 'hospitals' && hospitals.length === 0 && (
                        <div className="empty-state">
                            <div className="empty-icon"></div>
                            <p>No hospitals found. Add some from the Admin Dashboard.</p>
                        </div>
                    )}

                    {tab === 'hospitals' &&
                        hospitals.map((h, i) => (
                            <div key={i} className="card entity-card">
                                <div className="entity-card-header">
                                    <div className="entity-card-icon">
                                        
                                    </div>
                                    <div>
                                        <h3>{h.hospital_name}</h3>
                                        <p>{h.hospital_city}{h.hospital_area ? `, ${h.hospital_area}` : ''}</p>
                                    </div>
                                </div>
                                <div className="entity-detail">
                                    <span className="label">Type</span>
                                    <span className="value">{h.hospital_type}</span>
                                </div>
                                {h.ownership && (
                                    <div className="entity-detail">
                                        <span className="label">Ownership</span>
                                        <span className="value">{h.ownership}</span>
                                    </div>
                                )}
                                {h.total_beds != null && (
                                    <div className="entity-detail">
                                        <span className="label">Total Beds</span>
                                        <span className="value">{h.total_beds}</span>
                                    </div>
                                )}
                                {h.icu_beds != null && (
                                    <div className="entity-detail">
                                        <span className="label">ICU Beds</span>
                                        <span className="value">{h.icu_beds}</span>
                                    </div>
                                )}
                                <div className="entity-detail">
                                    <span className="label">Emergency</span>
                                    <span className="value">{h.emergency ? ' Yes' : ' No'}</span>
                                </div>
                                {h.accreditations && h.accreditations.length > 0 && (
                                    <div style={{ marginTop: 8 }}>
                                        {h.accreditations.map((a, j) => (
                                            <span key={j} className="tag">{a}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}

                    {tab === 'departments' && departments.length === 0 && (
                        <div className="empty-state">
                            <div className="empty-icon"></div>
                            <p>No departments found. Add some from the Admin Dashboard.</p>
                        </div>
                    )}

                    {tab === 'departments' &&
                        departments.map((d, i) => (
                            <div key={i} className="card entity-card">
                                <div className="entity-card-header">
                                    <div className="entity-card-icon">
                                        
                                    </div>
                                    <div>
                                        <h3>{d.department_name}</h3>
                                    </div>
                                </div>
                                <div className="entity-detail">
                                    <span className="label">ICU Support</span>
                                    <span className="value">{d.icu_support ? ' Yes' : ' No'}</span>
                                </div>
                                {d.services && d.services.length > 0 && (
                                    <div style={{ marginTop: 8 }}>
                                        {d.services.map((s, j) => (
                                            <span key={j} className="tag">{s}</span>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                </div>
            )}
        </div>
    );
}

