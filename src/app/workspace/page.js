'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ChatSidebar from '@/components/ChatSidebar';
import Canvas from '@/components/Canvas';
import DecisionMatrix from '@/components/DecisionMatrix';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [providers, setProviders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatId, setChatId] = useState(null);
  const [phase, setPhase] = useState('idle'); // idle | clarifying | scored
  const [selectedNode, setSelectedNode] = useState(null);
  const [intelPulse, setIntelPulse] = useState(null);
  const [activeMapping, setActiveMapping] = useState(null);
  const [mappedProvider, setMappedProvider] = useState(null);
  const router = useRouter();

  // Route protection and blank slate initialize
  useEffect(() => {
    const token = localStorage.getItem('cc_token');
    if (!token) {
      router.push('/login');
      return;
    }
    // Fetch chat history
    fetch(`${API_BASE}/api/chats`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(r => r.ok ? r.json() : { chats: [] })
    .then(data => setChatHistory(data.chats || []))
    .catch(console.error);

    setNodes([]);
    setEdges([]);
    setProviders([]);
  }, [router]);

  const loadChat = async (id) => {
    setIsLoading(true);
    try {
      const token = localStorage.getItem('cc_token');
      const chatRes = await fetch(`${API_BASE}/api/chat/${id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!chatRes.ok) throw new Error('Failed to load chat');
      const chatData = await chatRes.json();
      
      setChatId(chatData.chat_id);
      setMessages(chatData.messages || []);
      setPhase('scored'); // Assumed, since it's an old chat

      // Try fully restoring the blueprint if it existed
      if (chatData.metadata?.last_blueprint_id) {
        const bpRes = await fetch(`${API_BASE}/api/blueprint/${chatData.metadata.last_blueprint_id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (bpRes.ok) {
          const bpData = await bpRes.json();
          setNodes(bpData.nodes || []);
          setEdges(bpData.edges || []);
          if (bpData.scores) {
             setProviders(Object.values(bpData.scores));
          }
        }
      } else {
         setNodes([]); setEdges([]); setProviders([]);
      }
    } catch(err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async (query) => {
    const newUserMsg = { role: 'user', content: query, timestamp: new Date() };
    setMessages(prev => [...prev, newUserMsg]);
    setIsLoading(true);
    
    // Reset mapping back to generic when a new requirement is sent
    setActiveMapping(null);
    setMappedProvider(null);

    try {
      const token = localStorage.getItem('cc_token');
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          message: query,
          chat_id: chatId,
          history: messages.map(m => ({ role: m.role, content: m.content })),
        }),
      });

      if (!response.ok) {
        if (response.status === 401) router.push('/login');
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      setChatId(data.chat_id);
      setPhase(data.phase);

      // Add model response
      setMessages(prev => [...prev, {
        role: 'model',
        content: data.explanation || data.follow_up_question || 'Architecture updated.',
        timestamp: new Date()
      }]);

      // Update blueprint + scores when ready
      if (data.blueprint) {
        setNodes(data.blueprint.nodes || []);
        setEdges(data.blueprint.edges || []);
      }
      if (data.scoring) {
        setProviders(data.scoring);
      }
      
      // Fetch latest global sync status
      const healthRes = await fetch(`${API_BASE}/health`);
      if (healthRes.ok) {
        const healthData = await healthRes.json();
        setIntelPulse(healthData);
      }

    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'model',
        content: `⚠️ ${error.message}. Make sure the Python backend is running on ${API_BASE}.`,
        timestamp: new Date()
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleMapNative = async (providerId) => {
    if (!chatId) return;
    setIsLoading(true);
    setMappedProvider(providerId);
    try {
      const token = localStorage.getItem('cc_token');
      // Find the latest blueprint from the backend state
      const response = await fetch(`${API_BASE}/api/blueprint/map-native`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          blueprint_id: chatId, // simplified — in production, track blueprint_id separately
          provider: providerId,
          region: 'us-east-1',
        }),
      });

      if (!response.ok) {
        if (response.status === 401) router.push('/login');
        throw new Error(`HTTP ${response.status}`);
      }
      const data = await response.json();
      setActiveMapping(data.mapping);

      setMessages(prev => [...prev, {
        role: 'model',
        content: `✅ Native mapping complete for ${providerId.toUpperCase()}. Estimated cost: ₹${data.mapping?.total_estimated_monthly_cost_inr?.toFixed(2) || 'N/A'}/mo`,
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error('Native mapping error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('cc_token');
    router.push('/login');
  };

  const handleResetGeneric = () => {
    setActiveMapping(null);
    setMappedProvider(null);
  };

  return (
    <main className="app-container">
      <div className="workspace-nav">
        <div className="nav-logo">☁️ CloudCompare <span>Workspace</span></div>
        <div className="nav-actions">
          {mappedProvider && (
            <button onClick={handleResetGeneric} className="reset-btn">
              Reset to Generic
            </button>
          )}
          <button onClick={handleLogout} className="logout-btn">Log Out</button>
        </div>
      </div>

      <ChatSidebar
        messages={messages}
        chatHistory={chatHistory}
        onSendMessage={handleSendMessage}
        onLoadChat={loadChat}
        isLoading={isLoading}
      />

      <div className="main-content">
        <Canvas 
          nodes={nodes} 
          edges={edges} 
          onNodeClick={(node) => setSelectedNode(node)}
          selectedNodeId={selectedNode?.id}
          activeMapping={activeMapping}
          provider={mappedProvider}
        />
        <DecisionMatrix providers={providers} />
        
        {/* Node Detail Drawer */}
        {selectedNode && (
          <div className="node-drawer glass">
            <div className="drawer-header">
              <h4>{selectedNode.label}</h4>
              <button 
                className="close-btn"
                onClick={() => setSelectedNode(null)}
              >
                ✕
              </button>
            </div>
            <div className="drawer-body">
              <div className="prop">
                <label>Component Type</label>
                <span>{selectedNode.type.split('_').join(' ')}</span>
              </div>
              <div className="prop">
                <label>Infrastructure Layer</label>
                <span>{selectedNode.category}</span>
              </div>
              <div className="prop policy">
                <label>Policy & SLA Analysis</label>
                <div className="policy-pill">
                  <span className="dot pulse"></span>
                  Active Documentation Shield
                </div>
                <p>Governed by autonomous <strong>{selectedNode.category}</strong> reliability policies synced within last 24h.</p>
              </div>
              <p className="node-tip">
                Optimized for <strong>{selectedNode.type === 'gpu_worker' ? 'Parallel Compute' : 'Cloud Resilience'}</strong>. 
                Adheres to Principal engineering standards.
              </p>
            </div>
          </div>
        )}

        {/* Intelligence Status Badge */}
        {intelPulse && (
          <div className="intel-status glass">
            <span className="status-label">Global Source of Truth</span>
            <div className="statuses">
              <span className={`pill ${intelPulse.database === 'connected' ? 'active' : ''}`}>DB</span>
              <span className={`pill ${intelPulse.tavily === 'configured' ? 'active' : ''}`}>Market Intel</span>
              <span className={`pill ${intelPulse.gemini === 'configured' ? 'active' : ''}`}>AI Expert</span>
            </div>
          </div>
        )}

        {/* Phase badge */}
        <div className="phase-badge glass">
          <span className="phase-dot"></span>
          <span className="phase-text">
            {phase === 'idle' && 'Exploring — Describe workload'}
            {phase === 'clarifying' && 'Analyzing Constraints'}
            {phase === 'scored' && 'System Design Validated'}
          </span>
        </div>

        {/* Canvas Toolbar */}
        <div className="canvas-tools glass">
          <div className="tool-group">
            <button title="Zoom In">+</button>
            <button title="Zoom Out">−</button>
            <button title="Reset">⟲</button>
          </div>
          <div className="separator"></div>
          <div className="export-group">
            <button className="export-btn aws" onClick={() => handleMapNative('aws')}>AWS</button>
            <button className="export-btn gcp" onClick={() => handleMapNative('gcp')}>GCP</button>
            <button className="export-btn azure" onClick={() => handleMapNative('azure')}>Azure</button>
          </div>
        </div>
      </div>

      <style jsx>{`
        .workspace-nav {
          position: absolute;
          top: 0; left: 300px; /* offset sidebar width */
          right: 0;
          height: 60px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0 24px;
          background: rgba(10, 15, 18, 0.8);
          backdrop-filter: blur(8px);
          border-bottom: 1px solid var(--border-muted);
          z-index: 100;
        }

        .nav-logo { font-size: 14px; font-weight: 800; }
        .nav-logo span { color: var(--text-muted); font-weight: 600; margin-left: 8px; }

        .logout-btn {
          background: transparent;
          border: 1px solid var(--border-muted);
          color: var(--text-secondary);
          padding: 6px 12px;
          border-radius: var(--radius-pill);
          font-size: 11px;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s;
        }
        .logout-btn:hover { background: rgba(255, 68, 68, 0.1); color: #ff4444; border-color: rgba(255, 68, 68, 0.3); }
        
        .nav-actions { display: flex; gap: 12px; align-items: center; }
        
        .reset-btn {
          background: rgba(0, 245, 255, 0.1);
          border: 1px solid rgba(0, 245, 255, 0.3);
          color: var(--accent-primary);
          padding: 6px 12px;
          border-radius: var(--radius-pill);
          font-size: 11px;
          font-weight: 700;
          cursor: pointer;
          transition: all 0.2s;
        }
        .reset-btn:hover { background: rgba(0, 245, 255, 0.2); transform: translateY(-1px); }

        .app-container { padding-top: 60px; } /* Push down canvas */

        .node-drawer {
          position: absolute;
          bottom: 110px;
          right: 24px;
          width: 300px;
          padding: 24px;
          z-index: 10;
          animation: drawerSlide 0.4s var(--ease-soft);
          border-radius: var(--radius-soft);
        }

        .drawer-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .drawer-header h4 { 
          font-size: 13px; 
          font-weight: 800;
          text-transform: uppercase; 
          letter-spacing: 0.12em; 
          color: var(--accent-primary); 
        }

        .close-btn { 
          background: rgba(255, 255, 255, 0.05); 
          border: 1px solid var(--glass-border); 
          color: var(--text-muted); 
          width: 28px;
          height: 28px;
          border-radius: 50%;
          cursor: pointer; 
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          transition: all 0.2s;
        }
        
        .close-btn:hover { background: rgba(255,255,255,0.1); color: var(--text-primary); }

        .drawer-body { display: flex; flex-direction: column; gap: 16px; }
        .prop { display: flex; flex-direction: column; gap: 6px; }
        .prop label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; }
        .prop span { font-size: 14px; font-weight: 600; color: var(--text-primary); text-transform: capitalize; }
        
        .prop.policy { margin-top: 8px; }
        .policy-pill {
          display: flex;
          align-items: center;
          gap: 6px;
          background: rgba(0, 245, 255, 0.05);
          border: 1px solid rgba(0, 245, 255, 0.2);
          padding: 4px 8px;
          border-radius: var(--radius-pill);
          font-size: 10px;
          color: var(--accent-primary);
          width: fit-content;
          margin: 4px 0 8px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        
        .policy p {
          font-size: 11px;
          color: var(--text-muted);
          line-height: 1.5;
        }

        .dot.pulse {
          width: 5px;
          height: 5px;
          background: var(--accent-primary);
          border-radius: 50%;
          box-shadow: 0 0 6px var(--accent-primary);
          animation: miniPulse 1.5s infinite;
        }

        @keyframes miniPulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }

        .node-tip { 
          font-size: 11px; 
          color: var(--text-secondary); 
          margin-top: 12px; 
          line-height: 1.6; 
          padding: 12px; 
          background: rgba(255,255,255,0.02);
          border-radius: var(--radius-precise);
          border: 1px dashed var(--border-muted);
        }

        @keyframes drawerSlide {
          from { opacity: 0; transform: translateX(30px); }
          to { opacity: 1; transform: translateX(0); }
        }

        .phase-badge {
          position: absolute;
          top: 24px;
          left: 24px;
          padding: 8px 16px;
          z-index: 5;
          display: flex;
          align-items: center;
          gap: 10px;
          border-radius: var(--radius-pill);
        }

        .phase-text {
          font-size: 10px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-primary);
        }

        .phase-dot {
          width: 6px;
          height: 6px;
          border-radius: 50%;
          background: var(--accent-primary);
          box-shadow: 0 0 8px var(--accent-primary);
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.8); }
        }

        .intel-status {
          position: absolute;
          top: 24px;
          left: 50%;
          transform: translateX(-50%);
          padding: 10px 20px;
          display: flex;
          align-items: center;
          gap: 16px;
          border-radius: var(--radius-pill);
          z-index: 5;
        }

        .status-label {
          font-size: 10px;
          font-weight: 900;
          text-transform: uppercase;
          color: var(--text-muted);
          letter-spacing: 0.12em;
        }

        .statuses {
          display: flex;
          gap: 6px;
        }

        .pill {
          font-size: 9px;
          font-weight: 800;
          padding: 2px 8px;
          border-radius: 4px;
          color: var(--text-muted);
          background: rgba(255, 255, 255, 0.05);
          transition: all 0.3s;
        }

        .pill.active {
          color: var(--accent-primary);
          background: rgba(0, 245, 255, 0.1);
          border: 1px solid rgba(0, 245, 255, 0.2);
        }

        .canvas-tools {
          position: absolute;
          bottom: 24px;
          left: 50%;
          transform: translateX(-50%);
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 8px 12px;
          z-index: 5;
          border-radius: var(--radius-pill);
        }
        
        .tool-group, .export-group {
          display: flex;
          gap: 4px;
        }

        .canvas-tools button {
          background: transparent;
          border: none;
          color: var(--text-secondary);
          font-size: 16px;
          cursor: pointer;
          min-width: 32px;
          height: 32px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: var(--radius-pill);
          transition: all 0.2s;
        }

        .canvas-tools button:hover:not(.export-btn) {
          background: rgba(255, 255, 255, 0.08);
          color: var(--text-primary);
        }

        .separator {
          width: 1px;
          height: 20px;
          background: var(--border-muted);
        }

        .export-btn {
          font-size: 9px !important;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          padding: 0 16px !important;
          border: 1px solid var(--border-muted) !important;
          background: var(--bg-secondary) !important;
          color: var(--text-secondary) !important;
        }
        
        .export-btn:hover {
          border-color: var(--accent-primary) !important;
          color: var(--accent-primary) !important;
          box-shadow: var(--shadow-electric);
        }

        .export-btn.aws:hover { border-color: #ff9900 !important; color: #ff9900 !important; }
        .export-btn.gcp:hover { border-color: #4285f4 !important; color: #4285f4 !important; }
        .export-btn.azure:hover { border-color: #0078d4 !important; color: #0078d4 !important; }
      `}</style>
    </main>
  );
}
