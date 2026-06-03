import axios from 'axios';
import { AuthStatus, EmailStats, OAuthConfig, AuthResponse } from '../types/api';

const API_BASE = '/api';

class ApiService {
  private client = axios.create({
    baseURL: API_BASE,
    timeout: 10000,
  });

  // Auth endpoints
  async getAuthStatus(): Promise<AuthStatus> {
    const response = await this.client.get<AuthStatus>('/gmail/auth/status');
    return response.data;
  }

  async setupOAuth(config: OAuthConfig): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/gmail/auth/setup', config);
    return response.data;
  }

  async completeOAuth(code: string): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/gmail/auth/complete', { code });
    return response.data;
  }

  // Gmail endpoints
  async syncEmails(limit: number = 100): Promise<{ success: boolean; messages_synced: number; total_messages: number }> {
    const response = await this.client.post(`/gmail/sync?limit=${limit}`);
    return response.data;
  }

  async getEmailStats(): Promise<EmailStats> {
    const response = await this.client.get<EmailStats>('/gmail/stats');
    return response.data;
  }

  async getUserProfile(): Promise<any> {
    const response = await this.client.get('/gmail/profile');
    return response.data;
  }
}

export const apiService = new ApiService();