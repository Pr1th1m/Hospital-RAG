import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProtectedRoute from './components/ProtectedRoute';
import Landing from './pages/Landing';
import Chat from './pages/Chat';
import Explore from './pages/Explore';
import AdminLogin from './pages/AdminLogin';
import AdminDashboard from './pages/AdminDashboard';
import useChat from './hooks/useChat';
import './index.css';

function AppContent() {
  const location = useLocation();
  const isLanding = location.pathname === '/';

  const { messages, loading, inputRef, handleSend, handleNewChat } = useChat();

  // Dark mode
  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('theme') === 'dark';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    localStorage.setItem('theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode((prev) => !prev);

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
