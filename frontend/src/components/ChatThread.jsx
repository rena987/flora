import ReactMarkdown from 'react-markdown'

export default function ChatThread({ messages, loading }) {
  return (
    <div className="chat-thread">
      {messages.length === 0 && (
        <div style={{
          textAlign: "center", marginTop: "80px",
          color: "var(--text-secondary)"
        }}>
          <div style={{ fontSize: "3rem", marginBottom: "16px" }}>🌿</div>
          <p style={{ fontFamily: "var(--font-display)", fontSize: "1.1rem", marginBottom: "8px" }}>
            Welcome to Flora
          </p>
          <p style={{ fontSize: "0.85rem" }}>
            Upload a photo of your plant and describe what you're seeing
          </p>
        </div>
      )}

      {messages.map((msg, i) => (
        <div key={i} className={`message ${msg.role}`}>
          <div className="message-header">
            {msg.role === "flora" ? "🌿 Flora" : "You"}
          </div>
          {msg.image && (
            <img
              src={`data:image/jpeg;base64,${msg.image}`}
              className="message-image"
              alt="uploaded plant"
            />
          )}
          <div className="message-bubble">
            <ReactMarkdown>{msg.content}</ReactMarkdown>
          </div>
        </div>
      ))}

      {loading && (
        <div className="message flora">
          <div className="message-header">🌿 Flora</div>
          <div className="loading-dots">
            <span /><span /><span />
          </div>
        </div>
      )}
    </div>
  )
}