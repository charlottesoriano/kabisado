import React from 'react';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showSubtitle?: boolean;
  subtitle?: string;
  inverted?: boolean;
}

export const Logo: React.FC<LogoProps> = ({
  size = 'md',
  showSubtitle = false,
  subtitle = 'Reviewer',
  inverted = false,
}) => {
  const iconSize = size === 'sm' ? 24 : size === 'lg' ? 36 : 28;
  const textSize = size === 'sm' ? 'text-lg' : size === 'lg' ? 'text-2xl' : 'text-xl';

  return (
    <div className="flex items-center gap-2.5 select-none shrink-0">
      {/* 2px stroke line card-stack icon with Evergreen and Celadon accents */}
      <div
        className="relative flex items-center justify-center rounded-xl p-1.5 transition-transform"
        style={{
          width: iconSize + 12,
          height: iconSize + 12,
          backgroundColor: inverted ? '#1A281F' : '#A7E8BD',
          border: inverted ? '1.5px solid #A7E8BD' : '1.5px solid #1A281F',
        }}
        aria-hidden="true"
      >
        <svg
          width={iconSize}
          height={iconSize}
          viewBox="0 0 24 24"
          fill="none"
          stroke={inverted ? '#A7E8BD' : '#1A281F'}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {/* Back card */}
          <rect x="3" y="3" width="14" height="15" rx="3" fill="none" opacity="0.6" />
          {/* Middle card */}
          <rect x="5" y="5" width="14" height="15" rx="3" fill="none" opacity="0.8" />
          {/* Front card with check/spark */}
          <rect x="7" y="7" width="14" height="15" rx="3" fill={inverted ? '#1A281F' : '#FFFFFF'} />
          <path d="M10 14.5l2.5 2.5 5-5" strokeLinecap="round" />
        </svg>
      </div>

      <div className="flex flex-col leading-none">
        <span
          className={`font-heading font-bold tracking-tight ${textSize}`}
          style={{ color: inverted ? '#FFFFFF' : '#1A281F' }}
        >
          Kabisado
        </span>
        {showSubtitle && (
          <span
            className="text-[11px] font-medium tracking-wider uppercase mt-0.5"
            style={{ color: inverted ? '#C7EAE4' : '#635255' }}
          >
            {subtitle}
          </span>
        )}
      </div>
    </div>
  );
};
