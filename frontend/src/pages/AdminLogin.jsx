import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminLogin } from '../utils/api';
import { Shield, LogIn } from 'lucide-react';

export default function AdminLogin() {
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const res = await adminLogin(password);
            localStorage.setItem('admin_token', res.token);
            navigate('/admin');
        } catch (err) {
            setError('Invalid password. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="login-page">
            <div className="card login-card">
                <div className="login-icon"><Shield /></div>
                <h2>Admin Access</h2>
                <p className="subtitle">Enter your admin password to continue</p>

                {error && <p className="login-error">{error}</p>}

                <form onSubmit={handleLogin}>
                    <div className="input-group">
                        <label>Password</label>
                        <input
                            type="password"
                            className="input-field"
                            placeholder="Enter admin password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            autoFocus
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: 8 }}>
                        <LogIn />
                        {loading ? 'Verifying...' : 'Login'}
                    </button>
                </form>
            </div>
        </div>
    );
}
