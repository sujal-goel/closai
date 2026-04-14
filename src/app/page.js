'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';

export default function LandingPage() {
  useEffect(() => {
    // Animate scan bar
    const style = document.createElement('style');
    style.textContent = `
      @keyframes scan { 0% { top: 0%; } 100% { top: 100%; } }
      @keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-18px); } }
      @keyframes pulse-glow { 0%, 100% { opacity: 1; box-shadow: 0 0 20px rgba(0, 245, 255, 0.5); } 50% { opacity: 0.7; box-shadow: 0 0 40px rgba(0, 245, 255, 0.9); } }
      @keyframes orbit { from { transform: rotate(0deg) translateX(80px) rotate(0deg); } to { transform: rotate(360deg) translateX(80px) rotate(-360deg); } }
      @keyframes orbit2 { from { transform: rotate(120deg) translateX(60px) rotate(-120deg); } to { transform: rotate(480deg) translateX(60px) rotate(-480deg); } }
      @keyframes orbit3 { from { transform: rotate(240deg) translateX(100px) rotate(-240deg); } to { transform: rotate(600deg) translateX(100px) rotate(-600deg); } }
      @keyframes fadeUp { from { opacity: 0; transform: translateY(30px); } to { opacity: 1; transform: translateY(0); } }
      @keyframes shimmer { 0% { background-position: -200% center; } 100% { background-position: 200% center; } }
      .fade-up { animation: fadeUp 0.8s ease forwards; }
      .delay-1 { animation-delay: 0.1s; opacity: 0; }
      .delay-2 { animation-delay: 0.2s; opacity: 0; }
      .delay-3 { animation-delay: 0.3s; opacity: 0; }
      .delay-4 { animation-delay: 0.4s; opacity: 0; }
      .delay-5 { animation-delay: 0.5s; opacity: 0; }
    `;
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  return (
    <div style={{ background: '#090d1f', color: '#e2e4fe', fontFamily: "'Inter', sans-serif", overflowX: 'hidden', minHeight: '100vh' }}>
      <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />

      {/* Dot Grid Background */}
      <div style={{
        position: 'fixed', inset: 0, zIndex: 0, pointerEvents: 'none',
        backgroundImage: 'radial-gradient(circle at 1.5px 1.5px, rgba(161,250,255,0.07) 1.5px, transparent 0)',
        backgroundSize: '32px 32px',
      }} />
      {/* Ambient blobs */}
      <div style={{ position: 'fixed', top: '-10%', left: '20%', width: 700, height: 700, borderRadius: '50%', background: 'radial-gradient(circle, rgba(157,80,255,0.08) 0%, transparent 70%)', filter: 'blur(80px)', pointerEvents: 'none', zIndex: 0 }} />
      <div style={{ position: 'fixed', bottom: '10%', right: '10%', width: 500, height: 500, borderRadius: '50%', background: 'radial-gradient(circle, rgba(0,245,255,0.05) 0%, transparent 70%)', filter: 'blur(80px)', pointerEvents: 'none', zIndex: 0 }} />

      {/* ── NAVBAR ── */}
      <nav style={{ position: 'fixed', top: 28, left: 0, right: 0, display: 'flex', justifyContent: 'center', zIndex: 1000, padding: '0 24px' }}>
        <div style={{
          background: 'rgba(31,36,63,0.7)', backdropFilter: 'blur(30px)', WebkitBackdropFilter: 'blur(30px)',
          border: '1px solid rgba(161,250,255,0.08)', borderRadius: 9999,
          display: 'flex', alignItems: 'center', gap: 48, padding: '10px 12px 10px 32px',
          boxShadow: '0 8px 40px rgba(0,0,0,0.4)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 34, height: 34, borderRadius: 10, background: 'rgba(0,245,255,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#00f5ff" strokeWidth="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>
            </div>
            <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 16, letterSpacing: '-0.02em' }}>CLOS AI</span>
          </div>
          <div style={{ display: 'flex', gap: 32 }}>
            {['Architecture', 'Solutions', 'Process', 'Team'].map(label => (
              <a key={label} href={`#${label.toLowerCase()}`} style={{ color: '#a7aac2', textDecoration: 'none', fontWeight: 600, fontSize: 15, transition: 'color 0.2s' }}
                onMouseEnter={e => e.target.style.color = '#e2e4fe'} onMouseLeave={e => e.target.style.color = '#a7aac2'}>{label}</a>
            ))}
          </div>
          <Link href="/signup" style={{
            background: 'linear-gradient(135deg, #a1faff, #b884ff)',
            color: '#090d1f', fontWeight: 800, fontSize: 14, padding: '12px 28px',
            borderRadius: 9999, textDecoration: 'none', transition: 'all 0.3s',
            boxShadow: '0 0 20px rgba(161,250,255,0.2)',
          }}>Get Started</Link>
        </div>
      </nav>

      {/* ── HERO ── */}
      <section style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '160px 80px 80px', maxWidth: 1400, margin: '0 auto', position: 'relative', zIndex: 1, gap: 40 }}>
        <div style={{ flex: '1.2', maxWidth: 680 }}>
          <div className="fade-up delay-1" style={{ display: 'inline-flex', alignItems: 'center', gap: 8, background: 'rgba(161,250,255,0.06)', border: '1px solid rgba(161,250,255,0.15)', borderRadius: 9999, padding: '6px 16px', marginBottom: 32, fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', color: '#a1faff' }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#a1faff', animation: 'pulse-glow 2s infinite' }} />
            Now Powered by Agentic Intelligence
          </div>
          <h1 className="fade-up delay-2" style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 900, fontSize: 'clamp(3rem, 5vw, 5rem)', lineHeight: 1.05, letterSpacing: '-0.04em', margin: '0 0 28px' }}>
            The Autonomous<br />
            <span style={{ background: 'linear-gradient(135deg, #a1faff 0%, #b884ff 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>Systems Architect</span>
          </h1>
          <p className="fade-up delay-3" style={{ fontSize: 18, color: '#a7aac2', lineHeight: 1.6, marginBottom: 48, maxWidth: 560 }}>
            Deploy complex multi-cloud ecosystems in seconds. Orchestrate neural data flows with factual, day-zero limit logic across AWS, GCP, and Azure.
          </p>
          <div className="fade-up delay-4" style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <Link href="/signup" style={{
              background: 'linear-gradient(135deg, #a1faff 0%, #b884ff 100%)',
              color: '#090d1f', fontWeight: 800, fontSize: 16, padding: '18px 40px',
              borderRadius: 9999, textDecoration: 'none',
              boxShadow: '0 0 30px rgba(161,250,255,0.25)',
              transition: 'all 0.3s',
            }}>Start Designing Free</Link>
            <a href="#solutions" style={{
              background: 'transparent', color: '#a1faff', fontWeight: 700, fontSize: 16,
              padding: '18px 40px', borderRadius: 9999, textDecoration: 'none',
              border: '1px solid rgba(161,250,255,0.3)', transition: 'all 0.3s',
            }}>Explore Capabilities</a>
          </div>
        </div>

        {/* Hero Visual — 3D node diagram */}
        <div className="fade-up delay-5" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', minWidth: 340 }}>
          <div style={{ position: 'relative', width: 380, height: 380, animation: 'float 7s ease-in-out infinite' }}>
            {/* Core node */}
            <div style={{
              position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)',
              width: 100, height: 100, borderRadius: '50%',
              background: 'radial-gradient(circle at 35% 35%, rgba(161,250,255,0.4), rgba(0,244,254,0.1))',
              border: '1px solid rgba(161,250,255,0.4)',
              boxShadow: '0 0 60px rgba(161,250,255,0.3), inset 0 0 40px rgba(161,250,255,0.1)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 11, color: '#a1faff', textAlign: 'center', lineHeight: 1.2,
            }}>CLOS<br/>AI</div>

            {/* Orbit rings */}
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 200, height: 200, borderRadius: '50%', border: '1px solid rgba(161,250,255,0.1)' }} />
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: 300, height: 300, borderRadius: '50%', border: '1px solid rgba(184,132,255,0.08)' }} />

            {/* Orbiting nodes */}
            {[
              { anim: 'orbit 6s linear infinite', color: '#a1faff', label: 'AWS', bg: 'rgba(161,250,255,0.1)' },
              { anim: 'orbit2 9s linear infinite', color: '#b884ff', label: 'GCP', bg: 'rgba(184,132,255,0.1)' },
              { anim: 'orbit3 12s linear infinite', color: '#ff60cd', label: 'Azure', bg: 'rgba(255,96,205,0.1)' },
            ].map(({ anim, color, label, bg }) => (
              <div key={label} style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', animation: anim }}>
                <div style={{ width: 52, height: 52, borderRadius: '50%', background: bg, border: `1px solid ${color}40`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 9, fontWeight: 800, color, boxShadow: `0 0 20px ${color}30` }}>{label}</div>
              </div>
            ))}

            {/* Connector lines SVG */}
            <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.3 }}>
              <line x1="190" y1="190" x2="270" y2="110" stroke="#a1faff" strokeWidth="1" strokeDasharray="4,4" />
              <line x1="190" y1="190" x2="110" y2="270" stroke="#b884ff" strokeWidth="1" strokeDasharray="4,4" />
              <line x1="190" y1="190" x2="280" y2="260" stroke="#ff60cd" strokeWidth="1" strokeDasharray="4,4" />
            </svg>

            {/* Ambient glow under the diagram */}
            <div style={{ position: 'absolute', bottom: -40, left: '50%', transform: 'translateX(-50%)', width: 300, height: 60, background: 'radial-gradient(ellipse, rgba(161,250,255,0.15) 0%, transparent 70%)', filter: 'blur(20px)' }} />
          </div>
        </div>
      </section>

      {/* ── TRUST BAR ── */}
      <div style={{ borderTop: '1px solid rgba(255,255,255,0.04)', borderBottom: '1px solid rgba(255,255,255,0.04)', background: 'rgba(14,18,38,0.6)', backdropFilter: 'blur(12px)', position: 'relative', zIndex: 1 }}>
        <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px 80px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 48, flexWrap: 'wrap' }}>
          <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.12em', color: '#43475c' }}>Trusted by teams running</span>
          {[
            { label: 'AWS', color: '#FF9900' },
            { label: 'Google Cloud', color: '#4285F4' },
            { label: 'Microsoft Azure', color: '#0078D4' },
          ].map(({ label, color }) => (
            <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 20px', background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 9999 }}>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: color }} />
              <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 13, color: '#a7aac2' }}>{label}</span>
            </div>
          ))}
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 20px', background: 'rgba(161,250,255,0.05)', border: '1px solid rgba(161,250,255,0.2)', borderRadius: 9999 }}>
            <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#a1faff', animation: 'pulse-glow 1.5s infinite' }} />
            <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 13, color: '#a1faff' }}>Real-time Policy Sync</span>
          </div>
        </div>
      </div>

      {/* ── FEATURES BENTO ── */}
      <section id="solutions" style={{ padding: '140px 80px', maxWidth: 1400, margin: '0 auto', position: 'relative', zIndex: 1 }}>
        <div style={{ textAlign: 'center', marginBottom: 80 }}>
          <p style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.14em', color: '#a1faff', marginBottom: 16 }}>Product Capabilities</p>
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 'clamp(2rem, 4vw, 3.5rem)', letterSpacing: '-0.03em', margin: '0 0 16px' }}>Factual Intelligence Across<br />Every Cloud Dimension</h2>
          <p style={{ color: '#a7aac2', fontSize: 18, maxWidth: 540, margin: '0 auto' }}>Our agentic crawlers index the policies others miss.</p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gridTemplateRows: 'auto auto', gap: 20 }}>
          {/* Large card — Autonomous Crawling */}
          <div id="architecture" style={{
            gridRow: 'span 2', background: 'rgba(20, 24, 46, 0.7)', backdropFilter: 'blur(20px)',
            border: '1px solid rgba(255,255,255,0.06)', borderRadius: 24, padding: 40,
            transition: 'border-color 0.3s, transform 0.3s',
            boxShadow: '0 0 40px rgba(0,0,0,0.3)',
          }}>
            <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(161,250,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 28 }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#a1faff" strokeWidth="2"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/></svg>
            </div>
            <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 22, marginBottom: 12 }}>Autonomous Crawling</h3>
            <p style={{ color: '#a7aac2', lineHeight: 1.6, marginBottom: 32 }}>Our agentic crawlers continuously index technical policies, limits, and pricing across 400+ services. Updated every 24 hours without any manual intervention.</p>
            {/* Scan anim */}
            <div style={{ position: 'relative', height: 160, borderRadius: 14, overflow: 'hidden', background: 'rgba(0,0,0,0.3)', backgroundImage: 'radial-gradient(rgba(161,250,255,0.05) 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
              <div style={{ position: 'absolute', left: 0, right: 0, height: 2, background: 'linear-gradient(90deg, transparent, #a1faff, transparent)', boxShadow: '0 0 12px #a1faff', animation: 'scan 2.4s linear infinite' }} />
              {/* Mock data lines */}
              {[30, 55, 75, 95, 115, 135].map((top, i) => (
                <div key={i} style={{ position: 'absolute', top, left: 16, right: 16, height: 1, background: `rgba(161,250,255,${0.04 + i * 0.02})`, borderRadius: 2 }} />
              ))}
            </div>
          </div>

          {/* Multi-Cloud Sync */}
          <div style={{ background: 'rgba(20,24,46,0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 24, padding: 36 }}>
            <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(184,132,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#b884ff" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            </div>
            <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 20, marginBottom: 10 }}>Multi-Cloud Sync</h3>
            <p style={{ color: '#a7aac2', lineHeight: 1.6, fontSize: 15 }}>Real-time parity analysis between AWS, GCP, and Azure regions with zero manual overhead.</p>
          </div>

          {/* SLA Optimization */}
          <div style={{ background: 'rgba(20,24,46,0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 24, padding: 36 }}>
            <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(255,96,205,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#ff60cd" strokeWidth="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
            </div>
            <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 20, marginBottom: 10 }}>SLA Optimization</h3>
            <p style={{ color: '#a7aac2', lineHeight: 1.6, fontSize: 15 }}>AI-driven predictive design for 99.999% availability with automated node placement and global redundancy logic.</p>
          </div>

          {/* Intelligent Canvas — wide */}
          <div style={{ gridColumn: 'span 2', background: 'rgba(20,24,46,0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 24, padding: 36, display: 'flex', gap: 32, alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <div style={{ width: 48, height: 48, borderRadius: 14, background: 'rgba(0,136,255,0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 24 }}>
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0088ff" strokeWidth="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
              </div>
              <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 20, marginBottom: 10 }}>Intelligent Canvas</h3>
              <p style={{ color: '#a7aac2', lineHeight: 1.6, fontSize: 15, marginBottom: 20 }}>Manipulate nodes and watch as our AI validates your architecture against 1,200+ compliance rules in real-time.</p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {['Live Cost Impact', 'Compliance Guardrails', '1-Click Terraform Export'].map(f => (
                  <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 14, color: '#a7aac2' }}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#a1faff" strokeWidth="3"><polyline points="20 6 9 17 4 12"/></svg>
                    {f}
                  </div>
                ))}
              </div>
            </div>
            {/* Canvas mockup */}
            <div style={{ flex: 1.4, background: '#05081a', borderRadius: 16, border: '1px solid rgba(255,255,255,0.08)', overflow: 'hidden', height: 200 }}>
              <div style={{ padding: '10px 16px', background: 'rgba(255,255,255,0.02)', borderBottom: '1px solid rgba(255,255,255,0.05)', display: 'flex', alignItems: 'center', gap: 8 }}>
                {['#ff5f56','#ffbd2e','#27c93f'].map(c => <span key={c} style={{ width: 8, height: 8, borderRadius: '50%', background: c, opacity: 0.5 }} />)}
                <span style={{ fontSize: 10, color: '#43475c', marginLeft: 8, fontFamily: 'monospace' }}>project-alpha.tf</span>
              </div>
              <div style={{ position: 'relative', flex: 1, padding: 20, backgroundImage: 'radial-gradient(rgba(255,255,255,0.04) 1px, transparent 1px)', backgroundSize: '20px 20px', height: '100%' }}>
                <div style={{ position: 'absolute', top: '20%', left: '15%', background: 'rgba(161,250,255,0.1)', border: '1px solid rgba(161,250,255,0.4)', color: '#a1faff', borderRadius: 6, padding: '6px 14px', fontSize: 10, fontWeight: 700 }}>App Service</div>
                <div style={{ position: 'absolute', bottom: '25%', right: '15%', background: 'rgba(184,132,255,0.1)', border: '1px solid rgba(184,132,255,0.4)', color: '#b884ff', borderRadius: 6, padding: '6px 14px', fontSize: 10, fontWeight: 700 }}>Database</div>
                <svg style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', opacity: 0.3 }}>
                  <line x1="30%" y1="35%" x2="70%" y2="60%" stroke="#a1faff" strokeWidth="1" strokeDasharray="3,3" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section id="process" style={{ padding: '100px 80px', background: 'rgba(14,18,38,0.4)', position: 'relative', zIndex: 1 }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: 80 }}>
            <p style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.14em', color: '#b884ff', marginBottom: 16 }}>The Process</p>
            <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 'clamp(2rem, 4vw, 3rem)', letterSpacing: '-0.03em' }}>From Idea to Infrastructure<br />in Three Steps</h2>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24, position: 'relative' }}>
            {/* Connecting line */}
            <div style={{ position: 'absolute', top: 40, left: '17%', right: '17%', height: 1, background: 'linear-gradient(90deg, rgba(161,250,255,0.3), rgba(184,132,255,0.3))', zIndex: 0 }} />
            {[
              { num: '01', title: 'Describe Workload', desc: 'Input your business requirements and performance targets in natural language. No DevOps jargon required.', color: '#a1faff' },
              { num: '02', title: 'AI Scores Providers', desc: 'Our engine evaluates 500+ global data centers based on cost, latency, compliance, and CO₂ footprint.', color: '#b884ff' },
              { num: '03', title: 'Get Blueprint', desc: 'Receive an immutable, IaC-ready architecture file mapped to native services and priced in real-time.', color: '#ff60cd' },
            ].map(({ num, title, desc, color }) => (
              <div key={num} style={{ textAlign: 'center', padding: '40px 32px', background: 'rgba(20,24,46,0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 24, position: 'relative', zIndex: 1 }}>
                <div style={{ width: 72, height: 72, borderRadius: '50%', background: `${color}12`, border: `1px solid ${color}40`, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 28px', fontFamily: "'Space Grotesk', sans-serif", fontWeight: 900, fontSize: 22, color, boxShadow: `0 0 30px ${color}20` }}>{num}</div>
                <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 20, marginBottom: 12 }}>{title}</h3>
                <p style={{ color: '#a7aac2', lineHeight: 1.6, fontSize: 15 }}>{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── TEAM ── */}
      <section id="team" style={{ padding: '120px 80px', maxWidth: 1400, margin: '0 auto', position: 'relative', zIndex: 1 }}>
        <div style={{ textAlign: 'center', marginBottom: 80 }}>
          <p style={{ fontSize: 12, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.14em', color: '#ff60cd', marginBottom: 16 }}>The Architects</p>
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 'clamp(2rem, 4vw, 3rem)', letterSpacing: '-0.03em' }}>Technical Leadership</h2>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 28 }}>
          {[
            { name: 'Kanak Goel', role: 'Chief Architect', img: '/kanak.png', bio: 'Former AWS Principal. Specialist in high-availability distributed systems and agentic pipelines.' },
            { name: 'Mehul Sharma', role: 'Neural Architect', img: '/mehul.jpg', bio: 'Leading crawler logic for factual policy indexing and real-time documentation synthesis.' },
            { name: 'Vivek Kumar Sahani', role: 'Strategy Director', img: '/team-3.png', bio: '20+ years scaling cloud infrastructure and pioneering autonomous AI deployment engines.' },
          ].map(({ name, role, img, bio }) => (
            <div key={name} style={{ textAlign: 'center', padding: '48px 36px', background: 'rgba(20,24,46,0.7)', backdropFilter: 'blur(20px)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 24, transition: 'border-color 0.3s, transform 0.3s' }}>
              <div style={{ width: 88, height: 88, borderRadius: '50%', margin: '0 auto 24px', border: '2px solid rgba(161,250,255,0.25)', boxShadow: '0 0 20px rgba(161,250,255,0.15)', overflow: 'hidden', position: 'relative' }}>
                <Image src={img} alt={name} fill sizes="88px" style={{ objectFit: 'cover' }} />
              </div>
              <h3 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 20, marginBottom: 6 }}>{name}</h3>
              <p style={{ color: '#a1faff', fontWeight: 700, fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em', marginBottom: 16 }}>{role}</p>
              <p style={{ color: '#a7aac2', lineHeight: 1.6, fontSize: 14, marginBottom: 24 }}>{bio}</p>
              <div style={{ display: 'flex', justifyContent: 'center', gap: 16 }}>
                {['M', 'L'].map(icon => (
                  <div key={icon} style={{ width: 32, height: 32, borderRadius: '50%', background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', fontSize: 11, color: '#71748b' }}>{icon}</div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── FINAL CTA ── */}
      <section style={{ padding: '80px 80px 120px', position: 'relative', zIndex: 1 }}>
        <div style={{
          maxWidth: 1100, margin: '0 auto', padding: '100px 80px', textAlign: 'center',
          background: 'rgba(20,24,46,0.6)', backdropFilter: 'blur(20px)',
          borderRadius: 32, position: 'relative', overflow: 'hidden',
        }}>
          {/* Gradient border */}
          <div style={{ position: 'absolute', inset: 0, borderRadius: 32, padding: 1, background: 'linear-gradient(135deg, rgba(161,250,255,0.3), rgba(184,132,255,0.15), rgba(255,96,205,0.2))', WebkitMask: 'linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)', WebkitMaskComposite: 'xor', maskComposite: 'exclude', pointerEvents: 'none' }} />
          {/* Background glow */}
          <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at center, rgba(161,250,255,0.05) 0%, transparent 70%)', borderRadius: 32, pointerEvents: 'none' }} />
          <h2 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 900, fontSize: 'clamp(2rem, 4vw, 3.5rem)', letterSpacing: '-0.03em', marginBottom: 20, position: 'relative' }}>
            Ready to design with<br />
            <span style={{ background: 'linear-gradient(135deg, #a1faff, #b884ff)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent', backgroundClip: 'text' }}>absolute facts?</span>
          </h2>
          <p style={{ color: '#a7aac2', fontSize: 18, marginBottom: 48, maxWidth: 500, margin: '0 auto 48px', position: 'relative' }}>
            Join 2,000+ engineers building reliable multi-cloud systems with day-zero intelligence.
          </p>
          <Link href="/signup" style={{
            display: 'inline-block', background: 'linear-gradient(135deg, #a1faff 0%, #b884ff 100%)',
            color: '#090d1f', fontWeight: 800, fontSize: 17, padding: '20px 56px',
            borderRadius: 9999, textDecoration: 'none', boxShadow: '0 0 40px rgba(161,250,255,0.25)',
            position: 'relative',
          }}>Launch Architect Now</Link>
        </div>
      </section>

      {/* ── FOOTER ── */}
      <footer style={{ borderTop: '1px solid rgba(255,255,255,0.04)', padding: '60px 80px 48px', position: 'relative', zIndex: 1, background: 'rgba(9,13,31,0.8)' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: 60, marginBottom: 60, flexWrap: 'wrap' }}>
            <div style={{ maxWidth: 280 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
                <div style={{ width: 32, height: 32, borderRadius: 9, background: 'rgba(0,245,255,0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#00f5ff" strokeWidth="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/></svg>
                </div>
                <span style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 800, fontSize: 15 }}>CLOS AI</span>
              </div>
              <p style={{ color: '#71748b', fontSize: 14, lineHeight: 1.6 }}>Autonomous system design and multi-cloud optimization. Fact-based, agent-driven.</p>
            </div>
            <div style={{ display: 'flex', gap: 64, flexWrap: 'wrap' }}>
              {[
                { title: 'Platform', links: ['Features', 'Architecture Lab', 'Security'] },
                { title: 'Company', links: ['Team', 'About', 'Careers'] },
                { title: 'Resources', links: ['Documentation', 'API', 'Legal'] },
              ].map(({ title, links }) => (
                <div key={title}>
                  <h4 style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 700, fontSize: 13, marginBottom: 20, color: '#e2e4fe' }}>{title}</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {links.map(l => <a key={l} href="#" style={{ color: '#71748b', textDecoration: 'none', fontSize: 14, transition: 'color 0.2s' }} onMouseEnter={e => e.target.style.color = '#a1faff'} onMouseLeave={e => e.target.style.color = '#71748b'}>{l}</a>)}
                  </div>
                </div>
              ))}
            </div>
          </div>
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: 32, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
            <p style={{ color: '#43475c', fontSize: 13, fontFamily: 'monospace' }}>© 2026 CLOS AI. NEURAL ARCHITECTURE SECURED.</p>
            <p style={{ color: '#43475c', fontSize: 11, textTransform: 'uppercase', letterSpacing: '0.1em' }}>AETHERIC FLUX v2.1</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
