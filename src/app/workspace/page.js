'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import ChatSidebar from '@/components/ChatSidebar';
import Canvas from '@/components/Canvas';
import DecisionMatrix from '@/components/DecisionMatrix';
import ArchitecturalReport from '@/components/ArchitecturalReport';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);
  const [providers, setProviders] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [chatId, setChatId] = useState(null);
  const [phase, setPhase] = useState('scored'); 
  const [selectedNode, setSelectedNode] = useState(null);
  const [intelPulse, setIntelPulse] = useState(null);
  const [activeMapping, setActiveMapping] = useState(null);
  const [mappedProvider, setMappedProvider] = useState(null);
  const [deploymentPlan, setDeploymentPlan] = useState(null);
  const [showReport, setShowReport] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('cc_token');
    if (!token) {
      router.push('/login');
      return;
    }
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
      setPhase('scored'); 

      if (chatData.metadata?.deployment_plan) {
        setDeploymentPlan(chatData.metadata.deployment_plan);
        setShowReport(true);
      }

      if (chatData.metadata?.last_blueprint_id) {
        const bpRes = await fetch(`${API_BASE}/api/blueprint/${chatData.metadata.last_blueprint_id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        if (bpRes.ok) {
          const bpData = await bpRes.json();
          setNodes(bpData.nodes || []);
          setEdges(bpData.edges || []);
          if (bpData.scores) setProviders(Object.values(bpData.scores));
          if (bpData.deployment_plan) {
            setDeploymentPlan(bpData.deployment_plan);
            setShowReport(true);
          }
        }
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

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setChatId(data.chat_id);
      setPhase(data.phase);
      setMessages(prev => [...prev, {
        role: 'model',
        content: data.explanation || data.follow_up_question || 'Architecture updated.',
        timestamp: new Date()
      }]);

      if (data.blueprint) {
        setNodes(data.blueprint.nodes || []);
        setEdges(data.blueprint.edges || []);
      }
      if (data.scoring) setProviders(data.scoring);
      if (data.deployment_plan) {
        setDeploymentPlan(data.deployment_plan);
        setShowReport(true);
      }
      
      const healthRes = await fetch(`${API_BASE}/health`);
      if (healthRes.ok) setIntelPulse(await healthRes.json());
    } catch (error) {
      console.error('Chat error:', error);
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
      const response = await fetch(`${API_BASE}/api/blueprint/map-native`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          blueprint_id: chatId,
          provider: providerId,
          region: 'us-east-1',
        }),
      });

      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setActiveMapping(data.mapping);

      const mappingMessage = data.mapping?.within_budget === false
        ? `❌ Native mapping for ${providerId.toUpperCase()} is not feasible within your budget.`
        : `✅ Native mapping complete for ${providerId.toUpperCase()}. Estimated cost: ₹${data.mapping?.total_estimated_monthly_cost_inr?.toFixed(2) || 'N/A'}/mo`;

      setMessages(prev => [...prev, {
        role: 'model',
        content: mappingMessage,
        timestamp: new Date()
      }]);
    } catch (error) {
      console.error('Mapping error:', error);
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

  const getMappingForNode = (nodeId) => {
    if (!activeMapping || !activeMapping.mappings) return null;
    return activeMapping.mappings.find(m => m.generic_id === nodeId);
  };

  return (
    <main className="app-container">
      <div className="workspace-nav">
        <div className="nav-logo">☁️ CLOS AI <span>Workspace</span></div>
        <div className="nav-actions">
          {mappedProvider && (
            <button onClick={handleResetGeneric} className="reset-btn">
              Reset to Generic
            </button>
          )}
          {deploymentPlan && !showReport && (
            <button onClick={() => setShowReport(true)} className="reset-btn" style={{ borderColor: 'var(--accent-primary)', color: 'var(--accent-primary)' }}>
              Show Guardrails
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
        
        {phase === 'scored' && deploymentPlan && (
          <ArchitecturalReport plan={deploymentPlan} onClose={() => setDeploymentPlan(null)} />
        )}
        
        {selectedNode && (() => {
          const mapping = getMappingForNode(selectedNode.id);
          return (
            <div className="node-drawer glass">
              <div className="drawer-header">
                <div>
                  <h4>{mapping ? mapping.native_service : selectedNode.label}</h4>
                  {mappedProvider && (
                    <span className="provider-badge">{mappedProvider.toUpperCase()}</span>
                  )}
                </div>
                <button className="close-btn" onClick={() => setSelectedNode(null)}>✕</button>
              </div>
              <div className="drawer-body">
                {mapping ? (
                  <>
                    <div className="prop native">
                      <label>Native Service</label>
                      <span className="accent">{mapping.native_service}</span>
                    </div>
                    <div className="prop">
                      <label>SKU / Tier</label>
                      <span>{mapping.sku || 'N/A'}</span>
                    </div>
                    <div className="prop cost">
                      <label>Monthly Cost (Estimated)</label>
                      <span className="cost-val">₹{mapping.estimated_monthly_cost_inr?.toLocaleString() || 'N/A'}</span>
                      {mapping.pricing_note && <span className="cost-note">{mapping.pricing_note}</span>}
                    </div>
                    <div className="prop sla">
                      <label>SLA Availability</label>
                      <span>{mapping.sla_percentage}%</span>
                    </div>
                  </>
                ) : (
                  <>
                    <div className="prop">
                      <label>Component Type</label>
                      <span>{selectedNode.type.split('_').join(' ')}</span>
                    </div>
                    <div className="prop">
                      <label>Infrastructure Layer</label>
                      <span>{selectedNode.category}</span>
                    </div>
                  </>
                )}
                
                <div className="prop policy">
                  <label>Efficiency & Compliance</label>
                  <div className="policy-pill">
                    <span className="dot pulse"></span>
                    Governance Shield Active
                  </div>
                  <p>
                    {mapping 
                      ? mapping.notes || `Optimized for ${mappedProvider.toUpperCase()} reliability standards.` 
                      : `Governed by autonomous ${selectedNode.category} reliability policies synced within last 24h.`
                    }
                  </p>
                </div>
              </div>
            </div>
          );
        })()}

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

        <div className="phase-badge glass">
          <span className="phase-dot"></span>
          <span className="phase-text">{phase === 'scored' ? 'System Design Validated' : 'Exploring — Describe workload'}</span>
        </div>

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
          top: 0; left: 380px;
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
        .nav-actions { display: flex; gap: 12px; }
        .logout-btn, .reset-btn {
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
        .reset-btn { background: rgba(0, 245, 255, 0.1); border-color: rgba(0, 245, 255, 0.3); color: var(--accent-primary); }
        .reset-btn:hover { background: rgba(0, 245, 255, 0.2); }
        .main-content {
          position: fixed;
          top: 60px;
          left: 380px;
          right: 0;
          bottom: 0;
          overflow: hidden;
          background: radial-gradient(circle at 50% 50%, #0a0f12 0%, #05080a 100%);
        }
        .node-drawer {
          position: absolute;
          bottom: 24px;
          right: 360px;
          width: 320px;
          padding: 24px;
          z-index: 100;
          border-radius: var(--radius-soft);
          background: rgba(10, 15, 25, 0.98);
          border: 1px solid rgba(0, 245, 255, 0.3);
          backdrop-filter: blur(24px);
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.5);
          animation: drawerSlide 0.4s var(--ease-soft);
        }
        @keyframes drawerSlide { from { opacity: 0; transform: translateX(30px); } to { opacity: 1; transform: translateX(0); } }
        .drawer-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .drawer-header h4 { font-size: 13px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.12em; color: var(--accent-primary); }
        .provider-badge { font-size: 8px; font-weight: 900; color: var(--accent-primary); background: rgba(0, 245, 255, 0.1); padding: 2px 6px; border-radius: 4px; border: 1px solid rgba(0, 245, 255, 0.2); margin-top: 4px; display: inline-block; }
        .close-btn { background: rgba(255, 255, 255, 0.05); border: 1px solid var(--glass-border); color: var(--text-muted); width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; cursor: pointer; }
        .drawer-body { display: flex; flex-direction: column; gap: 16px; }
        .prop { display: flex; flex-direction: column; gap: 6px; }
        .prop label { font-size: 9px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; }
        .prop span { font-size: 14px; font-weight: 600; color: var(--text-primary); }
        .accent { color: var(--accent-primary) !important; }
        .cost-val { font-size: 18px !important; color: var(--accent-secondary) !important; font-weight: 800 !important; }
        .cost-note { font-size: 9px; color: var(--text-muted); font-style: italic; }
        .policy-pill { display: flex; align-items: center; gap: 6px; background: rgba(0, 245, 255, 0.05); border: 1px solid rgba(0, 245, 255, 0.2); padding: 4px 8px; border-radius: var(--radius-pill); font-size: 10px; color: var(--accent-primary); margin-bottom: 8px; width: fit-content; }
        .dot.pulse { width: 6px; height: 6px; background: var(--accent-primary); border-radius: 50%; box-shadow: 0 0 8px var(--accent-primary); }
        .prop.policy p { font-size: 11px; color: var(--text-secondary); line-height: 1.5; }
        .intel-status { position: absolute; top: 24px; left: 50%; transform: translateX(-50%); padding: 10px 20px; display: flex; align-items: center; gap: 16px; border-radius: var(--radius-pill); z-index: 5; }
        .status-label { font-size: 10px; font-weight: 900; text-transform: uppercase; color: var(--text-muted); }
        .statuses { display: flex; gap: 6px; }
        .pill { font-size: 9px; font-weight: 800; padding: 2px 8px; border-radius: 4px; color: var(--text-muted); background: rgba(255, 255, 255, 0.05); }
        .pill.active { color: var(--accent-primary); background: rgba(0, 245, 255, 0.1); border: 1px solid rgba(0, 245, 255, 0.2); }
        .phase-badge { position: absolute; top: 24px; left: 24px; padding: 10px 16px; display: flex; align-items: center; gap: 10px; border-radius: var(--radius-pill); z-index: 5; background: rgba(10, 15, 18, 0.6); }
        .phase-dot { width: 6px; height: 6px; border-radius: 50%; background: var(--accent-primary); box-shadow: 0 0 8px var(--accent-primary); }
        .phase-text { font-size: 10px; font-weight: 800; text-transform: uppercase; color: var(--text-primary); }
        .canvas-tools { position: absolute; bottom: 24px; left: 50%; transform: translateX(-50%); display: flex; align-items: center; gap: 16px; padding: 8px 12px; z-index: 5; border-radius: var(--radius-pill); background: rgba(10, 15, 18, 0.6); }
        .tool-group, .export-group { display: flex; gap: 4px; }
        .canvas-tools button { background: transparent; border: none; color: var(--text-secondary); font-size: 16px; cursor: pointer; min-width: 32px; height: 32px; display: flex; align-items: center; justify-content: center; border-radius: var(--radius-pill); transition: all 0.2s; }
        .canvas-tools button:hover:not(.export-btn) { background: rgba(255, 255, 255, 0.08); color: var(--text-primary); }
        .separator { width: 1px; height: 20px; background: var(--border-muted); }
        .export-btn { font-size: 9px !important; font-weight: 800; text-transform: uppercase; padding: 0 16px !important; border: 1px solid var(--border-muted) !important; background: var(--bg-secondary) !important; color: var(--text-secondary) !important; }
        .export-btn:hover { border-color: var(--accent-primary) !important; color: var(--accent-primary) !important; box-shadow: var(--shadow-electric); }
        .export-btn.aws:hover { border-color: #ff9900 !important; color: #ff9900 !important; }
        .export-btn.gcp:hover { border-color: #4285f4 !important; color: #4285f4 !important; }
        .export-btn.azure:hover { border-color: #0078d4 !important; color: #0078d4 !important; }
      `}</style>
    </main>
  );
}
