import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export interface RouteParams {
  [key: string]: string | undefined;
}

interface RouterContextType {
  pathname: string;
  params: RouteParams;
  query: Record<string, string>;
  push: (url: string) => void;
  replace: (url: string) => void;
  back: () => void;
}

const RouterContext = createContext<RouterContextType | null>(null);

// Helper to parse query parameters from URL string
const parseQuery = (url: string): Record<string, string> => {
  const queryIndex = url.indexOf('?');
  if (queryIndex === -1) return {};
  const queryString = url.slice(queryIndex + 1);
  const searchParams = new URLSearchParams(queryString);
  const result: Record<string, string> = {};
  searchParams.forEach((value, key) => {
    result[key] = value;
  });
  return result;
};

// Helper to extract pathname without hash or query
const extractPathname = (url: string): string => {
  const withoutHash = url.split('#')[0];
  const withoutQuery = withoutHash.split('?')[0];
  return withoutQuery || '/';
};

export const NextRouterProvider: React.FC<{
  children: React.ReactNode;
  initialPath?: string;
}> = ({ children, initialPath }) => {
  const getInitialPath = () => {
    if (initialPath) return initialPath;
    if (typeof window !== 'undefined') {
      const current = window.location.pathname;
      return current && current !== '/' ? current : '/dashboard';
    }
    return '/dashboard';
  };

  const [currentUrl, setCurrentUrl] = useState<string>(getInitialPath);

  // Sync with browser history popstate (back/forward)
  useEffect(() => {
    const handlePopState = () => {
      setCurrentUrl(window.location.pathname + window.location.search);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const push = useCallback((url: string) => {
    setCurrentUrl(url);
    if (typeof window !== 'undefined') {
      window.history.pushState({}, '', url);
    }
  }, []);

  const replace = useCallback((url: string) => {
    setCurrentUrl(url);
    if (typeof window !== 'undefined') {
      window.history.replaceState({}, '', url);
    }
  }, []);

  const back = useCallback(() => {
    if (typeof window !== 'undefined') {
      window.history.back();
    }
  }, []);

  const pathname = extractPathname(currentUrl);
  const query = parseQuery(currentUrl);

  // Extract dynamic params like [id]
  const extractParams = (path: string): RouteParams => {
    const params: RouteParams = {};
    const deckMatch = path.match(/^\/decks\/([^/?]+)/);
    if (deckMatch) params.id = deckMatch[1];

    const reviewMatch = path.match(/^\/review\/([^/?]+)/);
    if (reviewMatch) params.id = reviewMatch[1];

    const quizMatch = path.match(/^\/quiz\/([^/?]+)/);
    if (quizMatch) params.id = quizMatch[1];

    const problemMatch = path.match(/^\/problems\/([^/?]+)/);
    if (problemMatch) params.id = problemMatch[1];

    const codingMatch = path.match(/^\/coding\/([^/?]+)/);
    if (codingMatch) params.id = codingMatch[1];

    return params;
  };

  const params = extractParams(pathname);

  return (
    <RouterContext.Provider value={{ pathname, params, query, push, replace, back }}>
      {children}
    </RouterContext.Provider>
  );
};

export const useRouter = (): RouterContextType => {
  const context = useContext(RouterContext);
  if (!context) {
    throw new Error('useRouter must be used within a NextRouterProvider');
  }
  return context;
};

export const usePathname = (): string => {
  const { pathname } = useRouter();
  return pathname;
};

export const useParams = (): RouteParams => {
  const { params } = useRouter();
  return params;
};

export interface LinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  children: React.ReactNode;
  className?: string;
  replace?: boolean;
}

export const Link: React.FC<LinkProps> = ({
  href,
  children,
  className = '',
  replace = false,
  onClick,
  ...rest
}) => {
  const router = useRouter();

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (onClick) onClick(e);
    if (!e.defaultPrevented && !e.metaKey && !e.ctrlKey && !e.shiftKey && !e.altKey && e.button === 0) {
      e.preventDefault();
      if (replace) {
        router.replace(href);
      } else {
        router.push(href);
      }
    }
  };

  return (
    <a href={href} onClick={handleClick} className={className} {...rest}>
      {children}
    </a>
  );
};
