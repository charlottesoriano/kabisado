import React from 'react';
import { Home, Layers, UploadCloud, BarChart2 } from 'lucide-react';

export type MobileTab = 'home' | 'decks' | 'upload' | 'progress';

interface MobileTabBarProps {
  activeTab: MobileTab;
  onTabChange: (tab: MobileTab) => void;
}

export const MobileTabBar: React.FC<MobileTabBarProps> = ({
  activeTab,
  onTabChange,
}) => {
  const tabs: { id: MobileTab; label: string; icon: React.ReactNode }[] = [
    { id: 'home', label: 'Home', icon: <Home className="w-5 h-5" strokeWidth={2} /> },
    { id: 'decks', label: 'Decks', icon: <Layers className="w-5 h-5" strokeWidth={2} /> },
    { id: 'upload', label: 'Upload', icon: <UploadCloud className="w-5 h-5" strokeWidth={2} /> },
    { id: 'progress', label: 'Progress', icon: <BarChart2 className="w-5 h-5" strokeWidth={2} /> },
  ];

  return (
    <div
      className="sticky bottom-0 left-0 right-0 z-40 border-t flex items-center justify-around px-2 py-1.5 transition-colors"
      style={{
        backgroundColor: '#FFFFFF',
        borderColor: '#B8D3D1',
      }}
    >
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            onClick={() => onTabChange(tab.id)}
            className={`flex-1 min-h-[48px] flex flex-col items-center justify-center gap-1 rounded-xl transition-all cursor-pointer ${
              isActive ? 'text-[#1A281F] font-bold' : 'text-[#635255] hover:text-[#1A281F]'
            }`}
          >
            <div
              className={`p-1 rounded-lg transition-all ${
                isActive ? 'border' : ''
              }`}
              style={{
                backgroundColor: isActive ? '#A7E8BD' : 'transparent',
                borderColor: isActive ? '#1A281F' : 'transparent',
              }}
            >
              {tab.icon}
            </div>
            <span className="text-[10px] tracking-tight">
              {tab.label}
            </span>
          </button>
        );
      })}
    </div>
  );
};
