// Create Project page
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectsService } from '../services/projects';
import type { ProjectCreate } from '../types';
import { getApiErrorMessage } from '../utils';
import toast from 'react-hot-toast';

export default function CreateProject() {
  const navigate = useNavigate();
  const [form, setForm] = useState<ProjectCreate>({
    name: '',
    description: '',
    project_type: 'carbon',
    region: '',
    status: 'active',
    start_date: '',
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!form.name.trim()) errs.name = 'Project name is required.';
    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
    setErrors((prev) => ({ ...prev, [e.target.name]: '' }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;
    setLoading(true);
    try {
      const created = await projectsService.createProject({
        ...form,
        start_date: form.start_date || undefined,
        description: form.description || undefined,
        region: form.region || undefined,
      });
      toast.success('Project created successfully!');
      navigate(`/projects/${created.id}`);
    } catch (err) {
      toast.error(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Create Project</h1>
        <p className="text-slate-500 text-sm mt-0.5">
          Define an environmental project to start adding monitoring sites.
        </p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label htmlFor="proj-name" className="label">Project name *</label>
            <input
              id="proj-name"
              name="name"
              type="text"
              value={form.name}
              onChange={handleChange}
              className="input-field"
              placeholder="e.g. Green Horizon Restoration"
            />
            {errors.name && <p className="mt-1 text-xs text-red-400">{errors.name}</p>}
          </div>

          <div>
            <label htmlFor="proj-desc" className="label">Description</label>
            <textarea
              id="proj-desc"
              name="description"
              value={form.description}
              onChange={handleChange}
              className="input-field h-24 resize-none"
              placeholder="Describe the project goals and scope..."
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="proj-type" className="label">Project type</label>
              <select
                id="proj-type"
                name="project_type"
                value={form.project_type}
                onChange={handleChange}
                className="input-field"
              >
                <option value="carbon">Carbon</option>
                <option value="biodiversity">Biodiversity</option>
                <option value="carbon_biodiversity">Carbon + Biodiversity</option>
              </select>
            </div>

            <div>
              <label htmlFor="proj-status" className="label">Status</label>
              <select
                id="proj-status"
                name="status"
                value={form.status}
                onChange={handleChange}
                className="input-field"
              >
                <option value="active">Active</option>
                <option value="planned">Planned</option>
                <option value="paused">Paused</option>
                <option value="completed">Completed</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="proj-region" className="label">Region / Location</label>
              <input
                id="proj-region"
                name="region"
                type="text"
                value={form.region}
                onChange={handleChange}
                className="input-field"
                placeholder="e.g. Pará, Brazil"
              />
            </div>

            <div>
              <label htmlFor="proj-start" className="label">Start date</label>
              <input
                id="proj-start"
                name="start_date"
                type="date"
                value={form.start_date}
                onChange={handleChange}
                className="input-field"
              />
            </div>
          </div>

          <div className="flex gap-3 pt-2">
            <button
              type="submit"
              id="submit-project-btn"
              disabled={loading}
              className="btn-primary"
            >
              {loading ? 'Creating...' : 'Create Project'}
            </button>
            <button
              type="button"
              onClick={() => navigate('/projects')}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
