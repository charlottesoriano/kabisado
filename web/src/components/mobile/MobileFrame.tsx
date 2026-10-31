import React from 'react';
import { Wifi, Battery, Signal, WifiOff } from 'lucide-react';

interface MobileFrameProps {
  children: React.ReactNode;
  isOffline?: boolean;
}

export const MobileFrame: React.FC<MobileFrameProps> = ({
  children,
  isOffline = false,
}) => {
  return (
    <div className="py-6 px-4 flex justify-center items-center min-h-[calc(100vh-100px)]">
      {/* 390x844 Phone Shell */}
      <div
        className="w-[390px] h-[844px] rounded-[44px] border-[10px] shadow-2xl relative overflow-hidden flex flex-col select-none"
        style={{
          borderColor: '#1A281F',
          backgroundColor: '#F3FAF8',
        }}
      >
        {/* iOS Dynamic Island / Speaker */}
        <div className="absolute top-2.5 left-1/2 -translate-x-1/2 w-28 h-6 bg-[#1A281F] rounded-full z-50 flex items-center justify-between px-3">
          <div className="w-2.5 h-2.5 rounded-full bg-[#1A281F]/80" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-950" />
        </div>

        {/* Top Status Bar: 9:41, WiFi, Signal, Battery */}
        <div className="h-11 px-6 pt-2 flex items-center justify-between text-xs font-semibold shrink-0 z-40 text-[#1A281F]">
          <span className="font-heading">9:41</span>
          <div className="flex items-center gap-1.5">
            <Signal className="w-3.5 h-3.5" strokeWidth={2.5} />
            <Wifi className="w-3.5 h-3.5" strokeWidth={2.5} />
            <Battery className="w-4 h-4" strokeWidth={2.5} />
          </div>
        </div>

        {/* Offline Banner on Mobile (if enabled) */}
        {isOffline && (
          <div
            className="px-4 py-2 border-b flex items-center gap-2 text-xs font-medium z-40 shrink-0"
            style={{
              backgroundColor: '#1A281F',
              color: '#FFFFFF',
              borderColor: '#1A281F',
            }}
          >
            <WifiOff className="w-3.5 h-3.5 text-[#FFD972] shrink-0" strokeWidth={2.5} />
            <span className="truncate">
              Offline mode · Reviews will sync when connected
            </span>
          </div>
        )}

        {/* Scrollable Viewport Body */}
        <div className="flex-1 overflow-y-auto relative flex flex-col">
          {children}
        </div>

        {/* Bottom Home Indicator */}
        <div className="h-5 w-full flex items-center justify-center shrink-0 bg-transparent pointer-events-none pb-1 z-50">
          <div className="w-32 h-1 bg-[#1A281F]/40 rounded-full" />
        </div>
      </div>
    </div>
  );
};
