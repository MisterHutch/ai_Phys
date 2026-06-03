import React, { useState, useEffect } from 'react';
import { apiService } from '../services/api';
import { EmailStats, UserProfile } from '../types/api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface DashboardProps {
  profile: UserProfile;
}

const Dashboard: React.FC<DashboardProps> = ({ profile }) => {
  const [stats, setStats] = useState<EmailStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string>('');

  const loadStats = async () => {
    setLoading(true);
    setError('');
    try {
      const data = await apiService.getEmailStats();
      setStats(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load stats');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    setError('');
    try {
      const result = await apiService.syncEmails(100);
      console.log('Sync result:', result);
      await loadStats(); // Reload stats after sync
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to sync emails');
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  const emailTypeData = stats ? [
    { name: 'Sent', value: stats.sent_emails, color: '#667eea' },
    { name: 'Received', value: stats.received_emails, color: '#764ba2' }
  ] : [];

  const recentEmailsData = stats?.recent_emails?.map(email => ({
    subject: email.subject.length > 20 ? email.subject.substring(0, 20) + '...' : email.subject,
    type: email.message_type,
    date: new Date(email.date_sent).toLocaleDateString()
  })) || [];

  return (
    <div>
      <div className="card">
        <h2>Welcome, {profile.email}!</h2>
        <p>Total Messages in Gmail: {profile.total_messages.toLocaleString()}</p>
        
        <button 
          className="btn" 
          onClick={handleSync} 
          disabled={syncing}
          style={{ marginTop: '16px' }}
        >
          {syncing ? 'Syncing Emails...' : 'Sync Recent Emails'}
        </button>
        
        <button 
          className="btn" 
          onClick={loadStats} 
          disabled={loading}
          style={{ marginTop: '16px', marginLeft: '12px' }}
        >
          {loading ? 'Loading...' : 'Refresh Stats'}
        </button>
      </div>

      {error && (
        <div className="card" style={{ backgroundColor: '#ffebee' }}>
          <p style={{ color: 'red' }}>Error: {error}</p>
        </div>
      )}

      {stats && (
        <>
          <div className="stats-grid">
            <div className="card stat-card">
              <div className="stat-number">{stats.total_emails}</div>
              <div className="stat-label">Total Emails Analyzed</div>
            </div>
            <div className="card stat-card">
              <div className="stat-number">{stats.sent_emails}</div>
              <div className="stat-label">Sent</div>
            </div>
            <div className="card stat-card">
              <div className="stat-number">{stats.received_emails}</div>
              <div className="stat-label">Received</div>
            </div>
          </div>

          {stats.total_emails > 0 && (
            <div className="card">
              <h3>Email Distribution</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={emailTypeData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {emailTypeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}

          {stats.recent_emails && stats.recent_emails.length > 0 && (
            <div className="card">
              <h3>Recent Emails</h3>
              <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                {stats.recent_emails.map((email, index) => (
                  <div 
                    key={email.id} 
                    style={{ 
                      padding: '12px', 
                      borderBottom: '1px solid #eee',
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center'
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 'bold' }}>{email.subject || '(No Subject)'}</div>
                      <div style={{ color: '#666', fontSize: '0.9em' }}>
                        {email.message_type === 'sent' ? 'To' : 'From'}: {email.sender_name || email.sender_email}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ 
                        padding: '4px 8px', 
                        borderRadius: '4px', 
                        backgroundColor: email.message_type === 'sent' ? '#e3f2fd' : '#f3e5f5',
                        fontSize: '0.8em',
                        marginBottom: '4px'
                      }}>
                        {email.message_type}
                      </div>
                      <div style={{ color: '#666', fontSize: '0.8em' }}>
                        {new Date(email.date_sent).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!loading && !stats && (
        <div className="card">
          <p>No email data available. Click "Sync Recent Emails" to get started.</p>
        </div>
      )}
    </div>
  );
};

export default Dashboard;