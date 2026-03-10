import { useNavigate } from 'react-router-dom';

export default function Landing({ darkMode, toggleDarkMode }) {
    const navigate = useNavigate();

    return (
        <div className="landing-page">
            <nav className="landing-nav">
                <div className="landing-nav-logo">
                    <div className="ln-icon">MA</div>
                    <span>MedAssist AI</span>
                </div>
                <div className="landing-nav-actions">
                    <button className="btn btn-ghost" onClick={toggleDarkMode} title={darkMode ? 'Light Mode' : 'Dark Mode'}>
                        {darkMode ? 'Light' : 'Dark'}
                    </button>
                    <button className="btn btn-ghost" onClick={() => navigate('/admin/login')}>
                        Admin
                    </button>
                    <button className="btn btn-primary" onClick={() => navigate('/chat')}>
                        Start Chat
                    </button>
                </div>
            </nav>

            <section className="hero">
                <div className="hero-content">
                    <div className="hero-badge">AI-Powered Healthcare Assistant</div>
                    <h1>
                        Find the Right<br />
                        <span className="highlight">Healthcare, Instantly</span>
                    </h1>
                    <p>
                        Ask about hospitals, doctors, and departments in your area.
                        Get instant, accurate answers powered by intelligent search.
                    </p>
                    <div className="hero-buttons">
                        <button className="btn btn-primary btn-lg" onClick={() => navigate('/chat')}>
                            Start Chatting
                        </button>
                        <a href="#how-it-works" className="btn btn-ghost btn-lg">
                            Learn More
                        </a>
                    </div>
                </div>
            </section>

            <section className="how-it-works" id="how-it-works">
                <div className="section-header">
                    <h2>How It Works</h2>
                    <p>Three simple steps to find the healthcare you need</p>
                </div>
                <div className="steps-grid">
                    <div className="step-card card">
                        <div className="step-number">Step 01</div>
                        <div className="step-icon">Q</div>
                        <h3>Ask Anything</h3>
                        <p>Type your question about hospitals, doctors, specialties, or departments.</p>
                    </div>
                    <div className="step-card card">
                        <div className="step-number">Step 02</div>
                        <div className="step-icon">S</div>
                        <h3>Get Instant Answers</h3>
                        <p>Our AI searches across healthcare data to find the most relevant results for you.</p>
                    </div>
                    <div className="step-card card">
                        <div className="step-number">Step 03</div>
                        <div className="step-icon">A</div>
                        <h3>Take Action</h3>
                        <p>Get detailed information and make informed decisions about your healthcare.</p>
                    </div>
                </div>
            </section>

            <section className="cta-section">
                <div className="cta-content">
                    <h2>Ready to find the care you need?</h2>
                    <p>Start a conversation with MedAssist and discover hospitals, doctors, and departments near you.</p>
                    <button className="btn btn-primary btn-lg" onClick={() => navigate('/chat')}>
                        Start Chatting Now
                    </button>
                </div>
            </section>

            <footer className="landing-footer">
                Copyright 2026 MedAssist AI. Your Intelligent Healthcare Companion.
            </footer>
        </div>
    );
}
