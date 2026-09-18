// Project Details page
import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
import { projectsService } from '../services/projects';
import { sitesService } from '../services/sites';
import type { Project, Site } from '../types';
import {
  formatArea,
  formatBioScore,
  formatCarbonValue,
  formatDate,
  getProjectTypeLabel,
  getStatusBadgeClass,
} from '../utils';
import toast from 'react-hot-toast';

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string;

export default function ProjectDetails() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<mapboxgl.Map | null>(null);
  // Initialized flag prevents duplicate Map instances under React StrictMode
  const initialized = useRef(false);

  useEffect(() => {
    const id = parseInt(projectId!);
    Promise.all([
      projectsService.getProject(id),
      sitesService.getProjectSites(id),
    ])
      .then(([proj, sitesResp]) => {
        setProject(proj);
        setSites(sitesResp.data);
      })
      .catch(() => setError('Failed to load project.'))
      .finally(() => setLoading(false));
  }, [projectId]);

  // Initialize Mapbox when project data is ready
  useEffect(() => {
    if (initialized.current || !project || !mapContainer.current || !MAPBOX_TOKEN) return;

    if (!MAPBOX_TOKEN) {
      if (import.meta.env.DEV) {
        console.error('[ProjectDetails] VITE_MAPBOX_TOKEN is not set. Map will not initialize.');
      }
      return;
    }

    initialized.current = true;
    mapboxgl.accessToken = MAPBOX_TOKEN;
    const m = new mapboxgl.Map({
      container: mapContainer.current,
      style: 'mapbox://styles/mapbox/satellite-streets-v12',
      zoom: 5,
      center: [0, 0],
    });

    m.addControl(new mapboxgl.NavigationControl(), 'top-right');
    map.current = m;

    m.on('load', () => {
      m.resize();
      // Load site GeoJSON
      sitesService.getMapSites(parseInt(projectId!)).then((geojson) => {
        if (geojson.features.length === 0) return;

        m.addSource('sites', { type: 'geojson', data: geojson as never });

        // Fill layer
        m.addLayer({
          id: 'sites-fill',
          type: 'fill',
          source: 'sites',
          paint: {
            'fill-color': '#22c55e',
            'fill-opacity': 0.35,
          },
        });

        // Outline layer
        m.addLayer({
          id: 'sites-outline',
          type: 'line',
          source: 'sites',
          paint: {
            'line-color': '#4ade80',
            'line-width': 2,
          },
        });

        // Fit to bounds
        const coords = geojson.features.flatMap(
          (f) => f.geometry.coordinates[0] as [number, number][]
        );
        if (coords.length > 0) {
          const bounds = coords.reduce(
            (b, c) => b.extend(c as mapboxgl.LngLatLike),
            new mapboxgl.LngLatBounds(coords[0], coords[0])
          );
          m.fitBounds(bounds, { padding: 60 });
        }

        // Click handler
        m.on('click', 'sites-fill', (e) => {
          const props = e.features?.[0]?.properties;
          if (props) {
            navigate(`/sites/${props.id}`);
          }
        });

        m.on('mouseenter', 'sites-fill', () => {
          m.getCanvas().style.cursor = 'pointer';
        });
        m.on('mouseleave', 'sites-fill', () => {
          m.getCanvas().style.cursor = '';
        });
      });
    });

    return () => { m.remove(); map.current = null; initialized.current = false; };
  }, [project, projectId, navigate]);

  const handleDeleteProject = async () => {
    if (!project) return;
    if (!window.confirm(`Delete "${project.name}" and all its sites? This cannot be undone.`)) return;
    try {
      await projectsService.deleteProject(project.id);
      toast.success('Project deleted.');
      navigate('/projects');
    } catch {
      toast.error('Failed to delete project.');
    }
  };

  if (loading) return <div className="p-6"><div className="card h-96 animate-pulse bg-slate-800" /></div>;
  if (error) return <div className="p-6"><div className="card text-red-400">{error}</div></div>;
  if (!project) return null;

  return (
    <div className="p-6 max-w-screen-xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <Link to="/projects" className="text-slate-500 hover:text-slate-300 text-sm">
              ← Projects
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-slate-100">{project.name}</h1>
          <p className="text-slate-500 text-sm">{project.region || 'No region specified'}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={getStatusBadgeClass(project.status)}>{project.status}</span>
          <Link to={`/projects/${project.id}/sites/new`} className="btn-primary">
            + Add Site
          </Link>
          <button onClick={handleDeleteProject} className="btn-danger">Delete</button>
        </div>
      </div>

      {/* Summary + Map */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Summary card */}
        <div className="card space-y-4">
          <h2 className="font-semibold text-slate-200">Project Summary</h2>
          <div className="space-y-3 text-sm">
            <Row label="Type" value={getProjectTypeLabel(project.project_type)} />
            <Row label="Status" value={project.status} />
            <Row label="Sites" value={project.site_count.toString()} />
            <Row label="Total Area" value={formatArea(project.total_area_hectares)} />
            <Row label="Started" value={formatDate(project.start_date)} />
            <Row label="Created" value={formatDate(project.created_at)} />
          </div>
          {project.description && (
            <p className="text-sm text-slate-400 pt-2 border-t border-slate-800">
              {project.description}
            </p>
          )}
        </div>

        {/* Map */}
        <div className="lg:col-span-2">
          <div className="relative h-80 rounded-xl overflow-hidden border border-slate-800">
            {!MAPBOX_TOKEN ? (
              <div className="absolute inset-0 flex items-center justify-center bg-slate-900 text-slate-500 text-sm">
                Add VITE_MAPBOX_TOKEN to .env to enable map
              </div>
            ) : (
              <div
                ref={mapContainer}
                className="w-full h-full min-h-[320px]"
                style={{ width: '100%', height: '100%', minHeight: '320px' }}
              />
            )}
            {sites.length === 0 && MAPBOX_TOKEN && (
              <div className="absolute bottom-4 left-4 bg-slate-900/80 backdrop-blur-sm px-3 py-2 rounded-lg text-xs text-slate-400">
                No sites yet — Add a site to see polygons on the map
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Sites Table */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title mb-0">Sites ({sites.length})</h2>
          <Link to={`/projects/${project.id}/sites/new`} className="btn-secondary text-sm">
            + Add Site
          </Link>
        </div>

        {sites.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-slate-400 mb-2">No sites associated with this project</p>
            <p className="text-slate-600 text-sm mb-4">Add a site and draw a polygon to start monitoring.</p>
            <Link to={`/projects/${project.id}/sites/new`} className="btn-primary">
              Add First Site
            </Link>
          </div>
        ) : (
          <div className="card overflow-hidden p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800">
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">Site Name</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">Area</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">Status</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">Carbon</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">Biodiversity</th>
                  <th className="text-left px-4 py-3 text-slate-500 font-medium">Last Monitoring</th>
                  <th className="px-4 py-3" />
                </tr>
              </thead>
              <tbody>
                {sites.map((site, i) => (
                  <tr
                    key={site.id}
                    className={`border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${
                      i === sites.length - 1 ? 'border-none' : ''
                    }`}
                  >
                    <td className="px-4 py-3 font-medium text-slate-200">{site.name}</td>
                    <td className="px-4 py-3 text-slate-400">{formatArea(site.area_hectares)}</td>
                    <td className="px-4 py-3">
                      <span className={getStatusBadgeClass(site.status)}>{site.status}</span>
                    </td>
                    <td className="px-4 py-3 text-amber-400">{formatCarbonValue(site.latest_carbon_value)}</td>
                    <td className="px-4 py-3 text-emerald-400">{formatBioScore(site.latest_biodiversity_score)}</td>
                    <td className="px-4 py-3 text-slate-400">{formatDate(site.monitoring_date)}</td>
                    <td className="px-4 py-3">
                      <Link to={`/sites/${site.id}`} className="text-earth-400 hover:text-earth-300 text-xs font-medium">
                        Analytics →
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-500">{label}</span>
      <span className="text-slate-300">{value}</span>
    </div>
  );
}
