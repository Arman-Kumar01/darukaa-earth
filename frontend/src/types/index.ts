// TypeScript type definitions for Darukaa.Earth

export interface User {
  id: number;
  name: string;
  email: string;
  role: 'admin' | 'user';
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type ProjectType = 'carbon' | 'biodiversity' | 'carbon_biodiversity';
export type ProjectStatus = 'active' | 'completed' | 'planned' | 'paused';

export interface Project {
  id: number;
  name: string;
  description: string | null;
  project_type: ProjectType;
  region: string | null;
  status: ProjectStatus;
  start_date: string | null;
  created_by: number | null;
  created_at: string;
  updated_at: string;
  site_count: number;
  total_area_hectares: number;
}

export interface ProjectCreate {
  name: string;
  description?: string;
  project_type: ProjectType;
  region?: string;
  status: ProjectStatus;
  start_date?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  project_type?: ProjectType;
  region?: string;
  status?: ProjectStatus;
  start_date?: string;
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type SiteStatus = 'active' | 'completed' | 'planned' | 'inactive';

export interface GeoJSONPolygon {
  type: 'Polygon';
  coordinates: number[][][];
}

export interface Site {
  id: number;
  project_id: number;
  name: string;
  description: string | null;
  status: SiteStatus;
  geometry: GeoJSONPolygon | null;
  area_hectares: number | null;
  centroid_lat: number | null;
  centroid_lng: number | null;
  monitoring_date: string | null;
  created_at: string;
  updated_at: string;
  latest_carbon_value: number | null;
  latest_biodiversity_score: number | null;
}

export interface SiteCreate {
  project_id: number;
  name: string;
  description?: string;
  status: SiteStatus;
  monitoring_date?: string;
  geometry: GeoJSONPolygon;
}

export interface MetricPoint {
  recorded_at: string;
  carbon_value: number;
  biodiversity_score: number;
  vegetation_index: number;
  monitoring_score: number;
}

export interface SiteAnalytics {
  site_id: number;
  site_name: string;
  project_name: string;
  metrics: MetricPoint[];
  latest_carbon_value: number | null;
  latest_biodiversity_score: number | null;
  avg_carbon_value: number | null;
  avg_biodiversity_score: number | null;
  carbon_trend: number | null;
  biodiversity_trend: number | null;
}

export interface MonitoringEvent {
  id: number;
  event_date: string;
  event_type: string;
  notes: string | null;
}

export interface DashboardSummary {
  total_projects: number;
  total_sites: number;
  total_area_hectares: number;
  average_biodiversity_score: number;
  total_carbon_value: number;
  recent_projects: Array<{
    id: number;
    name: string;
    status: ProjectStatus;
    project_type: ProjectType;
    region: string | null;
    created_at: string;
  }>;
  area_by_project_type: Record<string, number>;
  active_sites_count: number;
}

export interface GeoJSONFeature {
  type: 'Feature';
  id: number;
  geometry: GeoJSONPolygon;
  properties: {
    id: number;
    name: string;
    project_id: number;
    status: SiteStatus;
    area_hectares: number | null;
    centroid_lat: number | null;
    centroid_lng: number | null;
    monitoring_date: string | null;
    latest_carbon_value: number | null;
    latest_biodiversity_score: number | null;
  };
}

export interface GeoJSONCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}
