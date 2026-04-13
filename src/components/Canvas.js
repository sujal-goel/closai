'use client';

import React, { useState, useEffect } from 'react';

/**
 * Node Types: api_server, gpu_worker, background_worker, scheduler,
 * relational_database, document_store, cache, object_storage, data_warehouse,
 * api_gateway, load_balancer, cdn, message_queue,
 * auth_service, secrets_manager, logging, metrics, alerting
 */

const Canvas = ({ 
  nodes = [], 
  edges = [], 
  onNodeClick, 
  selectedNodeId,
  activeMapping = null,
  provider = null
}) => {
  const mappings = activeMapping?.mappings || [];

  return (
    <div className="canvas-wrapper">
      <div className="canvas-grid"></div>
      
      <svg className="canvas-edges">
        {edges.map((edge, index) => {
          const sourceNode = nodes.find(n => n.id === edge.source);
          const targetNode = nodes.find(n => n.id === edge.target);
          if (!sourceNode || !targetNode) return null;
          
          return (
            <g key={`edge-${index}`}>
              <line
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke="rgba(0, 245, 255, 0.15)"
                strokeWidth="2"
              />
              <circle r="3" fill="var(--accent-primary)">
                <animateMotion
                  dur="3s"
                  repeatCount="indefinite"
                  path={`M ${sourceNode.x} ${sourceNode.y} L ${targetNode.x} ${targetNode.y}`}
                />
              </circle>
            </g>
          );
        })}
      </svg>

      <div className="canvas-nodes">
        {nodes.map((node) => {
          const mapping = mappings.find(m => m.generic_id === node.id);
          const isMapped = !!mapping;
          
          return (
            <div
              key={node.id}
              className={`canvas-node ${node.type} ${selectedNodeId === node.id ? 'selected' : ''} ${isMapped ? provider : ''}`}
              onClick={() => onNodeClick?.(node)}
              style={{
                left: node.x,
                top: node.y,
                transform: 'translate(-50%, -50%)',
                animation: `nodeEntry 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards`,
              }}
            >
              <div className="node-icon">
                {getIconForType(node.type)}
                {isMapped && <div className="provider-badge">{provider}</div>}
              </div>
              <div className="node-label">
                {isMapped ? mapping.native_service : (node.label || node.id)}
              </div>
              
              {isMapped ? (
                <div className="node-specs glass">
                  <div className="spec-item" title="Estimated Monthly Cost">
                    <span className="spec-icon">💰</span>
                    <span className="spec-val">${mapping.estimated_monthly_cost_usd}</span>
                  </div>
                  <div className="spec-item" title="Typical Latency">
                    <span className="spec-icon">⚡</span>
                    <span className="spec-val">{mapping.estimated_latency_ms}ms</span>
                  </div>
                  <div className="spec-item" title="SLA Guarantee">
                    <span className="spec-icon">✅</span>
                    <span className="spec-val">{mapping.sla_percentage}%</span>
                  </div>
                </div>
              ) : (
                <div className="node-status">{node.status || 'Active'}</div>
              )}
            </div>
          );
        })}
      </div>

      <style jsx>{`
        .canvas-wrapper {
          position: absolute;
          inset: 0;
          overflow: auto;
          background: radial-gradient(circle at center, #11181e 0%, #0a0f12 100%);
          cursor: grab;
        }
        
        .canvas-grid {
          position: absolute;
          inset: -2000px;
          background-image: 
            linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px);
          background-size: 50px 50px;
          pointer-events: none;
        }

        .canvas-edges {
          position: absolute;
          inset: 0;
          width: 2000px;
          height: 2000px;
          pointer-events: none;
        }

        .canvas-nodes {
          position: relative;
          width: 2000px;
          height: 2000px;
        }

        .canvas-node {
          position: absolute;
          width: 140px;
          height: 140px;
          background: rgba(15, 23, 28, 0.85);
          border: 1px solid var(--glass-border);
          border-radius: var(--radius-soft);
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 16px;
          backdrop-filter: blur(16px);
          transition: all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
          user-select: none;
          gap: 12px;
          box-shadow: var(--shadow-whisper);
        }

        .canvas-node:hover {
          border-color: var(--accent-primary);
          box-shadow: 0 0 30px rgba(0, 245, 255, 0.25);
          transform: translate(-50%, -50%) scale(1.08);
          z-index: 10;
        }

        .canvas-node.selected {
          border-color: var(--accent-primary);
          box-shadow: 0 0 40px rgba(0, 245, 255, 0.4);
          background: rgba(0, 245, 255, 0.1);
        }

        @keyframes nodeEntry {
          from { opacity: 0; transform: translate(-50%, -50%) scale(0.4); filter: blur(10px); }
          to { opacity: 1; transform: translate(-50%, -50%) scale(1); filter: blur(0); }
        }

        .node-icon {
          font-size: 28px;
          color: var(--accent-primary);
          background: rgba(0, 245, 255, 0.08);
          width: 56px;
          height: 56px;
          border-radius: var(--radius-precise);
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform 0.3s var(--ease-soft);
        }

        .canvas-node:hover .node-icon {
          transform: scale(1.1) rotate(5deg);
        }

        .node-label {
          font-size: 11px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          text-align: center;
          color: var(--text-primary);
        }

        .node-status {
          font-size: 9px;
          font-weight: 700;
          color: var(--accent-primary);
          padding: 3px 10px;
          background: rgba(0, 245, 255, 0.05);
          border-radius: var(--radius-pill);
          text-transform: uppercase;
          letter-spacing: 0.05em;
          border: 1px solid rgba(0, 245, 255, 0.1);
        }

        /* Type specific branding */
        .compute { border-bottom: 3px solid var(--accent-primary); }
        .data { border-bottom: 3px solid var(--accent-secondary); }
        .network { border-bottom: 3px solid #00ffa3; }
        .security { border-bottom: 3px solid var(--accent-tertiary); }

        /* Provider specific branding */
        .aws { border-color: #ff9900; box-shadow: 0 0 20px rgba(255, 153, 0, 0.1); }
        .gcp { border-color: #4285f4; box-shadow: 0 0 20px rgba(66, 133, 244, 0.1); }
        .azure { border-color: #0078d4; box-shadow: 0 0 20px rgba(0, 120, 212, 0.1); }

        .provider-badge {
          position: absolute;
          top: -8px;
          right: -8px;
          background: #000;
          color: #fff;
          font-size: 8px;
          font-weight: 900;
          text-transform: uppercase;
          padding: 2px 6px;
          border-radius: 4px;
          border: 1px solid rgba(255,255,255,0.2);
        }

        .node-specs {
          display: flex;
          flex-direction: column;
          gap: 4px;
          padding: 6px 10px;
          background: rgba(0,0,0,0.4);
          border-radius: 8px;
          width: 100%;
        }

        .spec-item {
          display: flex;
          align-items: center;
          gap: 6px;
        }

        .spec-icon { font-size: 10px; filter: grayscale(1); }
        .spec-val {
          font-size: 9px;
          font-weight: 700;
          color: var(--text-secondary);
        }

        .aws .node-specs { border-left: 2px solid #ff9900; }
        .gcp .node-specs { border-left: 2px solid #4285f4; }
        .azure .node-specs { border-left: 2px solid #0078d4; }
      `}</style>
    </div>
  );
};

function getIconForType(type) {
  // Simple mapping, can be replaced with SVG icons later
  const icons = {
    api_server: '⚡',
    gpu_worker: '🧠',
    relational_database: '💾',
    document_store: '📄',
    message_queue: '📥',
    api_gateway: '🌐',
    load_balancer: '⚖️',
    auth_service: '🔑',
    object_storage: '📦',
  };
  return icons[type] || '⚙️';
}

export default Canvas;
