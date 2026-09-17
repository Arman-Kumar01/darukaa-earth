// Projects API service
import apiClient from './api';
import type { PaginatedResponse, Project, ProjectCreate, ProjectUpdate } from '../types';

export interface ProjectFilters {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  project_type?: string;
}

export const projectsService = {
  async getProjects(filters: ProjectFilters = {}): Promise<PaginatedResponse<Project>> {
    const { data } = await apiClient.get<PaginatedResponse<Project>>('/projects', {
      params: filters,
    });
    return data;
  },

  async getProject(id: number): Promise<Project> {
    const { data } = await apiClient.get<Project>(`/projects/${id}`);
    return data;
  },

  async createProject(payload: ProjectCreate): Promise<Project> {
    const { data } = await apiClient.post<Project>('/projects', payload);
    return data;
  },

  async updateProject(id: number, payload: ProjectUpdate): Promise<Project> {
    const { data } = await apiClient.put<Project>(`/projects/${id}`, payload);
    return data;
  },

  async deleteProject(id: number): Promise<void> {
    await apiClient.delete(`/projects/${id}`);
  },
};
