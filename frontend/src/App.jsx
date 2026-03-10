import { useState, useRef, useEffect } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Landing from './pages/Landing';
import Chat from './pages/Chat';
import Explore from './pages/Explore';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import './index.css';

const API_BASE = 'http://localhost:8000';

function AppContent() {
  const location = useLocation();
  const isLanding = location.pathname === '/';

  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(() => localStorage.getItem('chat_session_id'));
  const [loading, setLoading] = useState(false);
  const inputRef = useRef(null);

  // Dark mode
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('theme') === 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    localStorage.setItem('theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode((prev) => !prev);

  // ---- Send handler with streaming + fallback ----
  const handleSend = async (text) => {
    if (!text.trim() || loading) return;

    const currentSessionId = sessionId || crypto.randomUUID();
    if (!sessionId) {
      setSessionId(currentSessionId);
      localStorage.setItem('chat_session_id', currentSessionId);
    }

    const updatedUserMsgs = [...messages, { role: 'user', content: text }];
    setMessages(updatedUserMsgs);
    setLoading(true);

    // Add empty bot message for streaming
    setMessages([...updatedUserMsgs, { role: 'bot', content: '', streaming: true }]);

    let streamWorked = false;

    try {
      // Try streaming first
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: currentSessionId }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let fullBotContent = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const data = JSON.parse(jsonStr);
            if (data.token) {
              fullBotContent += data.token;
              streamWorked = true;
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: 'bot',
                  content: fullBotContent,
                  streaming: true
                };
                return updated;
              });
            }
            if (data.done) {
              if (data.session_id) {
                setSessionId(data.session_id);
                localStorage.setItem('chat_session_id', data.session_id);
              }
              setMessages(prev => {
                const updated = [...prev];
                updated[updated.length - 1] = { ...updated[updated.length - 1], streaming: false };
                return updated;
              });
            }
          } catch (e) { }
        }
      }

      // If stream ended but we got no tokens, fall through to fallback
      if (!streamWorked) {
        throw new Error('No tokens received from stream');
      }

    } catch (err) {
      console.error('Stream failed, trying fallback:', err);

      // Fallback to non-streaming /chat endpoint
      try {
        const fallbackRes = await fetch(`${API_BASE}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: text, session_id: currentSessionId }),
        });

        const data = await fallbackRes.json();
        if (data.session_id) {
          setSessionId(data.session_id);
          localStorage.setItem('chat_session_id', data.session_id);
        }
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: 'bot',
            content: data.answer || 'No response received.',
            streaming: false,
          };
          return updated;
        });
      } catch (fallbackErr) {
        console.error('Fallback also failed:', fallbackErr);
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: 'bot',
            content: 'Something went wrong. Please try again.',
            streaming: false,
          };
          return updated;
        });
      }
    } finally {
      setLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(null);
    localStorage.removeItem('chat_session_id');
  };

  return (
    <div className={isLanding ? '' : 'app-layout'}>
      <Navbar darkMode={darkMode} toggleDarkMode={toggleDarkMode} />
      <main className={isLanding ? '' : 'app-main'}>
        <Routes>
          <Route path="/" element={<Landing darkMode={darkMode} toggleDarkMode={toggleDarkMode} />} />
          <Route
            path="/chat"
            element={
              <Chat
                messages={messages}
                loading={loading}
                onSend={handleSend}
                onNewChat={handleNewChat}
                inputRef={inputRef}
              />
            }
          />
          <Route path="/explore" element={<ProtectedRoute><Explore /></ProtectedRoute>} />
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
        </Routes>
      </main>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;

