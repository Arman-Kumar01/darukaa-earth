// Map Explorer page — full-screen Mapbox with all site polygons and side panel
import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { sitesService } from '../services/sites';
import { projectsService } from '../services/projects';
import type { GeoJSONCollection, GeoJSONFeature, Project } from '../types';
import {
  formatArea,
  formatBioScore,
  formatCarbonValue,
  formatDate,
  getStatusBadgeClass,
} from '../utils';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string;

export default function MapExplorer() {
  const navigate = useNavigate();
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);

  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('');
  const [selectedSite, setSelectedSite] = useState<GeoJSONFeature | null>(null);
  const [geojson, setGeojson] = useState<GeoJSONCollection | null>(null);
  const [loading, setLoading] = useState(true);

  // Load projects for filter
  useEffect(() => {
    projectsService.getProjects({ page_size: 100 }).then((r) => setProjects(r.data));
  }, []);

  // Load GeoJSON sites
  const loadMapData = (projectId?: number) => {
    setLoading(true);
    sitesService
      .getMapSites(projectId)
      .then((data) => {
        setGeojson(data);
        // Update map source if map is loaded
        if (map.current?.getSource('sites')) {
          (map.current.getSource('sites') as mapboxgl.GeoJSONSource).setData(data as never);
        }
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadMapData(); }, []);

  // Initialize Mapbox
  useEffect(() => {
    if (!mapContainer.current || map.current || !MAPBOX_TOKEN) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;
    const m = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      zoom: 3,
      center: [20, 10],
    });

    m.addControl(new mapboxgl.NavigationControl(), 'top-right');
    m.addControl(new mapboxgl.ScaleControl(), 'bottom-left');
    map.current = m;

    m.on('load', () => {
      // Add source (initially empty)
      m.addSource('sites', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] } as never,
      });

      // Fill layer
      m.addLayer({
        id: 'sites-fill',
        type: 'fill',
        source: 'sites',
        paint: {
          'fill-color': [
            'case',
            ['==', ['get', 'status'], 'active'], '#22c55e',
            ['==', ['get', 'status'], 'completed'], '#60a5fa',
            ['==', ['get', 'status'], 'planned'], '#fbbf24',
            '#6b7280',
          ],
          'fill-opacity': 0.4,
        },
      });

      // Outline
      m.addLayer({
        id: 'sites-outline',
        type: 'line',
        source: 'sites',
        paint: {
          'line-color': '#4ade80',
          'line-width': ['case', ['boolean', ['feature-state', 'selected'], false], 3, 1.5],
        },
      });

      // Load initial data
      sitesService.getMapSites().then((data) => {
        (m.getSource('sites') as mapboxgl.GeoJSONSource).setData(data as never);

        // Fit to all sites
        if (data.features.length > 0) {
          const coords = data.features.flatMap(
            (f) => f.geometry.coordinates[0] as [number, number][]
          );
          if (coords.length) {
            const bounds = coords.reduce(
              (b, c) => b.extend(c as mapboxgl.LngLatLike),
              new mapboxgl.LngLatBounds(coords[0], coords[0])
            );
            m.fitBounds(bounds, { padding: 80 });
          }
        }
      });

      // Click handler
      m.on('click', 'sites-fill', (e) => {
        const feature = e.features?.[0] as unknown as GeoJSONFeature;
        if (feature) setSelectedSite(feature);
      });

      m.on('click', (e) => {
        const features = m.queryRenderedFeatures(e.point, { layers: ['sites-fill'] });
        if (features.length === 0) setSelectedSite(null);
      });

      m.on('mouseenter', 'sites-fill', () => { m.getCanvas().style.cursor = 'pointer'; });
      m.on('mouseleave', 'sites-fill', () => { m.getCanvas().style.cursor = ''; });
    });

    return () => { m.remove(); map.current = null; };
  }, []);

  const handleProjectFilter = (value: string) => {
    setSelectedProjectId(value);
    setSelectedSite(null);
    loadMapData(value ? parseInt(value) : undefined);
  };

  const fitAllSites = () => {
    if (!geojson || !map.current) return;
    const coords = geojson.features.flatMap(
      (f) => f.geometry.coordinates[0] as [number, number][]
    );
    if (coords.length) {
      const bounds = coords.reduce(
        (b, c) => b.extend(c as mapboxgl.LngLatLike),
        new mapboxgl.LngLatBounds(coords[0], coords[0])
      );
      map.current.fitBounds(bounds, { padding: 80 });
    }
  };

  const flyToSite = (feature: GeoJSONFeature) => {
    if (!map.current || !feature.properties.centroid_lng) return;
    map.current.flyTo({
      center: [feature.properties.centroid_lng!, feature.properties.centroid_lat!],
      zoom: 13,
    });
  };

  return (
    <div className="flex flex-col h-full">
      {/* Controls bar */}
      <div className="flex items-center gap-4 px-4 py-3 border-b border-slate-800 bg-slate-900">
        <h1 className="text-lg font-semibold text-slate-100">Map Explorer</h1>

        <select
          value={selectedProjectId}
          onChange={(e) => handleProjectFilter(e.target.value)}
          className="input-field w-56 text-sm py-1.5"
          aria-label="Filter by project"
        >
          <option value="">All projects</option>
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>

        <button onClick={fitAllSites} className="btn-secondary text-sm py-1.5">
          Fit all sites
        </button>

        {loading && (
          <span className="text-slate-500 text-sm">Loading map data...</span>
        )}

        {geojson && (
          <span className="text-slate-500 text-sm ml-auto">
            {geojson.features.length} site{geojson.features.length !== 1 ? 's' : ''} shown
          </span>
        )}
      </div>

      {/* Map + Panel */}
      <div className="flex flex-1 overflow-hidden">
        {/* Map */}
        <div className="flex-1 relative">
          {!MAPBOX_TOKEN ? (
            <div className="absolute inset-0 flex items-center justify-center bg-slate-950 text-slate-500 text-center p-8">
              <div>
                <p className="text-xl font-medium mb-2">Mapbox Token Required</p>
                <p className="text-sm">Set <code className="bg-slate-800 px-1 rounded">VITE_MAPBOX_TOKEN</code> in your .env file.</p>
              </div>
            </div>
          ) : (
            <div ref={mapContainer} className="absolute inset-0" />
          )}

          {/* Legend */}
          {MAPBOX_TOKEN && (
            <div className="absolute bottom-8 right-4 bg-slate-900/90 backdrop-blur-sm rounded-lg p-3 text-xs space-y-1.5">
              <p className="text-slate-400 font-medium mb-2">Site Status</p>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-sm bg-emerald-500 opacity-70" /><span className="text-slate-400">Active</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-sm bg-blue-500 opacity-70" /><span className="text-slate-400">Completed</span></div>
              <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-sm bg-amber-500 opacity-70" /><span className="text-slate-400">Planned</span></div>
            </div>
          )}
        </div>

        {/* Side Panel */}
        {selectedSite && (
          <div className="w-72 border-l border-slate-800 bg-slate-900 p-4 overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <h2 className="font-semibold text-slate-200">Site Details</h2>
              <button
                onClick={() => setSelectedSite(null)}
                className="text-slate-500 hover:text-slate-300"
                aria-label="Close panel"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3">
              <div>
                <p className="text-xs text-slate-500">Site Name</p>
                <p className="font-medium text-slate-100">{selectedSite.properties.name}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Status</p>
                <span className={getStatusBadgeClass(selectedSite.properties.status)}>
                  {selectedSite.properties.status}
                </span>
              </div>
              <div>
                <p className="text-xs text-slate-500">Area</p>
                <p className="text-slate-300">{formatArea(selectedSite.properties.area_hectares)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Carbon Value</p>
                <p className="text-amber-400">{formatCarbonValue(selectedSite.properties.latest_carbon_value)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Biodiversity Score</p>
                <p className="text-emerald-400">{formatBioScore(selectedSite.properties.latest_biodiversity_score)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Last Monitoring</p>
                <p className="text-slate-300">{formatDate(selectedSite.properties.monitoring_date)}</p>
              </div>
              <div>
                <p className="text-xs text-slate-500">Centroid</p>
                <p className="text-slate-400 text-xs">
                  {selectedSite.properties.centroid_lat?.toFixed(5)}°, {selectedSite.properties.centroid_lng?.toFixed(5)}°
                </p>
              </div>
            </div>

            <div className="mt-6 flex flex-col gap-2">
              <button
                onClick={() => flyToSite(selectedSite)}
                className="btn-secondary text-sm"
              >
                Zoom to Site
              </button>
              <button
                onClick={() => navigate(`/sites/${selectedSite.properties.id}`)}
                className="btn-primary text-sm"
                id="view-analytics-btn"
              >
                View Analytics →
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
