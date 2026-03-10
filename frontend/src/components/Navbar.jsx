import { useState } from 'react';
import { NavLink, useLocation } from 'react-router-dom';

export default function Navbar({ darkMode, toggleDarkMode }) {
    const [open, setOpen] = useState(false);
    const location = useLocation();
    const isAdmin = !!localStorage.getItem('admin_token');

    if (location.pathname === '/') return null;

    const links = [
        { to: '/chat', icon: 'CH', label: 'Chat' },
        ...(isAdmin
            ? [
                { to: '/explore', icon: 'EX', label: 'Explore' },
                { to: '/admin', icon: 'AD', label: 'Admin' },
            ]
            : []),
    ];

    return (
        <>
            <button className="sidebar-toggle" onClick={() => setOpen(!open)}>
                {open ? 'Close' : 'Menu'}
            </button>

            <div
                className={`sidebar-overlay ${open ? 'visible' : ''}`}
                onClick={() => setOpen(false)}
            />

            <aside className={`sidebar ${open ? 'open' : ''}`}>
                <div className="sidebar-logo">
                    <div className="logo-icon">MA</div>
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
                    <button className="nav-link theme-toggle" onClick={toggleDarkMode}>
                        <span className="nav-icon">{darkMode ? 'LT' : 'DK'}</span>
                        {darkMode ? 'Light Mode' : 'Dark Mode'}
                    </button>
                    {!isAdmin && (
                        <NavLink to="/admin/login" className="nav-link" onClick={() => setOpen(false)}>
                            <span className="nav-icon">IN</span>
                            Admin Login
                        </NavLink>
                    )}
                    <NavLink to="/" className="nav-link" onClick={() => setOpen(false)}>
                        <span className="nav-icon">HM</span>
                        Home
                    </NavLink>
                </div>
            </aside>
        </>
    );
}
