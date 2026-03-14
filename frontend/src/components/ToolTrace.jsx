export default function ToolTrace({ steps, supervisor }) {
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
        {steps.length === 0 ? (
          <p className="trace-empty">Tools will appear here after each response</p>
        ) : (
          steps.map((step, i) => {
            const config = toolConfig[step.tool] || { icon: "🔧", label: step.tool, className: "rag", status: "called" }
            return (
              <div key={i} className={`trace-item ${config.className}`}>
                <span className="trace-icon">{config.icon}</span>
                <span className="trace-name">{config.label}</span>
                <span className="trace-status">{config.status}</span>
                <span className="trace-latency">{step.latency_ms}ms</span>
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