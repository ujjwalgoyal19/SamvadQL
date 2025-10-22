import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../../store';
import { toggleSidebar } from '../../store/slices/uiSlice';
import { useUser } from '../../context/UserContext';
import { apiService } from '@/services/api';
import {
  LayoutDashboard,
  Search,
  Table,
  History,
  Settings,
  Menu,
  X,
  LogOut,
  User
} from 'lucide-react';

interface AppLayoutProps {
  children: React.ReactNode;
}

const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const { state: userState, dispatch: userDispatch } = useUser();
  const { sidebarOpen } = useSelector((state: RootState) => state.ui);

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/query', label: 'Query', icon: Search },
    { path: '/tables', label: 'Tables', icon: Table },
    { path: '/history', label: 'History', icon: History },
    { path: '/settings', label: 'Settings', icon: Settings }
  ];

  const handleLogout = () => {
    // Clear the in-memory auth token to prevent unauthorized API calls
    apiService.clearAuthToken();

    // Clear user state
    userDispatch({ type: 'SIGNOUT' });

    // Redirect to signin page
    navigate('/signin');
  };

  const handleToggleSidebar = () => {
    dispatch(toggleSidebar());
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside
        className={`
          fixed inset-y-0 left-0 z-50 w-64 bg-card border-r border-border
          transform transition-transform duration-200 ease-in-out
          lg:translate-x-0 lg:static lg:inset-0
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        {/* Logo */}
        <div className="flex items-center justify-between h-16 px-6 border-b border-border">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg">
                S
              </span>
            </div>
            <span className="text-xl font-bold text-foreground">SamvadQL</span>
          </div>
          <button
            onClick={handleToggleSidebar}
            className="lg:hidden text-muted-foreground hover:text-foreground"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-6 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`
                  flex items-center space-x-3 px-4 py-3 rounded-lg
                  transition-colors duration-150
                  ${
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  }
                `}
                onClick={() => {
                  if (window.innerWidth < 1024) {
                    dispatch(toggleSidebar());
                  }
                }}
              >
                <Icon className="w-5 h-5" />
                <span className="font-medium">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* User Profile Section */}
        <div className="border-t border-border p-4">
          <div className="flex items-center space-x-3 px-4 py-3 rounded-lg bg-accent">
            <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-primary-foreground" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-foreground truncate">
                {userState.user?.name || userState.user?.email}
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {userState.user?.email}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="
              w-full mt-2 flex items-center space-x-3 px-4 py-3 rounded-lg
              text-muted-foreground hover:bg-destructive/10 hover:text-destructive
              transition-colors duration-150
            "
          >
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile Header */}
        <header className="lg:hidden flex items-center justify-between h-16 px-4 bg-card border-b border-border">
          <button
            onClick={handleToggleSidebar}
            className="text-muted-foreground hover:text-foreground"
          >
            <Menu className="w-6 h-6" />
          </button>
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-primary-foreground font-bold text-lg">
                S
              </span>
            </div>
            <span className="text-xl font-bold text-foreground">SamvadQL</span>
          </div>
          <div className="w-6" /> {/* Spacer for alignment */}
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto">{children}</main>
      </div>

      {/* Overlay for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={handleToggleSidebar}
        />
      )}
    </div>
  );
};

export default AppLayout;
