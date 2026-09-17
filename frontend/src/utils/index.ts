// Utility functions
import type { ProjectStatus, ProjectType, SiteStatus } from '../types';

export function formatArea(hectares: number | null | undefined): string {
  if (!hectares) return 'N/A';
  return `${hectares.toLocaleString('en-US', { maximumFractionDigits: 1 })} ha`;
}

export function formatNumber(value: number | null | undefined, decimals = 1): string {
  if (value === null || value === undefined) return 'N/A';
  return value.toLocaleString('en-US', { maximumFractionDigits: decimals });
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatCarbonValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)} tCO₂e/ha`;
}

export function formatBioScore(value: number | null | undefined): string {
  if (value === null || value === undefined) return 'N/A';
  return `${value.toFixed(1)}/100`;
}

export function getProjectTypeLabel(type: ProjectType): string {
  const labels: Record<ProjectType, string> = {
    carbon: 'Carbon',
    biodiversity: 'Biodiversity',
    carbon_biodiversity: 'Carbon + Biodiversity',
  };
  return labels[type] || type;
}

export function getProjectTypeColor(type: ProjectType): string {
  const colors: Record<ProjectType, string> = {
    carbon: 'text-amber-400',
    biodiversity: 'text-emerald-400',
    carbon_biodiversity: 'text-teal-400',
  };
  return colors[type] || 'text-slate-400';
}

export function getStatusBadgeClass(status: ProjectStatus | SiteStatus): string {
  const classes: Record<string, string> = {
    active: 'badge-active',
    completed: 'badge-completed',
    planned: 'badge-planned',
    paused: 'badge-inactive',
    inactive: 'badge-inactive',
  };
  return classes[status] || 'badge-inactive';
}

export function getTrendIcon(trend: number | null | undefined): string {
  if (!trend) return '→';
  if (trend > 2) return '↑';
  if (trend < -2) return '↓';
  return '→';
}

export function getTrendColor(trend: number | null | undefined): string {
  if (!trend) return 'text-slate-400';
  if (trend > 0) return 'text-earth-400';
  if (trend < 0) return 'text-red-400';
  return 'text-slate-400';
}

export function getApiErrorMessage(error: unknown): string {
  if (error && typeof error === 'object' && 'response' in error) {
    const axiosError = error as { response?: { data?: { detail?: string } } };
    return axiosError.response?.data?.detail || 'An unexpected error occurred.';
  }
  return 'Network error. Please check your connection.';
}
