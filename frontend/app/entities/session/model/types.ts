export interface User {
  id: string;
  email: string;
  display_name: string | null;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface Credentials {
  email: string;
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  display_name?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  user: User;
}
