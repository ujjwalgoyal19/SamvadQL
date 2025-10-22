import React from 'react';
import { Link } from 'react-router';

interface AuthLayoutProps {
  children: React.ReactNode;
}

const AuthLayout = ({ children }: AuthLayoutProps) => {
  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      {/* Logo/Branding */}
      <div className="flex justify-center pt-12 pb-6">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center shadow-lg">
            <span className="text-primary-foreground font-bold text-2xl">
              S
            </span>
          </div>
          <span className="text-3xl font-bold text-foreground">SamvadQL</span>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">{children}</div>
      </div>

      {/* Footer */}
      <footer className="py-6 px-4 text-center">
        <div className="flex justify-center space-x-6 text-sm text-muted-foreground">
          <Link to="/terms" className="hover:text-foreground transition-colors">
            Terms of Service
          </Link>
          <Link
            to="/privacy"
            className="hover:text-foreground transition-colors"
          >
            Privacy Policy
          </Link>
          <Link to="/help" className="hover:text-foreground transition-colors">
            Help
          </Link>
        </div>
        <p className="mt-4 text-xs text-muted-foreground">
          © {new Date().getFullYear()} SamvadQL. All rights reserved.
        </p>
      </footer>
    </div>
  );
};

export default AuthLayout;
