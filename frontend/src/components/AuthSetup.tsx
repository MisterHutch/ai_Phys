import React, { useState } from 'react';
import { apiService } from '../services/api';
import { OAuthConfig } from '../types/api';

interface AuthSetupProps {
  onAuthComplete: () => void;
}

const AuthSetup: React.FC<AuthSetupProps> = ({ onAuthComplete }) => {
  const [config, setConfig] = useState<OAuthConfig>({
    client_id: '',
    client_secret: '',
    project_id: '',
  });
  const [authUrl, setAuthUrl] = useState<string>('');
  const [authCode, setAuthCode] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState<'setup' | 'auth' | 'complete'>('setup');
  const [error, setError] = useState<string>('');

  const handleSetupOAuth = async () => {
    if (!config.client_id || !config.client_secret || !config.project_id) {
      setError('Please fill in all fields');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiService.setupOAuth(config);
      setAuthUrl(response.auth_url || '');
      setStep('auth');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to setup OAuth');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteAuth = async () => {
    if (!authCode) {
      setError('Please enter the authorization code');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await apiService.completeOAuth(authCode);
      if (response.success) {
        setStep('complete');
        setTimeout(() => {
          onAuthComplete();
        }, 2000);
      } else {
        setError('Authentication failed');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to complete authentication');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2>Gmail Setup</h2>
      
      {step === 'setup' && (
        <>
          <p>To get started, you'll need to set up Google Cloud Console credentials:</p>
          <ol style={{ margin: '16px 0', paddingLeft: '24px' }}>
            <li>Go to <a href="https://console.cloud.google.com" target="_blank" rel="noopener noreferrer">Google Cloud Console</a></li>
            <li>Create a new project or select existing one</li>
            <li>Enable the Gmail API</li>
            <li>Create OAuth 2.0 credentials</li>
            <li>Copy the credentials below:</li>
          </ol>
          
          <div style={{ marginTop: '20px' }}>
            <input
              type="text"
              placeholder="Client ID"
              value={config.client_id}
              onChange={(e) => setConfig({ ...config, client_id: e.target.value })}
              style={{ width: '100%', padding: '12px', margin: '8px 0', borderRadius: '4px', border: '1px solid #ddd' }}
            />
            <input
              type="text"
              placeholder="Client Secret"
              value={config.client_secret}
              onChange={(e) => setConfig({ ...config, client_secret: e.target.value })}
              style={{ width: '100%', padding: '12px', margin: '8px 0', borderRadius: '4px', border: '1px solid #ddd' }}
            />
            <input
              type="text"
              placeholder="Project ID"
              value={config.project_id}
              onChange={(e) => setConfig({ ...config, project_id: e.target.value })}
              style={{ width: '100%', padding: '12px', margin: '8px 0', borderRadius: '4px', border: '1px solid #ddd' }}
            />
            
            {error && <p style={{ color: 'red', margin: '10px 0' }}>{error}</p>}
            
            <button 
              className="btn" 
              onClick={handleSetupOAuth} 
              disabled={loading}
              style={{ marginTop: '16px' }}
            >
              {loading ? 'Setting up...' : 'Setup OAuth'}
            </button>
          </div>
        </>
      )}

      {step === 'auth' && (
        <>
          <h3>Authorize Access</h3>
          <p>Click the link below to authorize the application:</p>
          <a 
            href={authUrl} 
            target="_blank" 
            rel="noopener noreferrer"
            className="btn"
            style={{ display: 'inline-block', margin: '16px 0', textDecoration: 'none' }}
          >
            Authorize Gmail Access
          </a>
          
          <p>After authorizing, copy the authorization code here:</p>
          <input
            type="text"
            placeholder="Authorization Code"
            value={authCode}
            onChange={(e) => setAuthCode(e.target.value)}
            style={{ width: '100%', padding: '12px', margin: '8px 0', borderRadius: '4px', border: '1px solid #ddd' }}
          />
          
          {error && <p style={{ color: 'red', margin: '10px 0' }}>{error}</p>}
          
          <button 
            className="btn" 
            onClick={handleCompleteAuth} 
            disabled={loading || !authCode}
            style={{ marginTop: '16px' }}
          >
            {loading ? 'Completing...' : 'Complete Authentication'}
          </button>
        </>
      )}

      {step === 'complete' && (
        <div style={{ textAlign: 'center' }}>
          <h3 style={{ color: 'green' }}>✅ Authentication Successful!</h3>
          <p>Loading your dashboard...</p>
        </div>
      )}
    </div>
  );
};

export default AuthSetup;