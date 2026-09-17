// Projects list page
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { projectsService } from '../services/projects';
import type { PaginatedResponse, Project } from '../types';
import {
  formatArea,
  formatDate,
  getProjectTypeLabel,
  getStatusBadgeClass,
} from '../utils';

export default function Projects() {
  const [data, setData] = useState<PaginatedResponse<Project> | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [page, setPage] = useState(1);

  const fetchProjects = (s = search, st = statusFilter, t = typeFilter, p = page) => {
    setLoading(true);
    projectsService
      .getProjects({ search: s || undefined, status: st || undefined, project_type: t || undefined, page: p })
      .then(setData)
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchProjects(); }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProjects(search, statusFilter, typeFilter, 1);
  };

  return (
    <div className="p-6 max-w-screen-xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Projects</h1>
          <p className="text-slate-500 text-sm">{data?.total ?? 0} total projects</p>
        </div>
        <Link to="/projects/new" id="create-project-btn" className="btn-primary">
          + New Project
        </Link>
      </div>

      {/* Filters */}
      <form onSubmit={handleSearch} className="flex flex-wrap gap-3 mb-6">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search projects..."
          className="input-field w-64"
          aria-label="Search projects"
        />
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); fetchProjects(search, e.target.value, typeFilter, 1); }}
          className="input-field w-40"
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="completed">Completed</option>
          <option value="planned">Planned</option>
          <option value="paused">Paused</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); fetchProjects(search, statusFilter, e.target.value, 1); }}
          className="input-field w-52"
          aria-label="Filter by type"
        >
          <option value="">All types</option>
          <option value="carbon">Carbon</option>
          <option value="biodiversity">Biodiversity</option>
          <option value="carbon_biodiversity">Carbon + Biodiversity</option>
        </select>
        <button type="submit" className="btn-secondary">Search</button>
      </form>

      {/* Projects grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, i) => (
            <div key={i} className="card h-48 animate-pulse bg-slate-800" />
          ))}
        </div>
      ) : data?.data.length === 0 ? (
        <div className="card text-center py-16">
          <p className="text-slate-400 text-lg mb-2">No projects found</p>
          <p className="text-slate-600 text-sm mb-4">
            {search || statusFilter || typeFilter
              ? 'Try adjusting your filters.'
              : 'Create your first project to get started.'}
          </p>
          <Link to="/projects/new" className="btn-primary">Create Project</Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {data?.data.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>

          {/* Pagination */}
          {data && data.total_pages > 1 && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => { setPage(page - 1); fetchProjects(search, statusFilter, typeFilter, page - 1); }}
                disabled={page === 1}
                className="btn-secondary disabled:opacity-50"
              >
                Previous
              </button>
              <span className="flex items-center text-slate-400 text-sm px-4">
                Page {page} of {data.total_pages}
              </span>
              <button
                onClick={() => { setPage(page + 1); fetchProjects(search, statusFilter, typeFilter, page + 1); }}
                disabled={page === data.total_pages}
                className="btn-secondary disabled:opacity-50"
              >
                Next
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ProjectCard({ project }: { project: Project }) {
  return (
    <Link
      to={`/projects/${project.id}`}
      className="card hover:border-slate-700 transition-all group flex flex-col gap-4"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-slate-100 group-hover:text-earth-400 transition-colors truncate">
            {project.name}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">{project.region || 'No region'}</p>
        </div>
        <span className={getStatusBadgeClass(project.status)}>{project.status}</span>
      </div>

      {project.description && (
        <p className="text-sm text-slate-400 line-clamp-2">{project.description}</p>
      )}

      <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-800">
        <div>
          <p className="text-xs text-slate-600">Type</p>
          <p className="text-sm text-slate-300">{getProjectTypeLabel(project.project_type)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-600">Sites</p>
          <p className="text-sm text-slate-300">{project.site_count}</p>
        </div>
        <div>
          <p className="text-xs text-slate-600">Total Area</p>
          <p className="text-sm text-slate-300">{formatArea(project.total_area_hectares)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-600">Started</p>
          <p className="text-sm text-slate-300">{formatDate(project.start_date)}</p>
        </div>
      </div>
    </Link>
  );
}
