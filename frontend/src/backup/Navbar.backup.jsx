import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

export default function Navbar() {
    const [open, setOpen] = useState(false);
    const location = useLocation();
    const isAdmin = !!localStorage.getItem('admin_token');

    // Don't show sidebar on landing page
    if (location.pathname === '/') return null;

    const links = [
        { to: '/chat', icon: '💬', label: 'Chat' },
        ...(isAdmin
            ? [
                { to: '/explore', icon: '🏥', label: 'Explore' },
                { to: '/admin', icon: '⚙️', label: 'Admin' },
            ]
            : []),
    ];

    return (
        <>
            <button className="sidebar-toggle" onClick={() => setOpen(!open)}>
                {open ? '✕' : '☰'}
            </button>

            {/* Mobile overlay backdrop */}
            <div
                className={`sidebar-overlay ${open ? 'visible' : ''}`}
                onClick={() => setOpen(false)}
            />

            <aside className={`sidebar ${open ? 'open' : ''}`}>
                <div className="sidebar-logo">
                    <div className="logo-icon">🏥</div>
                    <h1>MedAssist</h1>
                </div>

                <nav className="sidebar-nav">
                    {links.map((link) => (
                        <NavLink
                            key={link.to}
                            to={link.to}
                            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
                            onClick={() => setOpen(false)}
                        >
                            <span className="nav-icon">{link.icon}</span>
                            {link.label}
                        </NavLink>
                    ))}
                </nav>

                <div className="sidebar-footer">
                    {!isAdmin && (
                        <NavLink to="/admin/login" className="nav-link" onClick={() => setOpen(false)}>
                            <span className="nav-icon">🔐</span>
                            Admin Login
                        </NavLink>
                    )}
                    <NavLink to="/" className="nav-link" onClick={() => setOpen(false)}>
                        <span className="nav-icon">🏠</span>
                        Home
                    </NavLink>
                </div>
            </aside>
        </>
    );
}
