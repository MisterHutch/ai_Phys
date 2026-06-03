export interface UserProfile {
  email: string;
  total_messages: number;
  total_threads: number;
}

export interface AuthStatus {
  authenticated: boolean;
  profile: UserProfile | null;
}

export interface EmailMessage {
  id: string;
  subject: string;
  sender_email: string;
  sender_name: string;
  date_sent: string;
  labels: string;
  message_type: 'sent' | 'received';
}

export interface EmailStats {
  total_emails: number;
  sent_emails: number;
  received_emails: number;
  recent_emails: EmailMessage[];
}

export interface OAuthConfig {
  client_id: string;
  client_secret: string;
  project_id: string;
}

export interface AuthResponse {
  auth_url?: string;
  message?: string;
  success?: boolean;
  profile?: UserProfile;
  user_id?: number;
}