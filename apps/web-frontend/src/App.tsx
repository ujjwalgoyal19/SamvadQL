import { Routes, Route, Navigate, useLocation } from 'react-router';
import AppLayout from '@/components/layout/AppLayout';
import AuthLayout from '@/components/layout/AuthLayout';
import HomePage from './pages/HomePage';
import SignIn from '@/pages/signin';
import SignUpPage from '@/pages/signup';
import ForgotPasswordPage from '@/pages/forgot-password';
import ResetPasswordPage from '@/pages/reset-password';
import { UserProvider, useUser } from './context/UserContext';

// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { state } = useUser();
  const location = useLocation();
  const isAuthenticated = !!state.user;

  if (!isAuthenticated) {
    return <Navigate to="/signin" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

// Auth Route wrapper (redirect to home if already authenticated)
function AuthRoute({ children }: { children: React.ReactNode }) {
  const { state } = useUser();
  const isAuthenticated = !!state.user;

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

function AppContent() {
  return (
    <Routes>
      {/* Authenticated Routes with AppLayout */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout>
              <HomePage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/query"
        element={
          <ProtectedRoute>
            <AppLayout>
              <HomePage />
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/tables"
        element={
          <ProtectedRoute>
            <AppLayout>
              <div className="p-8">Tables Page (Coming Soon)</div>
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <AppLayout>
              <div className="p-8">History Page (Coming Soon)</div>
            </AppLayout>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <AppLayout>
              <div className="p-8">Settings Page (Coming Soon)</div>
            </AppLayout>
          </ProtectedRoute>
        }
      />

      {/* Unauthenticated Routes with AuthLayout */}
      <Route
        path="/signin"
        element={
          <AuthRoute>
            <AuthLayout>
              <SignIn />
            </AuthLayout>
          </AuthRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <AuthRoute>
            <AuthLayout>
              <SignUpPage />
            </AuthLayout>
          </AuthRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <AuthRoute>
            <AuthLayout>
              <ForgotPasswordPage />
            </AuthLayout>
          </AuthRoute>
        }
      />
      <Route
        path="/reset-password"
        element={
          <AuthRoute>
            <AuthLayout>
              <ResetPasswordPage />
            </AuthLayout>
          </AuthRoute>
        }
      />

      {/* Catch-all redirect */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <UserProvider>
      <AppContent />
    </UserProvider>
  );
}

export default App;
