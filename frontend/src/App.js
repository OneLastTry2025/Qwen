import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || window.location.origin;

function App() {
  const [messages, setMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [availableModels, setAvailableModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('qwen3-235b-a22b');
  const [useWebSearch, setUseWebSearch] = useState(false);
  const [performanceStats, setPerformanceStats] = useState(null);
  const [directApiStatus, setDirectApiStatus] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load initial data
  useEffect(() => {
    loadPerformanceStats();
    loadConversations();
    loadModels();
  }, []);

  const loadPerformanceStats = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/performance`);
      const data = await response.json();
      if (data.success) {
        setPerformanceStats(data.data);
        setDirectApiStatus(data.direct_api_available);
      }
    } catch (error) {
      console.warn('Performance stats not available:', error);
    }
  };

  const loadConversations = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/conversations`);
      const data = await response.json();
      if (data.success && data.data) {
        setConversations(data.data.slice(0, 10)); // Show recent 10
      }
    } catch (error) {
      console.warn('Conversations not available:', error);
    }
  };

  const loadModels = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/models`);
      const data = await response.json();
      if (data.success && data.data) {
        setAvailableModels(data.data);
      }
    } catch (error) {
      console.warn('Models not available:', error);
    }
  };

  const sendMessage = async () => {
    if (!currentMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: currentMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    const messageToSend = currentMessage;
    setCurrentMessage('');

    try {
      const startTime = Date.now();
      
      const response = await fetch(`${BACKEND_URL}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: messageToSend,
          chat_id: currentChatId,
          model_name: selectedModel,
          use_web_search: useWebSearch
        })
      });

      const data = await response.json();
      const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);

      if (data.success || data.status === 'success') {
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.response || data.data?.response || 'Response received',
          timestamp: new Date(),
          responseTime: responseTime,
          apiMethod: directApiStatus ? 'Direct API' : 'Browser Automation'
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // Update chat ID for conversation continuity
        if (data.chat_id) {
          setCurrentChatId(data.chat_id);
        }

        // Refresh performance stats
        loadPerformanceStats();
      } else {
        throw new Error(data.message || data.error || 'Failed to send message');
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `Error: ${error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const generateImage = async () => {
    if (!currentMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: `🎨 Generate image: ${currentMessage}`,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    const prompt = currentMessage;
    setCurrentMessage('');

    try {
      const startTime = Date.now();
      
      const response = await fetch(`${BACKEND_URL}/api/image`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: prompt,
          chat_id: currentChatId
        })
      });

      const data = await response.json();
      const responseTime = ((Date.now() - startTime) / 1000).toFixed(2);

      if (data.success || data.status === 'success') {
        const imageMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: `Image generated for "${prompt}"`,
          imageUrl: data.image_url,
          timestamp: new Date(),
          responseTime: responseTime,
          apiMethod: directApiStatus ? 'Direct API' : 'Browser Automation'
        };

        setMessages(prev => [...prev, imageMessage]);
        
        if (data.chat_id) {
          setCurrentChatId(data.chat_id);
        }

        loadPerformanceStats();
      } else {
        throw new Error(data.message || data.error || 'Failed to generate image');
      }
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'error',
        content: `Image generation error: ${error.message}`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const startNewChat = () => {
    setCurrentChatId(null);
    setMessages([]);
    loadConversations();
  };

  const formatTime = (date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>⚡ Qwen Direct API</h1>
          <div className="performance-indicator">
            {directApiStatus ? (
              <span className="status-badge status-fast">
                🚀 Direct API (0.8s avg)
              </span>
            ) : (
              <span className="status-badge status-fallback">
                🔄 Browser Fallback (2-50s)
              </span>
            )}
          </div>
        </div>
      </header>

      <div className="app-body">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <button className="new-chat-btn" onClick={startNewChat}>
              ➕ New Chat
            </button>
          </div>

          {/* Performance Stats */}
          {performanceStats && (
            <div className="sidebar-section">
              <h3>📊 Performance</h3>
              <div className="performance-stats">
                <div className="stat-item">
                  <span>Direct API Calls</span>
                  <span>{performanceStats.direct_api_calls || 0}</span>
                </div>
                <div className="stat-item">
                  <span>Browser Fallback</span>
                  <span>{performanceStats.browser_fallback_calls || 0}</span>
                </div>
                {performanceStats.speed_improvement && (
                  <div className="stat-item highlight">
                    <span>Speed Improvement</span>
                    <span>{performanceStats.speed_improvement.toFixed(1)}x</span>
                  </div>
                )}
                <div className="stat-item">
                  <span>Avg Direct Time</span>
                  <span>{(performanceStats.avg_direct_time || 0).toFixed(2)}s</span>
                </div>
                <div className="stat-item">
                  <span>Avg Browser Time</span>
                  <span>{(performanceStats.avg_browser_time || 0).toFixed(2)}s</span>
                </div>
              </div>
            </div>
          )}

          {/* Recent Conversations */}
          {conversations.length > 0 && (
            <div className="sidebar-section">
              <h3>💬 Recent Chats</h3>
              <div className="conversations-list">
                {conversations.map((conv, index) => (
                  <div 
                    key={conv.id || index} 
                    className="conversation-item"
                    onClick={() => setCurrentChatId(conv.id)}
                  >
                    <div className="conversation-title">
                      {conv.title || conv.name || `Chat ${index + 1}`}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Models */}
          {availableModels.length > 0 && (
            <div className="sidebar-section">
              <h3>🧠 Models</h3>
              <select 
                value={selectedModel} 
                onChange={(e) => setSelectedModel(e.target.value)}
                className="model-selector"
              >
                {availableModels.map((model, index) => (
                  <option key={model.id || index} value={model.name || model}>
                    {model.name || model}
                  </option>
                ))}
              </select>
            </div>
          )}
        </aside>

        {/* Main Chat Area */}
        <main className="chat-area">
          {/* Messages */}
          <div className="messages-container">
            {messages.length === 0 ? (
              <div className="welcome-message">
                <h2>Welcome to Qwen Direct API! 🚀</h2>
                <p>Experience 60x faster responses compared to browser automation</p>
                <div className="feature-grid">
                  <div className="feature-card">
                    <span className="feature-icon">⚡</span>
                    <span>Lightning Fast</span>
                  </div>
                  <div className="feature-card">
                    <span className="feature-icon">🎨</span>
                    <span>Image Generation</span>
                  </div>
                  <div className="feature-card">
                    <span className="feature-icon">🌐</span>
                    <span>Web Search</span>
                  </div>
                  <div className="feature-card">
                    <span className="feature-icon">💬</span>
                    <span>Smart Chat</span>
                  </div>
                </div>
              </div>
            ) : (
              messages.map((message) => (
                <div key={message.id} className={`message message-${message.type}`}>
                  <div className="message-content">
                    {message.imageUrl ? (
                      <div>
                        <p>{message.content}</p>
                        <img 
                          src={message.imageUrl} 
                          alt="Generated image" 
                          className="generated-image"
                          onError={(e) => {
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'block';
                          }}
                        />
                        <div style={{display: 'none'}} className="image-error">
                          Image could not be loaded
                        </div>
                      </div>
                    ) : (
                      <pre className="message-text">{message.content}</pre>
                    )}
                  </div>
                  <div className="message-meta">
                    <span className="message-time">{formatTime(message.timestamp)}</span>
                    {message.responseTime && (
                      <span className="response-time">
                        ⚡ {message.responseTime}s via {message.apiMethod}
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
            
            {isLoading && (
              <div className="message message-assistant">
                <div className="message-content">
                  <div className="typing-indicator">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                  <p>
                    {directApiStatus 
                      ? "🚀 Processing with Direct API (lightning fast)..." 
                      : "🔄 Processing with Browser Automation (please wait)..."
                    }
                  </p>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="input-area">
            <div className="input-controls">
              <label className="control-item">
                <input
                  type="checkbox"
                  checked={useWebSearch}
                  onChange={(e) => setUseWebSearch(e.target.checked)}
                />
                🌐 Web Search
              </label>
            </div>

            <div className="input-container">
              <textarea
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask Qwen anything..."
                className="message-input"
                rows="3"
                disabled={isLoading}
              />
              <div className="input-buttons">
                <button
                  onClick={sendMessage}
                  disabled={!currentMessage.trim() || isLoading}
                  className="send-btn primary"
                >
                  💬 Send
                </button>
                <button
                  onClick={generateImage}
                  disabled={!currentMessage.trim() || isLoading}
                  className="send-btn secondary"
                >
                  🎨 Generate Image
                </button>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;