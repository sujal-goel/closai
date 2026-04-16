'use client';

import React from 'react';

const ArchitecturalReport = ({ plan, onClose }) => {
  if (!plan) return null;

  return (
    <div className="report-container glass">
      <div className="report-header">
        <div className="header-top">
          <span className="badge">Factual Deployment Plan</span>
          <button className="close-btn" onClick={onClose} title="Dismiss Report">✕</button>
        </div>
        <h3>Infrastructure Guardrails</h3>
      </div>

      <div className="metrics-grid">
        <div className="metric-card">
          <label>Latency (E2E)</label>
          <div className="value-group">
            <span className="value">{plan.expected_latency_ms}</span>
            <span className="unit">ms</span>
          </div>
          <p className="desc">Estimated response time based on provider benchmarks.</p>
        </div>

        <div className="metric-card highlight">
          <label>Max Concurrency</label>
          <div className="value-group">
            <span className="value">{plan.concurrency_limit.toLocaleString()}</span>
            <span className="unit">req/s</span>
          </div>
          <p className="desc">Design bottleneck identified at the primary compute node.</p>
        </div>

        <div className="metric-card">
          <label>Total Capacity</label>
          <div className="value-group">
            <span className="value">{(plan.total_users_capacity / 1000).toFixed(1)}k</span>
            <span className="unit">Users</span>
          </div>
          <p className="desc">Theoretical max users sustained during peak load.</p>
        </div>

        <div className="metric-card certs">
          <label>Compliance Audit</label>
          <div className="cert-list">
            {plan.compliance_status.map((cert, idx) => (
              <span key={idx} className="cert-pill">
                <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12"/>
                </svg>
                {cert}
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="report-footer">
        <span className="scalability">Scalability: <strong>{plan.scalability_rating}</strong></span>
        <span className="timestamp">Synced with live market policy</span>
      </div>

      <style jsx>{`
        .report-container {
          position: absolute;
          bottom: 110px;
          left: 24px;
          width: 380px;
          padding: 24px;
          z-index: 10;
          display: flex;
          flex-direction: column;
          gap: 24px;
          border-radius: var(--radius-soft);
          background: rgba(10, 15, 18, 0.9);
          border: 1px solid var(--accent-primary);
          box-shadow: 0 0 30px rgba(0, 245, 255, 0.1);
        }

        .report-header {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }
        
        .header-top {
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .close-btn {
          background: transparent;
          border: none;
          color: var(--text-muted);
          cursor: pointer;
          font-size: 14px;
          padding: 4px;
          line-height: 1;
          transition: all 0.2s;
        }
        
        .close-btn:hover {
          color: var(--accent-primary);
          transform: scale(1.1);
        }

        .badge {
          font-size: 10px;
          font-weight: 800;
          color: var(--accent-primary);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          background: rgba(0, 245, 255, 0.1);
          padding: 4px 10px;
          border-radius: var(--radius-pill);
          width: fit-content;
        }

        .report-header h3 {
          font-size: 18px;
          font-weight: 800;
          color: var(--text-primary);
          letter-spacing: -0.02em;
        }

        .metrics-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 16px;
        }

        .metric-card {
          padding: 16px;
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid var(--glass-border);
          border-radius: var(--radius-precise);
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .metric-card.highlight {
          border-color: rgba(184, 132, 255, 0.4);
          background: rgba(184, 132, 255, 0.05);
        }

        .metric-card label {
          font-size: 9px;
          font-weight: 700;
          color: var(--text-muted);
          text-transform: uppercase;
          letter-spacing: 0.08em;
        }

        .value-group {
          display: flex;
          align-items: baseline;
          gap: 4px;
        }

        .value {
          font-size: 24px;
          font-weight: 800;
          color: var(--text-primary);
        }

        .unit {
          font-size: 10px;
          font-weight: 600;
          color: var(--text-muted);
        }

        .desc {
          font-size: 10px;
          color: var(--text-secondary);
          line-height: 1.4;
          margin-top: 4px;
        }

        .certs {
          grid-column: span 2;
        }

        .cert-list {
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
          margin-top: 8px;
        }

        .cert-pill {
          display: flex;
          align-items: center;
          gap: 6px;
          font-size: 10px;
          font-weight: 700;
          background: rgba(0, 245, 255, 0.05);
          border: 1px solid rgba(0, 245, 255, 0.2);
          color: var(--accent-primary);
          padding: 4px 10px;
          border-radius: var(--radius-pill);
        }

        .report-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-top: 16px;
          border-top: 1px solid var(--border-muted);
        }

        .scalability {
          font-size: 11px;
          color: var(--text-muted);
        }

        .scalability strong {
          color: var(--accent-secondary);
        }

        .timestamp {
          font-size: 9px;
          color: var(--text-muted);
          font-style: italic;
        }
      `}</style>
    </div>
  );
};

export default ArchitecturalReport;
