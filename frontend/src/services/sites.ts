// Sites API service
import apiClient from './api';
import type {
  GeoJSONCollection,
  PaginatedResponse,
  Site,
  SiteCreate,
} from '../types';

export interface SiteFilters {
  project_id?: number;
  page?: number;
  page_size?: number;
  status?: string;
}

export const sitesService = {
  async getSites(filters: SiteFilters = {}): Promise<PaginatedResponse<Site>> {
    const { data } = await apiClient.get<PaginatedResponse<Site>>('/sites', {
      params: filters,
    });
    return data;
  },

  async getSite(id: number): Promise<Site> {
    const { data } = await apiClient.get<Site>(`/sites/${id}`);
    return data;
  },

  async createSite(payload: SiteCreate): Promise<Site> {
    const { data } = await apiClient.post<Site>('/sites', payload);
    return data;
  },

  async deleteSite(id: number): Promise<void> {
    await apiClient.delete(`/sites/${id}`);
  },

  async getMapSites(project_id?: number): Promise<GeoJSONCollection> {
    const { data } = await apiClient.get<GeoJSONCollection>('/map/sites', {
      params: project_id ? { project_id } : {},
    });
    return data;
  },

  async getProjectSites(projectId: number): Promise<PaginatedResponse<Site>> {
    return this.getSites({ project_id: projectId, page_size: 100 });
  },
};
