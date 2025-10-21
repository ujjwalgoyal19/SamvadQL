import { Routes, Route } from "react-router";
import Layout from "@/components/layout/Layout";
import HomePage from "./pages/HomePage";
import SignIn from "@/pages/signin";
import SignUpPage from "@/pages/signup";
import ForgotPasswordPage from "@/pages/forgot-password";
import ResetPasswordPage from "@/pages/reset-password";
import { UserProvider, useUser } from "./context/UserContext";

function AppContent() {
  const { state } = useUser();
  const isAuthenticated = !!state.user;
  return (
    <Layout>
      {isAuthenticated ? (
        <Routes>
          <Route path="/" element={<HomePage />} />
        </Routes>
      ) : (
        <Routes>
          <Route path="/signin" element={<SignIn />} />
          <Route path="/signup" element={<SignUpPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="*" element={<SignIn />} />
        </Routes>
      )}
    </Layout>
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
