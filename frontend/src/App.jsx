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
    if (!input.trim()) return

    const userMsg = { role: "user", content: input, image }
    setMessages(prev => [...prev, userMsg])
    setInput("")
    setLoading(true)

    try {
      const response = await axios.post("http://localhost:8000/chat", {
        message: input,
        image_base64: image
      })

      const floraMsg = {
        role: "flora",
        content: response.data.response
      }
      setMessages(prev => [...prev, floraMsg])
      setToolTrace(response.data.tools_called)
      setSupervisor(response.data.supervisor)
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
              disabled={loading || !input.trim()}
            >
              →
            </button>
          </div>
        </div>

        <ToolTrace toolsCalled={toolTrace} supervisor={supervisor} />
      </div>
    </div>
  )
}