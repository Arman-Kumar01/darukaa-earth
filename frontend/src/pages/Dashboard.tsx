// Dashboard page — executive summary with KPI cards, map overview, and recent projects
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { analyticsService } from '../services/analytics';
import type { DashboardSummary } from '../types';
import {
  formatArea,
  formatCarbonValue,
  formatBioScore,
  formatDate,
  getProjectTypeLabel,
  getStatusBadgeClass,
} from '../utils';

function KPICard({
  title,
  value,
  subtitle,
  icon,
  color,
}: {
  title: string;
  value: string;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
}) {
  return (
    <div className="kpi-card">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
          <p className="text-2xl font-bold text-slate-100 mt-1">{value}</p>
          {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
        </div>
        <div className={`p-2 rounded-lg ${color}`}>{icon}</div>
      </div>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} className="card h-24 bg-slate-800" />
        ))}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    analyticsService
      .getDashboardSummary()
      .then(setSummary)
      .catch(() => setError('Unable to load dashboard data.'))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-screen-xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Dashboard</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            Platform overview — all figures from live database records
          </p>
        </div>
        <Link to="/projects/new" className="btn-primary">
          + New Project
        </Link>
      </div>

      {loading && <LoadingSkeleton />}

      {error && (
        <div className="card border-red-800/50 bg-red-900/20 text-red-400 mb-6">
          {error}
        </div>
      )}

      {summary && (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-5 gap-4 mb-8">
            <KPICard
              title="Total Projects"
              value={summary.total_projects.toString()}
              icon={
                <svg className="w-5 h-5 text-earth-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" />
                </svg>
              }
              color="bg-earth-900/50"
            />
            <KPICard
              title="Total Sites"
              value={summary.total_sites.toString()}
              subtitle={`${summary.active_sites_count} active`}
              icon={
                <svg className="w-5 h-5 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
                </svg>
              }
              color="bg-blue-900/50"
            />
            <KPICard
              title="Total Area"
              value={formatArea(summary.total_area_hectares)}
              icon={
                <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                </svg>
              }
              color="bg-teal-900/50"
            />
            <KPICard
              title="Avg Biodiversity"
              value={formatBioScore(summary.average_biodiversity_score)}
              subtitle="Demo synthetic data"
              icon={
                <svg className="w-5 h-5 text-bio-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
                </svg>
              }
              color="bg-emerald-900/50"
            />
            <KPICard
              title="Carbon Impact"
              value={`${(summary.total_carbon_value / 1000).toFixed(1)}k`}
              subtitle="tCO₂e (synthetic demo)"
              icon={
                <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M2.25 18L9 11.25l4.306 4.307a11.95 11.95 0 015.814-5.519l2.74-1.22m0 0l-5.94-2.28m5.94 2.28l-2.28 5.941" />
                </svg>
              }
              color="bg-amber-900/50"
            />
          </div>

          {/* Recent Projects */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <h2 className="section-title">Recent Projects</h2>
              <div className="space-y-3">
                {summary.recent_projects.length === 0 ? (
                  <div className="card text-center text-slate-500 py-8">
                    No projects yet.{' '}
                    <Link to="/projects/new" className="text-earth-400">
                      Create your first project →
                    </Link>
                  </div>
                ) : (
                  summary.recent_projects.map((p) => (
                    <Link
                      key={p.id}
                      to={`/projects/${p.id}`}
                      className="card flex items-center justify-between hover:border-slate-700 transition-colors group"
                    >
                      <div>
                        <p className="font-medium text-slate-100 group-hover:text-earth-400 transition-colors">
                          {p.name}
                        </p>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {p.region || 'No region'} · {getProjectTypeLabel(p.project_type)} ·{' '}
                          {formatDate(p.created_at)}
                        </p>
                      </div>
                      <span className={getStatusBadgeClass(p.status)}>{p.status}</span>
                    </Link>
                  ))
                )}
              </div>
            </div>

            {/* Area by Type */}
            <div>
              <h2 className="section-title">Area by Project Type</h2>
              <div className="card space-y-4">
                {Object.entries(summary.area_by_project_type).map(([type, area]) => (
                  <div key={type}>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-slate-400">{getProjectTypeLabel(type as never)}</span>
                      <span className="text-slate-300">{formatArea(area)}</span>
                    </div>
                    <div className="h-1.5 bg-slate-800 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-earth-600 rounded-full transition-all"
                        style={{
                          width: `${Math.min(
                            100,
                            (area / summary.total_area_hectares) * 100
                          )}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}

                <div className="pt-3 border-t border-slate-800">
                  <Link
                    to="/map"
                    className="flex items-center gap-2 text-sm text-earth-400 hover:text-earth-300 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z" />
                    </svg>
                    Open Map Explorer
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* Demo notice */}
          <div className="mt-6 px-4 py-3 rounded-lg bg-amber-900/20 border border-amber-800/50 text-amber-400/80 text-xs">
            ⚠️ <strong>Demo Notice:</strong> Carbon and biodiversity metrics use synthetic data for demonstration purposes. They do not represent actual environmental measurements.
          </div>
        </>
      )}
    </div>
  );
}
