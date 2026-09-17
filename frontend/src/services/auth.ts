// Authentication API service
import apiClient from './api';
import type { TokenResponse, User } from '../types';

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export const authService = {
  async login(payload: LoginPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/auth/login', payload);
    return data;
  },

  async register(payload: RegisterPayload): Promise<TokenResponse> {
    const { data } = await apiClient.post<TokenResponse>('/auth/register', payload);
    return data;
  },

  async getMe(): Promise<User> {
    const { data } = await apiClient.get<User>('/auth/me');
    return data;
  },

  saveSession(tokenResponse: TokenResponse): void {
    localStorage.setItem('access_token', tokenResponse.access_token);
    localStorage.setItem('user', JSON.stringify(tokenResponse.user));
  },

  clearSession(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
  },

  getStoredUser(): User | null {
    const stored = localStorage.getItem('user');
    if (!stored) return null;
    try {
      return JSON.parse(stored) as User;
    } catch {
      return null;
    }
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  },
};
