import React, { useState, useEffect } from 'react';

interface TypeWriterProps {
  text: string;
  delay?: number;
  className?: string;
}

const TypeWriter: React.FC<TypeWriterProps> = ({ text, delay = 100, className = '' }) => {
  const [displayText, setDisplayText] = useState('');

  useEffect(() => {
    if (displayText.length < text.length) {
      const timeout = setTimeout(() => {
        setDisplayText(text.slice(0, displayText.length + 1));
      }, delay);

      return () => clearTimeout(timeout);
    }
  }, [displayText, text, delay]);

  return (
    <div className={className} style={{ whiteSpace: 'nowrap' }}>
      <span style={{ fontFamily: 'Tobias' }}>{displayText}</span>
      <span className="typing-cursor" />
    </div>
  );
};

export default TypeWriter;
