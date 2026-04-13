'use client';

import React from 'react';

const DecisionMatrix = ({ providers = [] }) => {
  // Sort providers by total score (example logic)
  const rankedProviders = [...providers].sort((a, b) => b.totalScore - a.totalScore);

  return (
    <div className="matrix-panel glass">
      <div className="matrix-header">
        <h3>Cloud Comparison</h3>
        <p>Ranked by best-fit SKUs</p>
      </div>
      
      <div className="provider-list">
        {rankedProviders.map((provider, idx) => (
          <div key={provider.id} className="provider-card">
            <div className="provider-info">
              <span className="rank-badge">#{idx + 1}</span>
              <span className="provider-name">{provider.name}</span>
              <span className="total-score">{provider.totalScore}%</span>
            </div>
            
            <div className="score-bars">
              {Object.entries(provider.dimensions).map(([key, value]) => (
                <div key={key} className="score-row">
                  <div className="row-meta">
                    <span className="dimension-label">{key.replace('_', ' ')}</span>
                    <span className="dimension-value">{value}%</span>
                  </div>
                  <div className="bar-track">
                    <div 
                      className="bar-fill" 
                      style={{ 
                        width: `${value}%`,
                        background: getBarColor(key)
                      }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>

            {provider.reasoning && (
              <div className="reasoning-box">
                <p>{provider.reasoning}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      <style jsx>{`
        .matrix-panel {
          position: absolute;
          top: 24px;
          right: 24px;
          width: 320px;
          max-height: calc(100vh - 48px);
          padding: 24px;
          display: flex;
          flex-direction: column;
          gap: 20px;
          z-index: 5;
          overflow-y: auto;
          scrollbar-width: none;
        }

        .matrix-panel::-webkit-scrollbar { display: none; }

        .matrix-header h3 {
          font-size: 14px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--accent-primary);
          margin-bottom: 4px;
        }

        .matrix-header p {
          font-size: 11px;
          color: var(--text-muted);
        }

        .provider-list {
          display: flex;
          flex-direction: column;
          gap: 28px;
        }

        .provider-card {
          display: flex;
          flex-direction: column;
          gap: 16px;
        }

        .provider-info {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .rank-badge {
          background: var(--bg-secondary);
          color: var(--accent-primary);
          border: 1px solid var(--accent-primary);
          font-size: 10px;
          font-weight: 800;
          padding: 2px 8px;
          border-radius: var(--radius-pill);
        }

        .provider-name {
          font-weight: 700;
          font-size: 14px;
          color: var(--text-primary);
          flex: 1;
        }

        .total-score {
          font-weight: 800;
          font-size: 16px;
          color: var(--accent-primary);
          text-shadow: 0 0 10px rgba(0, 245, 255, 0.3);
        }

        .score-bars {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .score-row {
          display: flex;
          flex-direction: column;
          gap: 6px;
        }

        .row-meta {
          display: flex;
          justify-content: space-between;
          font-size: 9px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--text-muted);
        }

        .bar-track {
          height: 6px;
          background: rgba(255, 255, 255, 0.03);
          border-radius: var(--radius-pill);
          overflow: hidden;
          border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .bar-fill {
          height: 100%;
          border-radius: var(--radius-pill);
          transition: width 1.2s cubic-bezier(0.34, 1.56, 0.64, 1);
          box-shadow: 0 0 10px currentColor;
        }

        .reasoning-box {
          margin-top: 8px;
          padding: 12px;
          background: rgba(255, 255, 255, 0.02);
          border-left: 2px solid var(--accent-primary);
          border-top-right-radius: var(--radius-precise);
          border-bottom-right-radius: var(--radius-precise);
        }

        .reasoning-box p {
          font-size: 11px;
          line-height: 1.5;
          color: var(--text-secondary);
          margin: 0;
          font-style: italic;
        }
      `}</style>
    </div>
  );
};

function getBarColor(dim) {
  const colors = {
    cost_efficiency: 'var(--accent-primary)',
    ops_complexity: 'var(--accent-secondary)',
    scalability: 'var(--accent-tertiary)',
    reliability: '#00ffa3',
    compliance: '#ffbb00',
    ecosystem: '#ff4400',
    future_roadmap: '#44ff00',
  };
  return colors[dim] || '#fff';
}

export default DecisionMatrix;
