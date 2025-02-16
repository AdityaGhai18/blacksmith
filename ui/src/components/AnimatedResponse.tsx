'use client'

import { useState, useEffect, useRef } from 'react'

interface AnimatedResponseProps {
  text: string;
  header: string;
  isVisible: boolean;
  onComplete: () => void;
}

export default function AnimatedResponse({ text, header, isVisible, onComplete }: AnimatedResponseProps) {
  const [displayedText, setDisplayedText] = useState("");
  const [isExpanded, setIsExpanded] = useState(true);
  const hasAnimatedRef = useRef(false);

  useEffect(() => {
    if (!isVisible) {
      setDisplayedText("");
      setIsExpanded(true);
      hasAnimatedRef.current = false;
      return;
    }

    if (hasAnimatedRef.current) return;

    let isMounted = true;
    hasAnimatedRef.current = true;

    const animate = async () => {
      // Reset states
      setDisplayedText("");
      setIsExpanded(true);

      // Animate text
      for (let i = 0; i < text.length; i += 2) {
        if (!isMounted) return;
        await new Promise(resolve => setTimeout(resolve, 30));
        setDisplayedText(text.slice(0, i + 2));
      }

      if (!isMounted) return;

      // Wait after text is complete
      await new Promise(resolve => setTimeout(resolve, 1000));
      if (!isMounted) return;

      // Collapse
      setIsExpanded(false);

      // Wait for collapse animation
      await new Promise(resolve => setTimeout(resolve, 500));
      if (!isMounted) return;

      // Signal completion
      onComplete();
    };

    animate();

    return () => {
      isMounted = false;
    };
  }, [isVisible, text, onComplete]);

  // Get first line for collapsed view
  console.log("Text:", text)
  // const firstLine = text.split('\n')[0];
  const firstLine = text;
  const previewText = firstLine.length > 100 ? firstLine.substring(0, 100) + '...' : firstLine;

  return (
    <div className={`
      w-full max-w-[600px]
      transition-all duration-500 ease-out
      border border-white/20 rounded-md
      ${isExpanded ? 'py-4 px-6' : 'py-3 px-4'}
      ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 -translate-y-4'}
      overflow-hidden
    `}>
      <div className={`
        text-white/90
        transition-all duration-500
        ${isExpanded ? 'space-y-2' : 'space-y-1'}
      `}>
        {/* Header */}
        <div className="text-white/60 text-sm font-medium">
          {header}
        </div>
        {/* Content */}
        <div className={`
          text-lg
          ${isExpanded ? 'whitespace-pre-wrap break-words' : 'whitespace-nowrap overflow-hidden text-ellipsis'}
        `}>
          {isExpanded ? displayedText : previewText}
        </div>
      </div>
    </div>
  );
}
