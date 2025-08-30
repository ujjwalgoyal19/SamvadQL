import { useAppSelector } from '@/store/hooks';
import QueryTab from '@/components/QueryTab';
import TablesTab from '@/components/TablesTab';
import HistoryTab from '@/components/HistoryTab';

export default function HomePage() {
  const { activeTab } = useAppSelector((state) => state.ui);

  const renderTabContent = () => {
    switch (activeTab) {
      case 'query':
        return <QueryTab />;
      case 'tables':
        return <TablesTab />;
      case 'history':
        return <HistoryTab />;
      default:
        return <QueryTab />;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Welcome Section - Only show on query tab */}
      {activeTab === 'query' && (
        <div className="border-b bg-card/50 p-6">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-3xl font-bold mb-2">Welcome to SamvadQL</h1>
            <p className="text-muted-foreground">
              Transform natural language questions into precise SQL queries
              using AI
            </p>
          </div>
        </div>
      )}

      {/* Tab Content */}
      <div className="flex-1 overflow-hidden">{renderTabContent()}</div>
    </div>
  );
}
