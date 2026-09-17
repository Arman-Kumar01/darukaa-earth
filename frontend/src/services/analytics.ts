// Analytics API service
import apiClient from './api';
import type { DashboardSummary, MetricPoint, MonitoringEvent, SiteAnalytics } from '../types';

export const analyticsService = {
  async getSiteAnalytics(siteId: number, limit = 24): Promise<SiteAnalytics> {
    const { data } = await apiClient.get<SiteAnalytics>(`/sites/${siteId}/analytics`, {
      params: { limit },
    });
    return data;
  },

  async getSiteMetrics(siteId: number, limit = 24): Promise<MetricPoint[]> {
    const { data } = await apiClient.get<MetricPoint[]>(`/sites/${siteId}/metrics`, {
      params: { limit },
    });
    return data;
  },

  async getMonitoringEvents(siteId: number): Promise<MonitoringEvent[]> {
    const { data } = await apiClient.get<MonitoringEvent[]>(
      `/sites/${siteId}/monitoring-events`
    );
    return data;
  },

  async getDashboardSummary(): Promise<DashboardSummary> {
    const { data } = await apiClient.get<DashboardSummary>('/dashboard/summary');
    return data;
  },
};
