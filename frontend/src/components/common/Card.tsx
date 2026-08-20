import React from 'react';

interface CardProps {
  children: React.ReactNode;
  interactive?: boolean;
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({
  children,
  interactive = false,
  className = '',
  style,
  onClick,
}) => {
  return (
    <div
      className={`card ${interactive ? 'card-interactive' : ''} ${className}`}
      onClick={onClick}
      style={{ cursor: interactive ? 'pointer' : 'default', ...style }}
    >
      {children}
    </div>
  );
};
