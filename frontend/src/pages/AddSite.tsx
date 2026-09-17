// Add Site page — key feature: Mapbox polygon drawing + site creation
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import mapboxgl from 'mapbox-gl';
import MapboxDraw from '@mapbox/mapbox-gl-draw';
import 'mapbox-gl/dist/mapbox-gl.css';
import '@mapbox/mapbox-gl-draw/dist/mapbox-gl-draw.css';
import { sitesService } from '../services/sites';
import { projectsService } from '../services/projects';
import type { GeoJSONPolygon, SiteCreate } from '../types';
import { getApiErrorMessage } from '../utils';
import toast from 'react-hot-toast';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string;

export default function AddSite() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();

  const [projectName, setProjectName] = useState('');
  const [form, setForm] = useState({
    name: '',
    description: '',
    status: 'active',
    monitoring_date: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [drawnGeometry, setDrawnGeometry] = useState<GeoJSONPolygon | null>(null);
  const [loading, setLoading] = useState(false);
  const [drawMode, setDrawMode] = useState(false);

  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  const draw = useRef<MapboxDraw | null>(null);

  // Load project name for display
  useEffect(() => {
    projectsService.getProject(parseInt(projectId!)).then((p) => setProjectName(p.name));
  }, [projectId]);

  // Initialize map
  useEffect(() => {
    if (!mapContainer.current || map.current || !MAPBOX_TOKEN) return;

    mapboxgl.accessToken = MAPBOX_TOKEN;
    const m = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      zoom: 3,
      center: [78.9629, 20.5937], // Center on India initially
    });

    const drawControl = new MapboxDraw({
      displayControlsDefault: false,
      controls: { polygon: true, trash: true },
      defaultMode: 'simple_select',
    });

    m.addControl(new mapboxgl.NavigationControl(), 'top-right');
    m.addControl(drawControl);

    map.current = m;
    draw.current = drawControl;

    // Trigger resize on load and idle to guarantee proper canvas dimensions
    m.on('load', () => {
      m.resize();
    });
    m.on('idle', () => {
      m.resize();
    });

    // ResizeObserver ensures canvas keeps matching container dimensions across layout reflows
    let resizeObserver: ResizeObserver | null = null;
    if (typeof ResizeObserver !== 'undefined' && mapContainer.current) {
      resizeObserver = new ResizeObserver(() => {
        m.resize();
      });
      resizeObserver.observe(mapContainer.current);
    }

    // Listen for polygon creation/updates
    const updateGeometry = () => {
      const data = drawControl.getAll();
      const features = data.features.filter((f) => f.geometry.type === 'Polygon');
      if (features.length > 0) {
        setDrawnGeometry(features[features.length - 1].geometry as GeoJSONPolygon);
        setDrawMode(false);
      } else {
        setDrawnGeometry(null);
      }
    };

    m.on('draw.create', updateGeometry);
    m.on('draw.update', updateGeometry);
    m.on('draw.delete', updateGeometry);

    return () => {
      resizeObserver?.disconnect();
      m.remove();
      map.current = null;
      draw.current = null;
    };
  }, []);

  const startDrawing = () => {
    if (draw.current) {
      map.current?.resize();
      draw.current.changeMode('draw_polygon');
      setDrawMode(true);
      toast('Click the map to place polygon vertices. Double-click to finish.', { icon: '✏️' });
    }
  };

  const clearPolygon = () => {
    draw.current?.deleteAll();
    setDrawnGeometry(null);
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.name.trim()) errs.name = 'Site name is required.';
    if (!drawnGeometry) errs.geometry = 'Please draw a polygon on the map.';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      const payload: SiteCreate = {
        project_id: parseInt(projectId!),
        name: form.name,
        description: form.description || undefined,
        status: form.status as never,
        monitoring_date: form.monitoring_date || undefined,
        geometry: drawnGeometry!,
      };
      const site = await sitesService.createSite(payload);
      toast.success(`Site "${site.name}" created! Area: ${site.area_hectares?.toFixed(2)} ha`);
      navigate(`/projects/${projectId}`);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-screen-xl mx-auto">
      <div className="mb-6">
        <div className="text-slate-500 text-sm mb-1">← {projectName || `Project ${projectId}`}</div>
        <h1 className="text-2xl font-bold text-slate-100">Add Monitoring Site</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Fill in site details and draw a polygon on the map to define its boundaries.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Form */}
        <div className="lg:col-span-2 card self-start">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="site-name" className="label">Site name *</label>
              <input
                id="site-name"
                type="text"
                value={form.name}
                onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
                className="input-field"
                placeholder="e.g. North Forest Corridor"
              />
              {errors.name && <p className="mt-1 text-xs text-red-400">{errors.name}</p>}
            </div>

            <div>
              <label htmlFor="site-desc" className="label">Description</label>
              <textarea
                id="site-desc"
                value={form.description}
                onChange={(e) => setForm((p) => ({ ...p, description: e.target.value }))}
                className="input-field h-20 resize-none"
                placeholder="Optional site description..."
              />
            </div>

            <div>
              <label htmlFor="site-status" className="label">Status</label>
              <select
                id="site-status"
                value={form.status}
                onChange={(e) => setForm((p) => ({ ...p, status: e.target.value }))}
                className="input-field"
              >
                <option value="active">Active</option>
                <option value="planned">Planned</option>
                <option value="inactive">Inactive</option>
                <option value="completed">Completed</option>
              </select>
            </div>

            <div>
              <label htmlFor="site-date" className="label">Last monitoring date</label>
              <input
                id="site-date"
                type="date"
                value={form.monitoring_date}
                onChange={(e) => setForm((p) => ({ ...p, monitoring_date: e.target.value }))}
                className="input-field"
              />
            </div>

            {/* Polygon section */}
            <div className="pt-2 border-t border-slate-800">
              <p className="label">Site polygon *</p>
              {drawnGeometry ? (
                <div className="flex items-center gap-2">
                  <div className="flex-1 px-3 py-2 rounded-lg bg-earth-900/30 border border-earth-800 text-earth-400 text-xs">
                    ✓ Polygon drawn ({drawnGeometry.coordinates[0].length - 1} vertices)
                  </div>
                  <button type="button" onClick={clearPolygon} className="btn-danger text-xs px-2 py-1.5">
                    Clear
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  onClick={startDrawing}
                  className={`w-full py-2 rounded-lg border text-sm font-medium transition-colors ${
                    drawMode
                      ? 'bg-earth-900/50 border-earth-600 text-earth-300'
                      : 'border-dashed border-slate-700 text-slate-400 hover:border-earth-700 hover:text-earth-400'
                  }`}
                  id="draw-polygon-btn"
                >
                  {drawMode ? '✏️ Drawing... click to place vertices' : '✏️ Draw Polygon on Map'}
                </button>
              )}
              {errors.geometry && (
                <p className="mt-1 text-xs text-red-400">{errors.geometry}</p>
              )}
            </div>

            <div className="flex gap-3 pt-2">
              <button
                type="submit"
                id="submit-site-btn"
                disabled={loading || !drawnGeometry}
                className="btn-primary"
              >
                {loading ? 'Saving...' : 'Save Site'}
              </button>
              <button
                type="button"
                onClick={() => navigate(`/projects/${projectId}`)}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>

        {/* Map */}
        <div className="lg:col-span-3">
          <div className="relative h-[600px] w-full rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
            {!MAPBOX_TOKEN ? (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-900 text-slate-500 text-sm text-center p-8">
                <div>
                  <p className="font-medium mb-2">Mapbox token required</p>
                  <p className="text-xs">Set VITE_MAPBOX_TOKEN in your .env file to enable the polygon drawing tool.</p>
                </div>
              </div>
            ) : (
              <>
                <div
                  ref={mapContainer}
                  className="w-full h-full min-h-[600px]"
                  style={{ width: '100%', height: '100%', minHeight: '600px' }}
                />
                {/* Map instruction overlay */}
                <div className="absolute top-4 left-4 bg-slate-900/90 backdrop-blur-sm px-3 py-2 rounded-lg text-xs text-slate-400 pointer-events-none z-10">
                  {drawMode
                    ? '🖱 Click to place vertices · Double-click to finish'
                    : drawnGeometry
                    ? '✅ Polygon ready — submit the form'
                    : '→ Click "Draw Polygon" then click on the map'}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
