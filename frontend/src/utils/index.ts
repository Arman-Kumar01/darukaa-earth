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
    const axiosError = error as {
      response?: { data?: { detail?: string | unknown[] }; status?: number };
      message?: string;
    };
    const status = axiosError.response?.status;
    const detail = axiosError.response?.data?.detail;

    // Use the server's detail message if it's a plain string
    if (detail && typeof detail === 'string') {
      return detail;
    }

    // Map common HTTP status codes to user-friendly messages
    switch (status) {
      case 400:
        return 'Invalid request. Please check your inputs.';
      case 401:
        return 'Your session has expired. Please log in again.';
      case 403:
        return 'You do not have permission to perform this action.';
      case 404:
        return 'The requested resource was not found.';
      case 422:
        return 'Validation error. Please check all required fields.';
      case 500:
        return 'Server error while processing your request. Please try again.';
      case 503:
        return 'Service temporarily unavailable. Please try again shortly.';
      default:
        return axiosError.message || 'An unexpected error occurred.';
    }
  }

  // Network-level error (no response received)
  if (error && typeof error === 'object' && 'message' in error) {
    const netError = error as { message?: string };
    if (netError.message?.toLowerCase().includes('network')) {
      return 'Network error. Please check your connection and try again.';
    }
  }

  return 'An unexpected error occurred. Please try again.';
}
