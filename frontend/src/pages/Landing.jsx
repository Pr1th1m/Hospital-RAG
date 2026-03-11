import { useNavigate, Link } from 'react-router-dom';
import { Stethoscope, MessageCircleQuestion, Search, CheckCircle, Sparkles, ArrowRight } from 'lucide-react';

export default function Landing({ darkMode, toggleDarkMode }) {
    const navigate = useNavigate();

    return (
        <div className="landing-page">
            <header className="landing-header">
                <nav className="landing-nav" aria-label="Main">
                    <Link to="/" className="landing-nav-logo" aria-label="MedAssist AI home">
                        <div className="ln-icon" aria-hidden="true"><Stethoscope /></div>
                        <span>MedAssist AI</span>
                    </Link>
                    <div className="landing-nav-actions">
                        <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={toggleDarkMode}
                            aria-label={darkMode ? 'Switch to light mode' : 'Switch to dark mode'}
                        >
                            {darkMode ? 'Light' : 'Dark'}
                        </button>
                        <button
                            type="button"
                            className="btn btn-ghost"
                            onClick={() => navigate('/admin/login')}
                        >
                            Admin
                        </button>
                        <button
                            type="button"
                            className="btn btn-primary"
                            onClick={() => navigate('/chat')}
                        >
                            Start Chat
                        </button>
                    </div>
                </nav>
            </header>

            <section className="hero" aria-labelledby="hero-heading">
                <div className="hero-content">
                    <div className="hero-badge">
                        <Sparkles aria-hidden="true" />
                        AI-Powered Healthcare Assistant
                    </div>
                    <h1 id="hero-heading">
                        Find the Right<br />
                        <span className="highlight">Healthcare, Instantly</span>
                    </h1>
                    <p>
                        Ask about hospitals, doctors, and departments in your area.
                        Get instant, accurate answers powered by intelligent search.
                    </p>
                    <div className="hero-buttons">
                        <button
                            type="button"
                            className="btn btn-primary btn-lg"
                            onClick={() => navigate('/chat')}
                        >
                            Start Chatting
                            <ArrowRight aria-hidden="true" />
                        </button>
                        <a href="#how-it-works" className="btn btn-ghost btn-lg">
                            Learn More
                        </a>
                    </div>
                    <div className="hero-stats" role="region" aria-label="Overview statistics">
                        <div className="hero-stat">
                            <div className="stat-value">500+</div>
                            <div className="stat-label">Hospitals</div>
                        </div>
                        <div className="hero-stat">
                            <div className="stat-value">2,000+</div>
                            <div className="stat-label">Doctors</div>
                        </div>
                        <div className="hero-stat">
                            <div className="stat-value">50+</div>
                            <div className="stat-label">Specialities</div>
                        </div>
                    </div>
                </div>
            </section>

            <section className="how-it-works" id="how-it-works" aria-labelledby="how-it-works-heading">
                <div className="section-header">
                    <h2 id="how-it-works-heading">How It Works</h2>
                    <p>Three simple steps to find the healthcare you need</p>
                </div>
                <div className="steps-grid">
                    <div className="step-card card">
                        <div className="step-number" aria-hidden="true">Step 01</div>
                        <div className="step-icon"><MessageCircleQuestion aria-hidden="true" /></div>
                        <h3>Ask Anything</h3>
                        <p>Type your question about hospitals, doctors, specialties, or departments.</p>
                    </div>
                    <div className="step-card card">
                        <div className="step-number" aria-hidden="true">Step 02</div>
                        <div className="step-icon"><Search aria-hidden="true" /></div>
                        <h3>Get Instant Answers</h3>
                        <p>Our AI searches across healthcare data to find the most relevant results for you.</p>
                    </div>
                    <div className="step-card card">
                        <div className="step-number" aria-hidden="true">Step 03</div>
                        <div className="step-icon"><CheckCircle aria-hidden="true" /></div>
                        <h3>Take Action</h3>
                        <p>Get detailed information and make informed decisions about your healthcare.</p>
                    </div>
                </div>
            </section>

            <section className="cta-section" aria-labelledby="cta-heading">
                <div className="cta-content">
                    <h2 id="cta-heading">Ready to find the care you need?</h2>
                    <p>Start a conversation with MedAssist and discover hospitals, doctors, and departments near you.</p>
                    <button
                        type="button"
                        className="btn btn-primary btn-lg"
                        onClick={() => navigate('/chat')}
                    >
                        Start Chatting Now
                        <ArrowRight aria-hidden="true" />
                    </button>
                </div>
            </section>

            <footer className="landing-footer">
                © 2026 MedAssist AI. Your Intelligent Healthcare Companion.
            </footer>
        </div>
    );
}
