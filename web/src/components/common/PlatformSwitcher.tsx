import React from 'react';
import { PlatformMode, WebScreen, MobileScreen } from '../../types';
import { Monitor, Smartphone, Layers, AlertCircle, WifiOff, Sparkles, FolderX } from 'lucide-react';

interface PlatformSwitcherProps {
  platform: PlatformMode;
  onPlatformChange: (mode: PlatformMode) => void;
  webScreen: WebScreen;
  onWebScreenChange: (screen: WebScreen) => void;
  mobileScreen: MobileScreen;
  onMobileScreenChange: (screen: MobileScreen) => void;
  webViewportWidth: 'full' | '1280' | '768' | '375';
  onWebViewportWidthChange: (width: 'full' | '1280' | '768' | '375') => void;
  // State simulation toggles
  isEmptyState: boolean;
  onToggleEmptyState: () => void;
  isFailedUploadState: boolean;
  onToggleFailedUploadState: () => void;
  isLoadingSkeleton: boolean;
  onToggleLoadingSkeleton: () => void;
  isMobileOffline: boolean;
  onToggleMobileOffline: () => void;
}

export const PlatformSwitcher: React.FC<PlatformSwitcherProps> = ({
  platform,
  onPlatformChange,
  webScreen,
  onWebScreenChange,
  mobileScreen,
  onMobileScreenChange,
  webViewportWidth,
  onWebViewportWidthChange,
  isEmptyState,
  onToggleEmptyState,
  isFailedUploadState,
  onToggleFailedUploadState,
  isLoadingSkeleton,
  onToggleLoadingSkeleton,
  isMobileOffline,
  onToggleMobileOffline,
}) => {
  const webScreensList: { id: WebScreen; label: string }[] = [
    { id: 'dashboard', label: '2. Dashboard' },
    { id: 'deck', label: '4. Deck page (Bio 101)' },
    { id: 'flashcard', label: '5. Flashcard review' },
    { id: 'quiz', label: '6. Quiz (answered)' },
    { id: 'quiz-results', label: '7. Quiz results' },
    { id: 'problem', label: '8. Problem practice' },
    { id: 'coding', label: '9. Coding problem' },
    { id: 'upload', label: '3. Upload notes/PDF' },
    { id: 'signin', label: '1. Sign in (Clerk)' },
  ];

  const mobileScreensList: { id: MobileScreen; label: string }[] = [
    { id: 'home', label: '2. Home & decks' },
    { id: 'flashcard-front', label: '3. Flashcard front' },
    { id: 'flashcard-back', label: '4. Flashcard back' },
    { id: 'quiz-question', label: '5. Quiz question' },
    { id: 'quiz-answered', label: '6. Quiz answered (sheet)' },
    { id: 'problem', label: '7. Problem practice (sheet)' },
    { id: 'signin', label: '1. Sign in' },
  ];

  return (
    <div
      className="sticky top-0 z-50 w-full border-b backdrop-blur-md px-4 py-2.5 transition-colors select-none"
      style={{
        backgroundColor: 'rgba(255, 255, 255, 0.95)',
        borderColor: '#B8D3D1',
      }}
    >
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        {/* Left: Platform Toggle */}
        <div className="flex items-center gap-2">
          <div
            className="flex items-center p-1 rounded-xl border"
            style={{ backgroundColor: '#F3FAF8', borderColor: '#B8D3D1' }}
          >
            <button
              type="button"
              onClick={() => onPlatformChange('web')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                platform === 'web'
                  ? 'bg-[#1A281F] text-white shadow-xs'
                  : 'text-[#635255] hover:text-[#1A281F]'
              }`}
            >
              <Monitor className="w-3.5 h-3.5" strokeWidth={2} />
              <span>Responsive Web (1280px)</span>
            </button>
            <button
              type="button"
              onClick={() => onPlatformChange('mobile')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                platform === 'mobile'
                  ? 'bg-[#1A281F] text-white shadow-xs'
                  : 'text-[#635255] hover:text-[#1A281F]'
              }`}
            >
              <Smartphone className="w-3.5 h-3.5" strokeWidth={2} />
              <span>Mobile App (390×844)</span>
            </button>
          </div>

          {/* Web Viewport Presets if Web */}
          {platform === 'web' && (
            <div className="hidden sm:flex items-center gap-1 text-xs">
              <span className="text-[#635255] font-medium mr-1">Width:</span>
              {(['full', '1280', '768', '375'] as const).map((width) => (
                <button
                  key={width}
                  type="button"
                  onClick={() => onWebViewportWidthChange(width)}
                  className={`px-2 py-1 rounded-md font-mono text-[11px] transition-colors cursor-pointer border ${
                    webViewportWidth === width
                      ? 'bg-[#A7E8BD] text-[#1A281F] border-[#1A281F] font-semibold'
                      : 'bg-white text-[#635255] border-[#B8D3D1] hover:bg-[#F3FAF8]'
                  }`}
                >
                  {width === 'full' ? 'Fluid' : `${width}px`}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Center: Screen Jumper */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-[#635255] flex items-center gap-1">
            <Layers className="w-3.5 h-3.5" strokeWidth={2} />
            <span>Screen:</span>
          </span>
          {platform === 'web' ? (
            <select
              value={webScreen}
              onChange={(e) => onWebScreenChange(e.target.value as WebScreen)}
              className="text-xs font-medium px-2.5 py-1.5 rounded-lg border bg-white text-[#1A281F] border-[#B8D3D1] focus:outline-none focus:border-[#1A281F] cursor-pointer"
            >
              {webScreensList.map((screen) => (
                <option key={screen.id} value={screen.id}>
                  {screen.label}
                </option>
              ))}
            </select>
          ) : (
            <select
              value={mobileScreen}
              onChange={(e) => onMobileScreenChange(e.target.value as MobileScreen)}
              className="text-xs font-medium px-2.5 py-1.5 rounded-lg border bg-white text-[#1A281F] border-[#B8D3D1] focus:outline-none focus:border-[#1A281F] cursor-pointer"
            >
              {mobileScreensList.map((screen) => (
                <option key={screen.id} value={screen.id}>
                  {screen.label}
                </option>
              ))}
            </select>
          )}
        </div>

        {/* Right: States Simulation Toggles */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-[11px] font-semibold text-[#635255] mr-0.5">States:</span>

          <button
            type="button"
            onClick={onToggleLoadingSkeleton}
            title="Toggle loading skeleton state"
            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1 cursor-pointer border ${
              isLoadingSkeleton
                ? 'bg-[#FFD972] text-[#1A281F] border-[#1A281F]'
                : 'bg-white text-[#635255] border-[#B8D3D1] hover:bg-[#F3FAF8]'
            }`}
          >
            <Sparkles className="w-3 h-3" strokeWidth={2} />
            <span>Skeleton</span>
          </button>

          <button
            type="button"
            onClick={onToggleEmptyState}
            title="Toggle empty dashboard state"
            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1 cursor-pointer border ${
              isEmptyState
                ? 'bg-[#FFD972] text-[#1A281F] border-[#1A281F]'
                : 'bg-white text-[#635255] border-[#B8D3D1] hover:bg-[#F3FAF8]'
            }`}
          >
            <FolderX className="w-3 h-3" strokeWidth={2} />
            <span>Empty</span>
          </button>

          <button
            type="button"
            onClick={onToggleFailedUploadState}
            title="Toggle scanned PDF failed upload state"
            className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1 cursor-pointer border ${
              isFailedUploadState
                ? 'bg-[#FCBCB8] text-[#1A281F] border-[#EFA7A7]'
                : 'bg-white text-[#635255] border-[#B8D3D1] hover:bg-[#F3FAF8]'
            }`}
          >
            <AlertCircle className="w-3 h-3" strokeWidth={2} />
            <span>Failed Upload</span>
          </button>

          {platform === 'mobile' && (
            <button
              type="button"
              onClick={onToggleMobileOffline}
              title="Toggle mobile offline banner state"
              className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all flex items-center gap-1 cursor-pointer border ${
                isMobileOffline
                  ? 'bg-[#1A281F] text-white border-[#1A281F]'
                  : 'bg-white text-[#635255] border-[#B8D3D1] hover:bg-[#F3FAF8]'
              }`}
            >
              <WifiOff className="w-3 h-3" strokeWidth={2} />
              <span>Offline</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
