import React, { useState, useEffect } from 'react';
import { apiService } from './services/api';
import { AuthStatus, UserProfile } from './types/api';
import AuthSetup from './components/AuthSetup';
import Dashboard from './components/Dashboard';

function App() {
  const [authStatus, setAuthStatus] = useState<AuthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  const checkAuthStatus = async () => {
    setLoading(true);
    try {
      const status = await apiService.getAuthStatus();
      setAuthStatus(status);
    } catch (error) {
      console.error('Failed to check auth status:', error);
      setAuthStatus({ authenticated: false, profile: null });
    } finally {
      setLoading(false);
    }
  };

  const handleAuthComplete = () => {
    checkAuthStatus();
  };

  useEffect(() => {
    checkAuthStatus();
  }, []);

  if (loading) {
    return (
      <div className="container">
        <div className="header">
          <h1>🧠 Personal AI Psychologist</h1>
          <p>Analyzing your digital communication patterns...</p>
        </div>
        <div className="card loading">
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <div style={{ 
              width: '50px', 
              height: '50px', 
              border: '3px solid rgba(0, 245, 255, 0.3)', 
              borderTop: '3px solid #00f5ff',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite',
              margin: '0 auto 20px'
            }}></div>
            <p>Loading application...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container">
      <div className="header">
        <h1>🧠 Personal AI Psychologist</h1>
        <p>Discover insights about your communication patterns and personality through AI analysis</p>
      </div>

      {authStatus?.authenticated && authStatus.profile ? (
        <Dashboard profile={authStatus.profile} />
      ) : (
        <AuthSetup onAuthComplete={handleAuthComplete} />
      )}

      <div className="card" style={{ textAlign: 'center', marginTop: '40px' }}>
        <p style={{ fontSize: '0.9em', opacity: '0.7' }}>
          Your data is processed locally and securely. We respect your privacy.
        </p>
      </div>
    </div>
  );
}

export default App;