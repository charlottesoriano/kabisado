import React from 'react';
import { WebNavbar } from '../components/web/WebNavbar';
import { usePathname, useRouter } from '../lib/router';

interface RootLayoutProps {
  children: React.ReactNode;
  webViewportWidth?: 'full' | '1280' | '768' | '375';
}

/**
 * Next.js Root Layout Component
 * Following Next.js App Router layout conventions:
 * - Persistent Navbar across routes
 * - Conditionally unmounts navigation during focus review mode and sign-in
 * - Handles viewport container width adjustments
 */
export const RootLayout: React.FC<RootLayoutProps> = ({
  children,
  webViewportWidth = '1280',
}) => {
  const pathname = usePathname();
  const router = useRouter();

  // Exclude navbar in full-screen focus modes or authentication
  const isFocusMode = pathname.startsWith('/review/') || pathname === '/sign-in';

  const getViewportContainerClass = () => {
    switch (webViewportWidth) {
      case '1280':
        return 'max-w-[1280px] mx-auto border-x shadow-xs';
      case '768':
        return 'max-w-[768px] mx-auto border-x shadow-xs';
      case '375':
        return 'max-w-[375px] mx-auto border-x shadow-xs';
      default:
        return 'w-full';
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#F3FAF8] text-[#1A281F]">
      {/* Persistent Web Navigation bar following Next.js Root Layout pattern */}
      {!isFocusMode && (
        <WebNavbar
          onNewDeckClick={() => router.push('/upload')}
        />
      )}

      {/* Main Viewport Container */}
      <main
        className={`flex-1 transition-all ${getViewportContainerClass()}`}
        style={{
          backgroundColor: '#F3FAF8',
          borderColor: '#B8D3D1',
        }}
      >
        {children}
      </main>
    </div>
  );
};

export default RootLayout;
