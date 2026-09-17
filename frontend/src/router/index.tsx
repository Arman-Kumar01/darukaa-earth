// App router with protected routes
import { Navigate, Route, Routes } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import AppLayout from '../components/layout/AppLayout';
import Dashboard from '../pages/Dashboard';
import Login from '../pages/Login';
import Register from '../pages/Register';
import Projects from '../pages/Projects';
import ProjectDetails from '../pages/ProjectDetails';
import SiteDetails from '../pages/SiteDetails';
import MapExplorer from '../pages/MapExplorer';
import CreateProject from '../pages/CreateProject';
import AddSite from '../pages/AddSite';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();
  return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" replace />;
}

export default function AppRouter() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <Register />
          </PublicRoute>
        }
      />

      {/* Protected routes with sidebar layout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="projects" element={<Projects />} />
        <Route path="projects/new" element={<CreateProject />} />
        <Route path="projects/:projectId" element={<ProjectDetails />} />
        <Route path="projects/:projectId/sites/new" element={<AddSite />} />
        <Route path="sites/:siteId" element={<SiteDetails />} />
        <Route path="map" element={<MapExplorer />} />
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
