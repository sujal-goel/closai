'use client';

import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';

const ChatSidebar = ({ messages = [], chatHistory = [], onSendMessage, onLoadChat, isLoading }) => {
  const [input, setInput] = useState('');
  const [showHistory, setShowHistory] = useState(false);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
    }
  };

  return (
    <aside className="sidebar glass">
      <div className="sidebar-header">
        <div className="logo">
          <span className="logo-icon">☁️</span>
          <span className="logo-text">CloudCompare <small>v2</small></span>
        </div>
        <button className="history-toggle" onClick={() => setShowHistory(!showHistory)}>
          {showHistory ? 'Close History' : 'View History'}
        </button>
      </div>

      {showHistory ? (
        <div className="history-panel">
          <h3>Past Sessions</h3>
          {chatHistory.length === 0 ? (
            <p className="no-history">No history found.</p>
          ) : (
            chatHistory.map(chat => (
              <div key={chat.chat_id} className="history-item" onClick={() => { onLoadChat(chat.chat_id); setShowHistory(false); }}>
                <div className="history-intent">{chat.intent}</div>
                <div className="history-summary">{chat.summary || 'Architecture discussion'}</div>
                <div className="history-date">
                  {chat.updated_at ? new Date(chat.updated_at).toLocaleDateString() : ''}
                </div>
              </div>
            ))
          )}
        </div>
      ) : (
        <div className="chat-history">
        {messages.length === 0 ? (
          <div className="empty-state">
            <p>Describe your workload to begin generating a system architecture.</p>
            <div className="suggestions">
              <button onClick={() => setInput('Build a scalable AI/ML pipeline with GPU workers')}>AI/ML Pipeline</button>
              <button onClick={() => setInput('Serverless web app with global CDN and Auth')}>Serverless Web App</button>
            </div>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div key={i} className={`message ${msg.role}`}>
              <div className="message-content">
                {msg.role === 'model' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  msg.content
                )}
              </div>
              <div className="message-meta">{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
            </div>
          ))
        )}
        {isLoading && <div className="message model loading">Analyzing constraints...</div>}
      </div>
      )}

      <div className="input-area">
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            placeholder="Describe your architecture constraints..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            {isLoading ? '...' : '→'}
          </button>
        </form>
      </div>

      <style jsx>{`
        .sidebar {
          display: flex;
          flex-direction: column;
          border-radius: 0;
          border-left: none;
          background: rgba(10, 15, 18, 0.95);
        }

        .sidebar-header {
          padding: 24px;
          border-bottom: 1px solid var(--border-muted);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .history-toggle {
          background: rgba(0, 245, 255, 0.1);
          border: 1px solid rgba(0, 245, 255, 0.2);
          color: var(--accent-primary);
          padding: 6px 12px;
          border-radius: var(--radius-pill);
          font-size: 10px;
          text-transform: uppercase;
          font-weight: 800;
          cursor: pointer;
        }

        .history-panel {
          flex: 1;
          overflow-y: auto;
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .history-panel h3 {
          font-size: 12px;
          text-transform: uppercase;
          color: var(--text-muted);
          margin-bottom: 8px;
        }

        .history-item {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid var(--border-muted);
          padding: 12px;
          border-radius: var(--radius-soft);
          cursor: pointer;
          transition: all 0.2s;
        }

        .history-item:hover {
          border-color: var(--accent-primary);
          background: rgba(0, 245, 255, 0.05);
        }

        .history-intent {
          font-size: 10px;
          font-weight: 800;
          color: var(--accent-primary);
          text-transform: uppercase;
          margin-bottom: 4px;
        }

        .history-summary {
          font-size: 13px;
          color: var(--text-primary);
          margin-bottom: 8px;
        }

        .history-date {
          font-size: 10px;
          color: var(--text-muted);
        }

        .logo {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .logo-icon { font-size: 24px; }
        .logo-text { font-weight: 800; font-size: 18px; color: var(--text-primary); }
        .logo-text small { font-size: 10px; color: var(--accent-primary); margin-left: 4px; border: 1px solid var(--accent-primary); padding: 1px 4px; border-radius: 4px; }

        .chat-history {
          flex: 1;
          overflow-y: auto;
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .empty-state {
          display: flex;
          flex-direction: column;
          gap: 16px;
          color: var(--text-secondary);
          text-align: center;
          margin-top: 40px;
        }

        .suggestions {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          justify-content: center;
        }

        .suggestions button {
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid var(--border-muted);
          color: var(--text-secondary);
          padding: 8px 12px;
          border-radius: 8px;
          font-size: 11px;
          cursor: pointer;
          transition: all 0.2s;
        }

        .suggestions button:hover {
          background: var(--accent-primary);
          color: #000;
        }

        .message {
          max-width: 90%;
          padding: 12px 18px;
          font-size: 14px;
          line-height: 1.6;
        }

        .user {
          align-self: flex-end;
          background: var(--accent-primary);
          color: #000;
          border-radius: var(--radius-soft);
          border-bottom-right-radius: 4px;
          font-weight: 500;
          box-shadow: var(--shadow-electric);
        }

        .model {
          align-self: flex-start;
          background: var(--bg-card);
          color: var(--text-primary);
          border-radius: var(--radius-soft);
          border-bottom-left-radius: 4px;
          border: 1px solid var(--glass-border);
          box-shadow: var(--shadow-whisper);
        }

        .loading {
          font-style: italic;
          color: var(--accent-primary);
          background: transparent;
          border: none;
        }

        .message-meta {
          font-size: 9px;
          margin-top: 4px;
          opacity: 0.6;
        }

        .input-area {
          padding: 24px;
          background: rgba(10, 15, 18, 0.8);
          backdrop-filter: blur(8px);
          position: sticky;
          bottom: 0;
          z-index: 10;
        }

        form {
          display: flex;
          gap: 12px;
          background: var(--bg-secondary);
          padding: 6px 6px 6px 16px;
          border-radius: var(--radius-pill);
          border: 1px solid var(--border-muted);
          box-shadow: var(--shadow-whisper);
          transition: border-color var(--ease-soft) 0.3s, box-shadow var(--ease-soft) 0.3s;
        }

        form:focus-within {
          border-color: var(--accent-primary);
          box-shadow: var(--shadow-electric);
        }

        input {
          flex: 1;
          background: transparent;
          border: none;
          color: var(--text-primary);
          padding: 8px 12px;
          font-family: inherit;
          outline: none;
        }

        button[type="submit"] {
          background: var(--accent-primary);
          border: none;
          color: #000;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          font-weight: 800;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform var(--ease-soft) 0.2s, box-shadow var(--ease-soft) 0.2s;
        }

        button[type="submit"]:not(:disabled):hover {
          transform: scale(1.05);
          box-shadow: var(--shadow-electric);
        }

        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      `}</style>
    </aside>
  );
};

export default ChatSidebar;
