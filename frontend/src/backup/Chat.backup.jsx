import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { transcribeAudio } from '../utils/api';

export default function Chat({ messages, loading, onSend, onNewChat, inputRef }) {
    const [input, setInput] = useState('');
    const [recording, setRecording] = useState(false);
    const [transcribing, setTranscribing] = useState(false);
    const [copiedIndex, setCopiedIndex] = useState(null);
    const messagesEndRef = useRef(null);
    const localInputRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const ref = inputRef || localInputRef;

    const suggestions = [
        { icon: '🏥', text: 'Find hospitals near me' },
        { icon: '👨‍⚕️', text: 'Search for cardiologists' },
        { icon: '🏢', text: 'Which departments does AIIMS have?' },
        { icon: '🔍', text: 'Best hospitals for emergency care' },
    ];

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    useEffect(() => {
        ref.current?.focus();
    }, []);

    useEffect(() => {
        if (!loading) {
            ref.current?.focus();
        }
    }, [loading]);

    // Auto-resize textarea
    const handleInputChange = (e) => {
        setInput(e.target.value);
        const textarea = e.target;
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    };

    const handleSend = () => {
        const text = input.trim();
        if (!text || loading) return;
        setInput('');
        // Reset textarea height
        if (ref.current) ref.current.style.height = 'auto';
        onSend(text);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleNewChat = () => {
        setInput('');
        if (ref.current) ref.current.style.height = 'auto';
        onNewChat();
        ref.current?.focus();
    };

    const handleSuggestionClick = (text) => {
        onSend(text);
    };

    const handleCopy = async (content, index) => {
        try {
            await navigator.clipboard.writeText(content);
            setCopiedIndex(index);
            setTimeout(() => setCopiedIndex(null), 2000);
        } catch (err) {
            console.error('Copy failed:', err);
        }
    };

    const formatTime = () => {
        return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    // ---- Voice Recording ----
    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) chunksRef.current.push(e.data);
            };

            mediaRecorder.onstop = async () => {
                stream.getTracks().forEach((t) => t.stop());
                const audioBlob = new Blob(chunksRef.current, { type: 'audio/webm' });
                setTranscribing(true);

                try {
                    const res = await transcribeAudio(audioBlob);
                    if (res.text) {
                        onSend(res.text);
                    }
                } catch (err) {
                    console.error('Transcription failed:', err);
                } finally {
                    setTranscribing(false);
                }
            };

            mediaRecorder.start();
            setRecording(true);
        } catch (err) {
            console.error('Microphone access denied:', err);
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
            mediaRecorderRef.current.stop();
        }
        setRecording(false);
    };

    const toggleRecording = () => {
        if (recording) {
            stopRecording();
        } else {
            startRecording();
        }
    };

    const isDisabled = loading || transcribing;

    return (
        <div className="chat-container">
            <div className="chat-header">
                <h2>💬 MedAssist Chat</h2>
                <button className="btn btn-ghost" onClick={handleNewChat}>
                    ✨ New Chat
                </button>
            </div>

            <div className="chat-messages">
                {messages.length === 0 && (
                    <div className="welcome-message">
                        <div className="welcome-icon">🏥</div>
                        <h3>Welcome to MedAssist</h3>
                        <p>
                            I can help you find hospitals, doctors, and departments.
                            Ask me anything about healthcare services in your area.
                        </p>

                        <div className="suggestion-cards">
                            {suggestions.map((s, i) => (
                                <button
                                    key={i}
                                    className="suggestion-card"
                                    onClick={() => handleSuggestionClick(s.text)}
                                >
                                    <span className="suggestion-icon">{s.icon}</span>
                                    <span>{s.text}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div key={i} className={`message message-${msg.role}`}>
                        <div className="message-avatar">
                            {msg.role === 'bot' ? '🤖' : '👤'}
                        </div>
                        <div className="message-bubble-wrapper">
                            <div className="message-bubble">
                                {msg.role === 'bot' ? (
                                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                                ) : (
                                    <p>{msg.content}</p>
                                )}
                            </div>
                            <div className="message-meta">
                                <span className="message-time">{msg.time || formatTime()}</span>
                                {msg.role === 'bot' && (
                                    <button
                                        className="copy-btn"
                                        onClick={() => handleCopy(msg.content, i)}
                                        title="Copy response"
                                    >
                                        {copiedIndex === i ? '✓ Copied' : '📋 Copy'}
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                ))}

                {(loading || transcribing) && (
                    <div className="message message-bot">
                        <div className="message-avatar">🤖</div>
                        <div className="message-bubble">
                            <div className="typing-indicator">
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>
                            <p className="typing-label">
                                {transcribing ? 'Transcribing your voice...' : 'MedAssist is thinking...'}
                            </p>
                        </div>
                    </div>
                )}

                <div ref={messagesEndRef} />
            </div>

            <div className="chat-input-area">
                <div className="chat-input-wrapper">
                    <textarea
                        ref={ref}
                        className="chat-input"
                        placeholder="Ask about hospitals, doctors, departments..."
                        value={input}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        rows={1}
                        disabled={isDisabled}
                    />
                    <button
                        className={`chat-mic-btn ${recording ? 'recording' : ''}`}
                        onClick={toggleRecording}
                        disabled={loading || transcribing}
                        title={recording ? 'Stop recording' : 'Start voice input'}
                    >
                        {recording ? '⏹' : '🎤'}
                    </button>
                    <button
                        className="chat-send-btn"
                        onClick={handleSend}
                        disabled={!input.trim() || isDisabled}
                    >
                        ➤
                    </button>
                </div>
                <div className="input-hint">
                    Press <kbd>Shift + Enter</kbd> for a new line
                </div>
            </div>
        </div>
    );
}
