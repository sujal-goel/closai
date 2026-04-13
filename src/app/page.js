'use client';

import React from 'react';
import Link from 'next/link';

export default function LandingPage() {
  return (
    <div className="landing-container">
      {/* Navbar */}
      <nav className="navbar glass">
        <div className="nav-logo">
          <span className="logo-icon">☁️</span>
          <span className="logo-text">CloudCompare <span className="badge">v2</span></span>
        </div>
        <div className="nav-links">
          <Link href="/login" className="nav-link">Sign In</Link>
          <Link href="/signup" className="nav-button">Get Started</Link>
        </div>
      </nav>

      {/* Hero Section */}
      <main className="hero-section">
        <div className="hero-content">
          <div className="pill-badge">
            <span className="dot pulse"></span>
            Now Powered by Live Global Market Intel
          </div>
          <h1 className="hero-title">
            Your Autonomous <br />
            <span className="gradient-text">Principal Systems Architect</span>
          </h1>
          <p className="hero-subtitle">
            Instantly design, score, and optimize cloud infrastructure. 
            We continuously crawl deep technical policies across AWS, GCP, and Azure 
            so you design with factual, day-zero limit logic—not guesswork.
          </p>
          
          <div className="cta-group">
            <Link href="/signup" className="cta-primary">
              Start Designing Free →
            </Link>
            <a href="#features" className="cta-secondary">
              See How It Works
            </a>
          </div>
        </div>

        {/* Abstract 3D/Glass Architecture Graphic */}
        <div className="hero-visual">
          <div className="glass-card card-1">
            <div className="card-header">Autonomous Crawl</div>
            <div className="metric">1.2M+ Policies Indexed</div>
          </div>
          <div className="glass-card card-2">
            <div className="card-header">Cost Optimization</div>
            <div className="metric">Live Pricing Sync</div>
          </div>
          <div className="glass-card card-3">
            <div className="card-header">SLA Engine</div>
            <div className="metric">Multi-Region RTO & RPO</div>
          </div>
          <div className="glow-orb orb-1"></div>
          <div className="glow-orb orb-2"></div>
        </div>
      </main>

      <style jsx>{`
        .landing-container {
          min-height: 100vh;
          background: var(--bg-primary);
          overflow-x: hidden;
          position: relative;
          color: var(--text-primary);
        }

        .navbar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 16px 40px;
          position: fixed;
          top: 24px;
          left: 50%;
          transform: translateX(-50%);
          width: calc(100% - 96px);
          max-width: 1200px;
          z-index: 100;
          border-radius: var(--radius-pill);
        }

        .nav-logo {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        .logo-text { font-weight: 800; font-size: 18px; }
        .badge {
          font-size: 10px;
          color: var(--accent-primary);
          border: 1px solid var(--accent-primary);
          padding: 2px 6px;
          border-radius: 4px;
          margin-left: 6px;
          vertical-align: middle;
        }

        .nav-links {
          display: flex;
          align-items: center;
          gap: 24px;
        }

        .nav-link {
          color: var(--text-secondary);
          font-weight: 600;
          text-decoration: none;
          font-size: 14px;
          transition: color 0.2s;
        }
        .nav-link:hover { color: var(--text-primary); }

        .nav-button {
          background: rgba(255, 255, 255, 0.08);
          border: 1px solid var(--glass-border);
          color: var(--text-primary);
          padding: 8px 16px;
          border-radius: var(--radius-pill);
          text-decoration: none;
          font-weight: 700;
          font-size: 14px;
          transition: all 0.3s;
        }
        .nav-button:hover {
          background: var(--text-primary);
          color: var(--bg-primary);
        }

        .hero-section {
          min-height: 100vh;
          display: flex;
          max-width: 1200px;
          margin: 0 auto;
          padding: 160px 48px;
          position: relative;
          align-items: center;
          gap: 80px;
        }

        .hero-content {
          flex: 1;
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          z-index: 10;
        }

        .pill-badge {
          display: flex;
          align-items: center;
          gap: 10px;
          background: rgba(0, 245, 255, 0.05);
          border: 1px solid rgba(0, 245, 255, 0.15);
          color: var(--accent-primary);
          padding: 6px 16px;
          border-radius: var(--radius-pill);
          font-size: 11px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-bottom: 24px;
        }

        .dot {
          width: 6px; height: 6px;
          background: var(--accent-primary);
          border-radius: 50%;
          box-shadow: 0 0 10px var(--accent-primary);
        }

        .pulse { animation: pulseAnim 2s infinite; }
        @keyframes pulseAnim { 0%, 100% { opacity: 1; } 50% { opacity: 0.3; } }

        .hero-title {
          font-size: 56px;
          line-height: 1.1;
          font-weight: 900;
          margin-bottom: 24px;
          letter-spacing: -0.02em;
        }

        .gradient-text {
          background: linear-gradient(135deg, var(--accent-primary), #00ffaa);
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .hero-subtitle {
          font-size: 18px;
          color: var(--text-secondary);
          line-height: 1.6;
          max-width: 500px;
          margin-bottom: 48px;
        }

        .cta-group {
          display: flex;
          gap: 16px;
          align-items: center;
        }

        .cta-primary {
          background: var(--accent-primary);
          color: #000;
          font-weight: 800;
          font-size: 15px;
          padding: 16px 32px;
          border-radius: var(--radius-pill);
          text-decoration: none;
          box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
          transition: all 0.3s;
        }
        .cta-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 0 30px rgba(0, 245, 255, 0.4);
        }

        .cta-secondary {
          color: var(--text-secondary);
          text-decoration: none;
          font-weight: 700;
          font-size: 15px;
          padding: 16px 24px;
          transition: color 0.3s;
        }
        .cta-secondary:hover { color: var(--text-primary); }

        .hero-visual {
          flex: 1;
          position: relative;
          height: 500px;
          perspective: 1000px;
        }

        .glass-card {
          position: absolute;
          background: rgba(20, 25, 30, 0.6);
          border: 1px solid rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(16px);
          padding: 24px;
          border-radius: var(--radius-soft);
          box-shadow: var(--shadow-whisper);
          animation: float 6s ease-in-out infinite;
        }

        .card-1 {
          top: 10%; right: 10%; width: 240px;
          animation-delay: 0s;
        }
        .card-2 {
          top: 45%; right: 30%; width: 220px; z-index: 2;
          animation-delay: -2s;
        }
        .card-3 {
          bottom: 10%; right: 5%; width: 260px;
          animation-delay: -4s;
        }

        .card-header {
          font-size: 10px;
          text-transform: uppercase;
          color: var(--accent-primary);
          font-weight: 800;
          letter-spacing: 0.1em;
          margin-bottom: 8px;
        }

        .metric {
          font-size: 20px;
          font-weight: 800;
        }

        .glow-orb {
          position: absolute;
          border-radius: 50%;
          filter: blur(80px);
          z-index: 0;
          opacity: 0.4;
        }

        .orb-1 {
          width: 300px; height: 300px;
          background: var(--accent-primary);
          top: 20%; right: 20%;
        }

        .orb-2 {
          width: 250px; height: 250px;
          background: #00ffaa;
          bottom: 10%; right: 40%;
        }

        @keyframes float {
          0%, 100% { transform: translateY(0) rotateX(0) rotateY(0); }
          50% { transform: translateY(-20px) rotateX(5deg) rotateY(5deg); }
        }

        @media (max-width: 900px) {
          .hero-section { flex-direction: column; text-align: center; padding-top: 120px; }
          .hero-content { align-items: center; }
          .hero-subtitle { margin: 0 auto 32px; }
          .hero-visual { width: 100%; height: 400px; }
        }
      `}</style>
    </div>
  );
}
