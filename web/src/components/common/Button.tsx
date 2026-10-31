import React from 'react';

export type ButtonVariant =
  | 'primary' // Evergreen with white text
  | 'outline' // Taupe Grey border and text
  | 'ghost' // Transparent with Taupe Grey/Evergreen text
  | 'jasmine' // Jasmine background with Evergreen text (e.g. mobile hero "Start review")
  | 'pale-sky' // Pale Sky background with Evergreen text (e.g. "Explain my mistake")
  | 'celadon'; // Celadon background with Evergreen text

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: 'sm' | 'md' | 'lg';
  fullWidth?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  fullWidth = false,
  icon,
  iconPosition = 'left',
  className = '',
  disabled = false,
  style,
  ...props
}) => {
  // 10-12px radius, touch targets >= 44px
  const sizeClasses = {
    sm: 'min-h-[40px] px-3.5 py-1.5 text-[13px] font-medium rounded-[10px]',
    md: 'min-h-[44px] px-5 py-2.5 text-[15px] font-semibold rounded-[12px]',
    lg: 'min-h-[48px] px-6 py-3 text-[16px] font-semibold rounded-[12px]',
  }[size];

  const variantStyles: Record<ButtonVariant, React.CSSProperties> = {
    primary: {
      backgroundColor: '#1A281F',
      color: '#FFFFFF',
      border: '1px solid #1A281F',
    },
    outline: {
      backgroundColor: '#FFFFFF',
      color: '#635255',
      border: '1px solid #635255',
    },
    ghost: {
      backgroundColor: 'transparent',
      color: '#1A281F',
      border: '1px solid transparent',
    },
    jasmine: {
      backgroundColor: '#FFD972',
      color: '#1A281F',
      border: '1px solid #FFD972',
    },
    'pale-sky': {
      backgroundColor: '#C0E8F9',
      color: '#1A281F',
      border: '1px solid #B8D3D1',
    },
    celadon: {
      backgroundColor: '#A7E8BD',
      color: '#1A281F',
      border: '1px solid #A7E8BD',
    },
  };

  const disabledStyle: React.CSSProperties = {
    backgroundColor: '#B8D3D1',
    color: '#635255',
    border: '1px solid #B8D3D1',
    cursor: 'not-allowed',
    opacity: 0.8,
  };

  return (
    <button
      className={`inline-flex items-center justify-center gap-2 transition-all select-none whitespace-nowrap shrink-0 cursor-pointer active:scale-[0.98] ${
        fullWidth ? 'w-full' : ''
      } ${sizeClasses} ${className}`}
      style={{
        ...(disabled ? disabledStyle : variantStyles[variant]),
        ...style,
      }}
      disabled={disabled}
      {...props}
    >
      {icon && iconPosition === 'left' && <span className="shrink-0">{icon}</span>}
      <span>{children}</span>
      {icon && iconPosition === 'right' && <span className="shrink-0">{icon}</span>}
    </button>
  );
};
