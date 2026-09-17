// Site Details / Analytics page — Chart.js time-series charts
import { useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import { analyticsService } from '../services/analytics';
import { sitesService } from '../services/sites';
import type { MonitoringEvent, Site, SiteAnalytics } from '../types';
import {
  formatArea,
  formatBioScore,
  formatCarbonValue,
  formatDate,
  getStatusBadgeClass,
  getTrendColor,
  getTrendIcon,
} from '../utils';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string;

const CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: 'index' as const, intersect: false },
  plugins: {
    legend: { labels: { color: '#94a3b8', font: { size: 12 } } },
    tooltip: { backgroundColor: '#1e293b', titleColor: '#e2e8f0', bodyColor: '#94a3b8' },
  },
  scales: {
    x: { ticks: { color: '#475569' }, grid: { color: '#1e293b' } },
    y: { ticks: { color: '#475569' }, grid: { color: '#1e293b' } },
  },
};

export default function SiteDetails() {
  const { siteId } = useParams<{ siteId: string }>();
  const [site, setSite] = useState<Site | null>(null);
  const [analytics, setAnalytics] = useState<SiteAnalytics | null>(null);
  const [events, setEvents] = useState<MonitoringEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  useEffect(() => {
    const id = parseInt(siteId!);
    Promise.all([
      sitesService.getSite(id),
      analyticsService.getSiteAnalytics(id),
      analyticsService.getMonitoringEvents(id),
    ])
      .then(([s, a, ev]) => {
        setSite(s);
        setAnalytics(a);
        setEvents(ev);
      })
      .catch(() => setError('Failed to load site analytics.'))
      .finally(() => setLoading(false));
  }, [siteId]);

  // Mini map showing site polygon
  useEffect(() => {
    if (!site?.geometry || !mapContainer.current || map.current || !MAPBOX_TOKEN) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;
    const m = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      zoom: 10,
      center: [site.centroid_lng ?? 0, site.centroid_lat ?? 0],
    });

    m.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current = m;

    m.on('load', () => {
      m.addSource('site-geom', {
        type: 'geojson',
        data: {
          type: 'Feature',
          geometry: site.geometry!,
          properties: {},
        } as never,
      });

      m.addLayer({ id: 'site-fill', type: 'fill', source: 'site-geom', paint: { 'fill-color': '#22c55e', 'fill-opacity': 0.4 } });
      m.addLayer({ id: 'site-outline', type: 'line', source: 'site-geom', paint: { 'line-color': '#4ade80', 'line-width': 2 } });

      // Fit bounds
      const coords = site.geometry!.coordinates[0] as [number, number][];
      const bounds = coords.reduce(
        (b, c) => b.extend(c as mapboxgl.LngLatLike),
        new mapboxgl.LngLatBounds(coords[0], coords[0])
      );
      m.fitBounds(bounds, { padding: 40 });
    });

    return () => { m.remove(); map.current = null; };
  }, [site]);

  if (loading) return <div className="p-6"><div className="card h-96 animate-pulse bg-slate-800" /></div>;
  if (error) return <div className="p-6"><div className="card text-red-400">{error}</div></div>;
  if (!site || !analytics) return null;

  const labels = analytics.metrics.map((m) =>
    new Date(m.recorded_at).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })
  );

  const carbonChartData = {
    labels,
    datasets: [{
      label: 'Carbon (tCO₂e/ha)',
      data: analytics.metrics.map((m) => m.carbon_value),
      borderColor: '#f59e0b',
      backgroundColor: 'rgba(245,158,11,0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 3,
    }],
  };

  const bioChartData = {
    labels,
    datasets: [{
      label: 'Biodiversity Score',
      data: analytics.metrics.map((m) => m.biodiversity_score),
      borderColor: '#10b981',
      backgroundColor: 'rgba(16,185,129,0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 3,
    }],
  };

  const ndviChartData = {
    labels,
    datasets: [{
      label: 'Vegetation Index (NDVI)',
      data: analytics.metrics.map((m) => m.vegetation_index),
      borderColor: '#60a5fa',
      backgroundColor: 'rgba(96,165,250,0.1)',
      fill: true,
      tension: 0.4,
      pointRadius: 3,
    }, {
      label: 'Monitoring Score',
      data: analytics.metrics.map((m) => m.monitoring_score / 100),
      borderColor: '#a78bfa',
      backgroundColor: 'transparent',
      tension: 0.4,
      pointRadius: 2,
      borderDash: [4, 4],
    }],
  };

  return (
    <div className="p-6 max-w-screen-xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="text-sm text-slate-500 mb-1">
            <Link to={`/projects/${site.project_id}`} className="hover:text-slate-300">
              ← {analytics.project_name}
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-slate-100">{site.name}</h1>
          <p className="text-slate-500 text-sm">{formatArea(site.area_hectares)} · {site.centroid_lat?.toFixed(4)}°N, {site.centroid_lng?.toFixed(4)}°E</p>
        </div>
        <span className={getStatusBadgeClass(site.status)}>{site.status}</span>
      </div>

      {/* Demo notice */}
      <div className="px-4 py-2 rounded-lg bg-amber-900/20 border border-amber-800/40 text-amber-400/80 text-xs">
        ⚠️ Analytics data is synthetic and for demonstration only — not real environmental measurements.
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 xl:grid-cols-4 gap-4">
        <KPICard title="Site Area" value={formatArea(site.area_hectares)} color="text-teal-400" />
        <KPICard
          title="Carbon Value"
          value={formatCarbonValue(analytics.latest_carbon_value)}
          trend={analytics.carbon_trend}
          color="text-amber-400"
        />
        <KPICard
          title="Biodiversity Score"
          value={formatBioScore(analytics.latest_biodiversity_score)}
          trend={analytics.biodiversity_trend}
          color="text-emerald-400"
        />
        <KPICard
          title="Monitoring Events"
          value={events.length.toString()}
          color="text-blue-400"
        />
      </div>

      {/* Charts + Map */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        <div className="xl:col-span-2 space-y-6">
          {/* Carbon chart */}
          <div className="card">
            <h3 className="font-semibold text-slate-200 mb-4">Carbon Performance Over Time</h3>
            {analytics.metrics.length === 0 ? (
              <EmptyChart message="No metric data available" />
            ) : (
              <div className="h-48"><Line data={carbonChartData} options={CHART_OPTIONS} /></div>
            )}
          </div>

          {/* Biodiversity chart */}
          <div className="card">
            <h3 className="font-semibold text-slate-200 mb-4">Biodiversity Score Over Time</h3>
            {analytics.metrics.length === 0 ? (
              <EmptyChart message="No metric data available" />
            ) : (
              <div className="h-48"><Line data={bioChartData} options={CHART_OPTIONS} /></div>
            )}
          </div>

          {/* NDVI + Monitoring */}
          <div className="card">
            <h3 className="font-semibold text-slate-200 mb-4">Environmental Performance</h3>
            {analytics.metrics.length === 0 ? (
              <EmptyChart message="No metric data available" />
            ) : (
              <div className="h-48"><Line data={ndviChartData} options={CHART_OPTIONS} /></div>
            )}
          </div>
        </div>

        {/* Right column: mini map + monitoring events */}
        <div className="space-y-6">
          {/* Mini Map */}
          <div className="card p-0 overflow-hidden h-56">
            {!MAPBOX_TOKEN ? (
              <div className="h-full flex items-center justify-center bg-slate-900 text-slate-500 text-xs p-4 text-center">
                Add VITE_MAPBOX_TOKEN to view site on map
              </div>
            ) : (
              <div ref={mapContainer} className="w-full h-full" />
            )}
          </div>

          {/* Monitoring Events */}
          <div className="card">
            <h3 className="font-semibold text-slate-200 mb-3">Monitoring Activity</h3>
            {events.length === 0 ? (
              <p className="text-slate-500 text-sm">No monitoring events recorded.</p>
            ) : (
              <div className="space-y-3 max-h-72 overflow-y-auto">
                {events.map((event) => (
                  <div key={event.id} className="flex gap-3 text-sm">
                    <div className="flex-shrink-0 w-1.5 h-1.5 rounded-full bg-earth-500 mt-1.5" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-slate-300 capitalize">
                          {event.event_type.replace(/_/g, ' ')}
                        </span>
                        <span className="text-xs text-slate-600">{event.event_date}</span>
                      </div>
                      {event.notes && (
                        <p className="text-xs text-slate-500 mt-0.5">{event.notes}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Site details */}
          <div className="card text-sm space-y-2">
            <h3 className="font-semibold text-slate-200 mb-2">Site Details</h3>
            <Row label="Project" value={analytics.project_name} />
            <Row label="Status" value={site.status} />
            <Row label="Area" value={formatArea(site.area_hectares)} />
            <Row label="Avg Carbon" value={formatCarbonValue(analytics.avg_carbon_value)} />
            <Row label="Avg Biodiversity" value={formatBioScore(analytics.avg_biodiversity_score)} />
            <Row label="Last Monitoring" value={formatDate(site.monitoring_date)} />
            <Row label="Created" value={formatDate(site.created_at)} />
          </div>
        </div>
      </div>
    </div>
  );
}

function KPICard({
  title,
  value,
  trend,
  color,
}: {
  title: string;
  value: string;
  trend?: number | null;
  color: string;
}) {
  return (
    <div className="kpi-card">
      <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">{title}</p>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      {trend !== undefined && trend !== null && (
        <p className={`text-xs ${getTrendColor(trend)}`}>
          {getTrendIcon(trend)} {Math.abs(trend).toFixed(1)}% since start
        </p>
      )}
    </div>
  );
}

function EmptyChart({ message }: { message: string }) {
  return (
    <div className="h-48 flex items-center justify-center text-slate-600 text-sm">
      {message}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-300 text-right">{value}</span>
    </div>
  );
}
