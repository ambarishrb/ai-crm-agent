export default function ChatMessage({ role, content }) {
  return (
    <div className={`chat-message chat-message--${role}`}>
      {content}
    </div>
  );
}
