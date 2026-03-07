export default function ToolTrace({ toolsCalled, supervisor }) {
  const toolConfig = {
    vision_analyze:  { icon: "🔍", label: "vision_analyze",  className: "vision",   status: "analyzed" },
    rag_lookup:      { icon: "📚", label: "rag_lookup",      className: "rag",      status: "retrieved" },
    severity_assess: { icon: "⚠️",  label: "severity_assess", className: "severity", status: "assessed" },
    escalate:        { icon: "🚨", label: "escalate",        className: "escalate", status: "flagged" },
  }

  return (
    <div className="trace-panel">
      <div className="trace-header">Tool Trace</div>
      <div className="trace-body">
        {toolsCalled.length === 0 ? (
          <p className="trace-empty">Tools will appear here after each response</p>
        ) : (
          toolsCalled.map((tool, i) => {
            const config = toolConfig[tool] || { icon: "🔧", label: tool, className: "rag", status: "called" }
            return (
              <div key={i} className={`trace-item ${config.className}`}>
                <span className="trace-icon">{config.icon}</span>
                <span className="trace-name">{config.label}</span>
                <span className="trace-status">{config.status}</span>
              </div>
            )
          })
        )}
      </div>

      {supervisor && (
        <div className={`supervisor-badge ${supervisor.approved ? "approved" : "flagged"}`}>
          <span>{supervisor.approved ? "✅" : "🚨"}</span>
          <span>Supervisor — {supervisor.approved ? "APPROVED" : `FLAGGED: ${supervisor.flag_reason}`}</span>
        </div>
      )}
    </div>
  )
}