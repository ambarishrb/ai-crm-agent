import { useState, useCallback, useRef, useEffect } from 'react';
import InteractionForm from './InteractionForm';
import ChatPanel from './ChatPanel';

export default function LogInteraction() {
  const [chatWidth, setChatWidth] = useState(40); // percentage
  const isDragging = useRef(false);
  const containerRef = useRef(null);

  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    isDragging.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  }, []);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isDragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const pct = ((rect.width - x) / rect.width) * 100;
      // Clamp between 25% and 60%
      setChatWidth(Math.min(60, Math.max(25, pct)));
    };

    const handleMouseUp = () => {
      if (isDragging.current) {
        isDragging.current = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
      }
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, []);

  const formWidth = 100 - chatWidth;

  return (
    <div className="log-interaction" ref={containerRef}>
      <div className="log-interaction__form" style={{ flex: `0 0 ${formWidth}%` }}>
        <InteractionForm />
      </div>
      <div
        className="log-interaction__divider"
        onMouseDown={handleMouseDown}
      />
      <div className="log-interaction__chat" style={{ flex: `0 0 ${chatWidth}%` }}>
        <ChatPanel />
      </div>
    </div>
  );
}
