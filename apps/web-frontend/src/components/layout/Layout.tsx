import React from 'react';
import { useAppSelector, useAppDispatch } from '@/store/hooks';
import { toggleSidebar, setActiveTab } from '@/store/slices/uiSlice';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Menu, Database, History, MessageSquare } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const dispatch = useAppDispatch();
  const { sidebarOpen, activeTab } = useAppSelector((state) => state.ui);

  const handleTabChange = (value: string) => {
    dispatch(setActiveTab(value as 'query' | 'history' | 'tables'));
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b bg-card">
        <div className="flex items-center justify-between px-4 py-4">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => dispatch(toggleSidebar())}
              className="md:hidden"
            >
              <Menu className="h-4 w-4" />
            </Button>
            <h1 className="text-2xl font-bold text-primary">SamvadQL</h1>
          </div>

          <Tabs
            value={activeTab}
            onValueChange={handleTabChange}
            className="hidden md:flex"
          >
            <TabsList>
              <TabsTrigger value="query" className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4" />
                Query
              </TabsTrigger>
              <TabsTrigger value="tables" className="flex items-center gap-2">
                <Database className="h-4 w-4" />
                Tables
              </TabsTrigger>
              <TabsTrigger value="history" className="flex items-center gap-2">
                <History className="h-4 w-4" />
                History
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>
      </header>

      <div className="flex h-[calc(100vh-73px)]">
        {/* Mobile Navigation */}
        <div className="md:hidden">
          <Tabs
            value={activeTab}
            onValueChange={handleTabChange}
            orientation="vertical"
          >
            <TabsList
              className={`fixed left-0 top-[73px] z-40 h-full w-64 transform transition-transform ${
                sidebarOpen ? 'translate-x-0' : '-translate-x-full'
              } bg-card border-r flex-col justify-start p-4`}
            >
              <TabsTrigger value="query" className="w-full justify-start gap-2">
                <MessageSquare className="h-4 w-4" />
                Query
              </TabsTrigger>
              <TabsTrigger
                value="tables"
                className="w-full justify-start gap-2"
              >
                <Database className="h-4 w-4" />
                Tables
              </TabsTrigger>
              <TabsTrigger
                value="history"
                className="w-full justify-start gap-2"
              >
                <History className="h-4 w-4" />
                History
              </TabsTrigger>
            </TabsList>
          </Tabs>
        </div>

        {/* Main Content */}
        <main className="flex-1 overflow-hidden">{children}</main>
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/50 md:hidden"
          onClick={() => dispatch(toggleSidebar())}
        />
      )}
    </div>
  );
}
