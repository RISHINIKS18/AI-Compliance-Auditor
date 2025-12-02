import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardLayout from './components/layout/DashboardLayout';
import DashboardPage from './pages/DashboardPage';
import PoliciesPage from './pages/PoliciesPage';
import AuditsPage from './pages/AuditsPage';
import ViolationsPage from './pages/ViolationsPage';
import SettingsPage from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <Toaster position="top-right" />
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <ErrorBoundary>
                      <DashboardLayout />
                    </ErrorBoundary>
                  </ProtectedRoute>
                }
              >
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route 
                  path="dashboard" 
                  element={
                    <ErrorBoundary>
                      <DashboardPage />
                    </ErrorBoundary>
                  } 
                />
                <Route 
                  path="policies" 
                  element={
                    <ErrorBoundary>
                      <PoliciesPage />
                    </ErrorBoundary>
                  } 
                />
                <Route 
                  path="audits" 
                  element={
                    <ErrorBoundary>
                      <AuditsPage />
                    </ErrorBoundary>
                  } 
                />
                <Route 
                  path="violations" 
                  element={
                    <ErrorBoundary>
                      <ViolationsPage />
                    </ErrorBoundary>
                  } 
                />
                <Route 
                  path="settings" 
                  element={
                    <ErrorBoundary>
                      <SettingsPage />
                    </ErrorBoundary>
                  } 
                />
              </Route>
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
