import { useState, useRef, useEffect } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { sendMessage } from '../store/chatSlice';
import ChatMessage from './ChatMessage';

export default function ChatPanel() {
  const { messages, isLoading } = useSelector((s) => s.chat);
  const dispatch = useDispatch();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Focus input after response arrives
  useEffect(() => {
    if (!isLoading) {
      inputRef.current?.focus();
    }
  }, [isLoading]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isLoading) return;
    dispatch(sendMessage(text));
    setInput('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <div className="chat-header__title">
          AI Assistant
        </div>
        <div className="chat-header__subtitle">
          Log interaction via chat
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-message chat-message--assistant">
            Log interaction details here (e.g., &quot;Met Dr. Smith, discussed Product X efficacy, positive sentiment, shared brochure&quot;) or ask for help.
          </div>
        )}
        {messages.map((msg, i) => (
          <ChatMessage key={i} role={msg.role} content={msg.content} />
        ))}
        {isLoading && (
          <div className="chat-loading">
            <div className="chat-loading__dot" />
            <div className="chat-loading__dot" />
            <div className="chat-loading__dot" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="chat-input-bar">
        <input
          ref={inputRef}
          type="text"
          placeholder="Describe interaction..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
        />
        <button
          className="btn--log"
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
        >
          Log
        </button>
      </div>
    </div>
  );
}
