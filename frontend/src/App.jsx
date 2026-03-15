import { useState } from 'react'
import axios from 'axios'
import './index.css'
import ChatThread from './components/ChatThread'
import ToolTrace from './components/ToolTrace'
import ImageUploader from './components/ImageUploader'

export default function App() {
  const [messages, setMessages] = useState([])
  const [toolTrace, setToolTrace] = useState([])
  const [input, setInput] = useState("")
  const [image, setImage] = useState(null)
  const [loading, setLoading] = useState(false)
  const [supervisor, setSupervisor] = useState(null)

  const handleImageSelect = (e) => {
    const file = e.target.files[0]
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      const base64 = reader.result.split(",")[1]
      setImage(base64)
    }
    reader.readAsDataURL(file)
  }

  const sendMessage = async () => {
    if (!input.trim() && !image) return

    const userMsg = { role: "user", content: input, image }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setLoading(true)

    const floraMsg = {
      role: "flora",
      content: ""
    }
    setMessages(prev => [...prev, floraMsg])

    try {
      const response = await fetch("https://flora-production-90a7.up.railway.app/chat/stream", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: input, image_base64: image})
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error("Backend error: ", response.status, errorText)
        throw new Error(`Backend returned ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break 

        const chunk = decoder.decode(value)
        buffer += chunk 
        const lines = buffer.split("\n")
        buffer = lines.pop()

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue
          try {
            const data = JSON.parse(line.slice(6))
            if (data.type === "token") {
              setMessages(prev => {
                const updated = [...prev]
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: updated[updated.length - 1].content + data.content
                }
                return updated
              })
            }
            if (data.type === "done") {
              setToolTrace(data.trace.steps)
              setSupervisor(data.supervisor)
            }
          } catch (e) {
            // incomplete JSON fragment — skip silently
          }
        }
      }

    } catch (err) {
      console.error(err)
      setMessages(prev => [...prev, {
        role: "flora",
        content: "Something went wrong. Please try again."
      }])
    } finally {
      setLoading(false)
      setImage(null)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <span>🌿</span>
        <h1>Flora</h1>
      </header>

      <div className="app-body">
        <div className="chat-panel">
          <ChatThread messages={messages} loading={loading} />

          <div className="input-area">
            <ImageUploader
              onImageSelect={handleImageSelect}
              imagePreview={image}
              onClear={() => setImage(null)}
            />
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Describe your plant's symptoms..."
              rows={1}
            />
            <button
              className="send-btn"
              onClick={sendMessage}
              disabled={loading || (!input.trim() && !image)}
            >
              →
            </button>
          </div>
        </div>

        <ToolTrace steps={toolTrace} supervisor={supervisor} />
      </div>
    </div>
  )
}