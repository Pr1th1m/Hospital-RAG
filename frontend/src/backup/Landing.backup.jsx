import { useNavigate } from 'react-router-dom';

export default function Landing() {
    const navigate = useNavigate();

    const steps = [
        {
            number: '01',
            icon: '💬',
            title: 'Ask Anything',
            description: 'Type or speak your question about hospitals, doctors, or departments in plain language.',
        },
        {
            number: '02',
            icon: '🔍',
            title: 'Get Instant Answers',
            description: 'Receive accurate, up-to-date information sourced from our comprehensive medical database.',
        },
        {
            number: '03',
            icon: '✅',
            title: 'Take Action',
            description: 'Find the right doctor, locate the nearest hospital, or explore department details — all in one place.',
        },
    ];

    return (
        <div className="landing-page">
            {/* ─── Top Nav ─── */}
            <nav className="landing-nav">
                <div className="landing-nav-logo">
                    <div className="ln-icon">🏥</div>
                    <span>MedAssist</span>
                </div>
                <div className="landing-nav-actions">
                    <button className="btn btn-ghost" onClick={() => navigate('/admin/login')}>
                        Admin Login
                    </button>
                    <button className="btn btn-primary" onClick={() => navigate('/chat')}>
                        Open Chat
                    </button>
                </div>
            </nav>

            {/* ─── Hero ─── */}
            <section className="hero">
                <div className="hero-content">
                    <div className="hero-badge">
                        <span>✨</span>
                        AI-Powered Healthcare Assistant
                    </div>
                    <h1>
                        Find the Right<br />
                        <span className="highlight">Care, Instantly</span>
                    </h1>
                    <p>
                        Your intelligent healthcare companion. Ask about hospitals, doctors,
                        and departments using natural language — and get accurate answers in seconds.
                    </p>
                    <div className="hero-buttons">
                        <button className="btn btn-primary btn-lg" onClick={() => navigate('/chat')}>
                            💬 Start a Conversation
                        </button>
                        <button className="btn btn-ghost btn-lg" onClick={() => {
                            document.getElementById('how-it-works')?.scrollIntoView({ behavior: 'smooth' });
                        }}>
                            Learn More ↓
                        </button>
                    </div>
                </div>
            </section>

            {/* ─── How It Works ─── */}
            <section className="how-it-works" id="how-it-works">
                <div className="section-header">
                    <h2>How It Works</h2>
                    <p>Get the healthcare information you need in three simple steps.</p>
                </div>
                <div className="steps-grid">
                    {steps.map((step, i) => (
                        <div key={i} className="card step-card">
                            <div className="step-number">{step.number}</div>
                            <div className="step-icon">{step.icon}</div>
                            <h3>{step.title}</h3>
                            <p>{step.description}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* ─── CTA Section ─── */}
            <section className="cta-section">
                <div className="cta-content">
                    <h2>Ready to find the care you need?</h2>
                    <p>
                        Skip the endless searching. Just ask MedAssist and get instant,
                        reliable healthcare information.
                    </p>
                    <button className="btn btn-primary btn-lg" onClick={() => navigate('/chat')}>
                        Get Started — It's Free
                    </button>
                </div>
            </section>

            {/* ─── Footer ─── */}
            <footer className="landing-footer">
                © 2026 MedAssist · Your Intelligent Healthcare Companion
            </footer>
        </div>
    );
}
