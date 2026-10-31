import React from 'react';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
  variant?: 'white' | 'evergreen' | 'frozen';
  radius?: 'normal' | 'large'; // 14-16px or 20-24px for flashcards
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'white',
  radius = 'normal',
  style,
  ...props
}) => {
  const radiusClass = radius === 'large' ? 'rounded-[22px]' : 'rounded-[16px]';

  const baseStyles: Record<string, React.CSSProperties> = {
    white: {
      backgroundColor: '#FFFFFF',
      borderColor: '#B8D3D1',
      borderWidth: '1px',
      color: '#1A281F',
    },
    evergreen: {
      backgroundColor: '#1A281F',
      borderColor: '#1A281F',
      borderWidth: '1px',
      color: '#FFFFFF',
    },
    frozen: {
      backgroundColor: '#C7EAE4',
      borderColor: '#B8D3D1',
      borderWidth: '1px',
      color: '#1A281F',
    },
  };

  return (
    <div
      className={`${radiusClass} border transition-colors ${className}`}
      style={{
        ...baseStyles[variant],
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
};
