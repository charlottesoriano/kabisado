import React from 'react';

export type ChipVariant =
  | 'frozen-water' // #C7EAE4 (topic chips, highlighted numbers)
  | 'pale-sky' // #C0E8F9 (topic chips)
  | 'jasmine' // #FFD972 (due-count badges, hints)
  | 'celadon' // #A7E8BD (correct status, good)
  | 'powder-blush' // #FCBCB8 (wrong-answer background)
  | 'outline';

interface ChipProps {
  children: React.ReactNode;
  variant?: ChipVariant;
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Chip: React.FC<ChipProps> = ({
  children,
  variant = 'frozen-water',
  size = 'sm',
  icon,
  className = '',
  onClick,
}) => {
  const sizeClasses = size === 'sm' ? 'px-2.5 py-0.5 text-[12px]' : 'px-3 py-1 text-[13px]';

  const styles: Record<ChipVariant, React.CSSProperties> = {
    'frozen-water': {
      backgroundColor: '#C7EAE4',
      color: '#1A281F',
      border: '1px solid #B8D3D1',
    },
    'pale-sky': {
      backgroundColor: '#C0E8F9',
      color: '#1A281F',
      border: '1px solid #B8D3D1',
    },
    jasmine: {
      backgroundColor: '#FFD972',
      color: '#1A281F',
      border: '1px solid #B8D3D1',
    },
    celadon: {
      backgroundColor: '#A7E8BD',
      color: '#1A281F',
      border: '1px solid #A7E8BD',
    },
    'powder-blush': {
      backgroundColor: '#FCBCB8',
      color: '#1A281F',
      border: '1px solid #EFA7A7',
    },
    outline: {
      backgroundColor: '#FFFFFF',
      color: '#635255',
      border: '1px solid #B8D3D1',
    },
  };

  const isClickable = !!onClick;

  return (
    <span
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 font-medium rounded-full select-none shrink-0 ${sizeClasses} ${
        isClickable ? 'cursor-pointer hover:opacity-90 active:scale-95' : ''
      } ${className}`}
      style={styles[variant]}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};
