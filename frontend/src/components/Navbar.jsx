import { useState } from 'react';
import { NavLink, useLocation, Link } from 'react-router-dom';
import { MessageSquare, Compass, Settings, Sun, Moon, LogIn, Stethoscope, Menu, X } from 'lucide-react';

export default function Navbar({ darkMode, toggleDarkMode }) {
    const [open, setOpen] = useState(false);
    const location = useLocation();
    const isAdmin = !!localStorage.getItem('admin_token');

    if (location.pathname === '/') return null;

    const links = [
        { to: '/chat', icon: <MessageSquare />, label: 'Chat' },
        ...(isAdmin
            ? [
                { to: '/explore', icon: <Compass />, label: 'Explore' },
                { to: '/admin', icon: <Settings />, label: 'Admin' },
            ]
            : []),
    ];

    return (
        <>
            <button
                type="button"
                className="sidebar-toggle"
                onClick={() => setOpen(!open)}
                aria-label="Toggle menu"
                aria-expanded={open}
                aria-controls="sidebar-nav"
            >
                {open ? <X /> : <Menu />}
            </button>

            <div
                className={`sidebar-overlay ${open ? 'visible' : ''}`}
                onClick={() => setOpen(false)}
                aria-hidden="true"
            />

            <aside id="sidebar-nav" className={`sidebar ${open ? 'open' : ''}`} aria-label="Main">
                <Link to="/" className="sidebar-logo" aria-label="MedAssist home" onClick={() => setOpen(false)}>
                    <div className="logo-icon" aria-hidden="true"><Stethoscope /></div>
                    <h1>MedAssist</h1>
                </Link>

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
                    <button type="button" className="nav-link theme-toggle" onClick={toggleDarkMode}>
                        <span className="nav-icon">{darkMode ? <Sun /> : <Moon />}</span>
                        {darkMode ? 'Light Mode' : 'Dark Mode'}
                    </button>
                    {!isAdmin && (
                        <NavLink to="/admin/login" className="nav-link" onClick={() => setOpen(false)}>
                            <span className="nav-icon"><LogIn /></span>
                            Admin Login
                        </NavLink>
                    )}
                </div>
            </aside>
        </>
    );
}
