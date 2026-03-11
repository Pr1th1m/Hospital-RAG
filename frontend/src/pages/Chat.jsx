import { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { transcribeAudio } from '../utils/api';
import { Bot, User, Stethoscope, Building2, UserCog, LayoutGrid, Siren, ThumbsUp, ThumbsDown, Copy, Check } from 'lucide-react';

export default function Chat({ messages, loading, onSend, onNewChat, inputRef }) {
    const [input, setInput] = useState('');
    const [recording, setRecording] = useState(false);
    const [copiedIdx, setCopiedIdx] = useState(null);
    const [reactions, setReactions] = useState({});
    const messagesEndRef = useRef(null);
    const mediaRecorder = useRef(null);
    const audioChunks = useRef([]);
    const textareaRef = inputRef || useRef(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading]);

    useEffect(() => {
        const ta = textareaRef.current;
        if (ta) {
            ta.style.height = 'auto';
            ta.style.height = Math.min(ta.scrollHeight, 120) + 'px';
        }
    }, [input]);

    const handleSend = () => {
        if (!input.trim()) return;
        onSend(input.trim());
        setInput('');
        if (textareaRef.current) textareaRef.current.style.height = 'auto';
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleSuggestion = (text) => {
        onSend(text);
    };

    const handleCopy = (text, idx) => {
        navigator.clipboard.writeText(text);
        setCopiedIdx(idx);
        setTimeout(() => setCopiedIdx(null), 2000);
    };

    const handleReaction = (idx, type) => {
        setReactions((prev) => ({
            ...prev,
            [idx]: prev[idx] === type ? null : type,
        }));
    };

    const formatTime = () => new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            mediaRecorder.current = new MediaRecorder(stream);
            audioChunks.current = [];
            mediaRecorder.current.ondataavailable = (e) => audioChunks.current.push(e.data);
            mediaRecorder.current.onstop = async () => {
                const blob = new Blob(audioChunks.current, { type: 'audio/webm' });
                stream.getTracks().forEach((t) => t.stop());
                try {
                    const res = await transcribeAudio(blob);
                    if (res.text) {
                        setInput(res.text);
                        textareaRef.current?.focus();
                    }
                } catch {
                    // ignore
                }
            };
            mediaRecorder.current.start();
            setRecording(true);
        } catch {
            // no mic access
        }
    };

    const stopRecording = () => {
        mediaRecorder.current?.stop();
        setRecording(false);
    };

    const suggestions = [
        { icon: <Building2 />, text: 'Find hospitals near me' },
        { icon: <UserCog />, text: 'Search for cardiologists' },
        { icon: <LayoutGrid />, text: 'Which departments does AIIMS have?' },
        { icon: <Siren />, text: 'Best hospitals for emergency care' },
    ];

    return (
        <div className="chat-container">
            <div className="chat-header">
                <div className="chat-header-left">
                    <div className="chat-header-avatar"><Bot /></div>
                    <div className="chat-header-info">
                        <h2>MedAssist AI</h2>
                        <div className="chat-header-status">
                            <span className="status-dot" />
                            Online
                        </div>
                    </div>
                </div>
                <button className="btn btn-ghost" onClick={onNewChat} style={{ fontSize: '13px' }}>
                    New Chat
                </button>
            </div>

            <div className="chat-messages">
                {messages.length === 0 && !loading ? (
                    <div className="welcome-message">
                        <div className="welcome-icon"><Stethoscope /></div>
                        <h3>Welcome to MedAssist AI</h3>
                        <p>
                            I can help you find hospitals, doctors, and departments.
                            Ask me anything about healthcare services in your area.
                        </p>
                        <div className="suggestion-cards">
                            {suggestions.map((s, i) => (
                                <button key={i} className="suggestion-card" onClick={() => handleSuggestion(s.text)}>
                                    <span className="suggestion-icon">{s.icon}</span>
                                    {s.text}
                                </button>
                            ))}
                        </div>
                    </div>
                ) : (
                    <>
                        {messages.map((msg, i) => (
                            <div key={i} className={`message message-${msg.role === 'user' ? 'user' : 'bot'}`}>
                                <div className="message-avatar">
                                    {msg.role === 'user' ? <User /> : <Bot />}
                                </div>
                                <div className="message-bubble-wrapper">
                                    <div className="message-bubble">
                                        {msg.role === 'user' ? (
                                            msg.content
                                        ) : (
                                            <>
                                                <ReactMarkdown>{msg.content}</ReactMarkdown>
                                                {msg.streaming && <span className="streaming-cursor" />}
                                            </>
                                        )}
                                    </div>
                                    <div className="message-meta">
                                        <span className="message-time">{formatTime()}</span>
                                        {msg.role === 'bot' && !msg.streaming && msg.content && (
                                            <>
                                                <button className="copy-btn" onClick={() => handleCopy(msg.content, i)} title="Copy">
                                                    {copiedIdx === i ? <Check /> : <Copy />}
                                                </button>
                                                <button
                                                    className={`reaction-btn ${reactions[i] === 'up' ? 'active' : ''}`}
                                                    onClick={() => handleReaction(i, 'up')}
                                                    title="Helpful"
                                                >
                                                    <ThumbsUp />
                                                </button>
                                                <button
                                                    className={`reaction-btn ${reactions[i] === 'down' ? 'active' : ''}`}
                                                    onClick={() => handleReaction(i, 'down')}
                                                    title="Not helpful"
                                                >
                                                    <ThumbsDown />
                                                </button>
                                            </>
                                        )}
                                    </div>
                                </div>
                            </div>
                        ))}

                        {loading && messages[messages.length - 1]?.role !== 'bot' && (
                            <div className="message message-bot">
                                <div className="message-avatar"><Bot /></div>
                                <div className="message-bubble-wrapper">
                                    <div className="message-bubble">
                                        <div className="typing-indicator">
                                            <span /><span /><span />
                                        </div>
                                        <div className="typing-label">MedAssist is thinking...</div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
                <div className="chat-input-wrapper">
                    <textarea
                        ref={textareaRef}
                        className="chat-input"
                        rows="1"
                        placeholder="Ask about hospitals, doctors, departments..."
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={loading}
                    />
                    <button
                        className={`chat-mic-btn ${recording ? 'recording' : ''}`}
                        onClick={recording ? stopRecording : startRecording}
                        disabled={loading}
                        title={recording ? 'Stop recording' : 'Voice input'}
                    >
                        {recording ? (
                            <svg viewBox="0 0 24 24" aria-hidden="true">
                                <rect x="7" y="7" width="10" height="10" rx="2" />
                            </svg>
                        ) : (
                            <svg viewBox="0 0 24 24" aria-hidden="true">
                                <path d="M12 15a3 3 0 0 0 3-3V7a3 3 0 1 0-6 0v5a3 3 0 0 0 3 3Z" />
                                <path d="M19 12a7 7 0 0 1-14 0" />
                                <path d="M12 19v3" />
                            </svg>
                        )}
                    </button>
                    <button
                        className="chat-send-btn"
                        onClick={handleSend}
                        disabled={!input.trim() || loading}
                        title="Send message"
                    >
                        <svg viewBox="0 0 24 24" aria-hidden="true">
                            <path d="M12 19V6" />
                            <path d="m6 12 6-6 6 6" />
                        </svg>
                    </button>
                </div>
                <div className="input-hint">
                    Press <kbd>Shift</kbd> + <kbd>Enter</kbd> for a new line
                </div>
            </div>
        </div>
    );
}
