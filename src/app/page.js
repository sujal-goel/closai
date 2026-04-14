'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { Icon } from '@iconify/react';

export default function LandingPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        type: "spring",
        stiffness: 100,
        damping: 12
      }
    }
  };

  return (
    <div className="landing-container">
      {/* Dynamic Background */}
      <div className="bg-mesh"></div>
      <div className="bg-gradient-top"></div>
      
      {/* Redesigned Floating Island Navbar */}
      <nav className="navbar-wrapper">
        <motion.nav 
          initial={{ y: -100, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ type: "spring", stiffness: 40, damping: 15 }}
          className="navbar floating-island"
        >
          <div className="nav-brand">
            <div className="brand-icon-wrapper">
              <Icon icon="lucide:cloud" className="logo-icon" width="22" height="22" />
            </div>
            <span className="logo-text">CLOS AI</span>
          </div>
          
          <div className="nav-main-links">
            <a href="#features" className="nav-item">
              <span className="nav-label">Features</span>
              <span className="nav-indicator"></span>
            </a>
            <a href="#team" className="nav-item">
              <span className="nav-label">Team</span>
              <span className="nav-indicator"></span>
            </a>
            <Link href="/login" className="nav-item">
              <span className="nav-label">Sign In</span>
              <span className="nav-indicator"></span>
            </Link>
          </div>

          <div className="nav-actions">
            <Link href="/signup" className="btn-get-started">
              Get Started
              <Icon icon="lucide:arrow-right" width="16" height="16" className="cta-icon" />
            </Link>
          </div>
        </motion.nav>
      </nav>

      {/* Hero Section */}
      <section className="hero">
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="hero-content"
        >
          <motion.div variants={itemVariants} className="pill-badge">
            <span className="dot pulse"></span>
            Now Powered by Agentic Intelligence
          </motion.div>
          
          <motion.h1 variants={itemVariants} className="hero-title">
            The Autonomous <br />
            <span className="gradient-text">Systems Architect</span>
          </motion.h1>
          
          <motion.p variants={itemVariants} className="hero-subtitle">
            Instantly design, score, and optimize multi-cloud infrastructure. 
            We index deep technical policies across AWS, GCP, and Azure 
            so you design with factual, day-zero limit logic.
          </motion.p>
          
          <motion.div variants={itemVariants} className="cta-group">
            <Link href="/signup" className="btn-hero-primary">
              Start Designing Free
            </Link>
            <a href="#features" className="btn-hero-secondary">
              Explore Capabilities
            </a>
          </motion.div>
        </motion.div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 1.2, ease: "easeOut" }}
          className="hero-visual"
        >
          <div className="image-wrapper">
            <Image 
              src="/hero-visual.png" 
              alt="Cloud Architecture Node" 
              width={700} 
              height={700} 
              priority
              className="floating-image"
            />
            <div className="visual-glow"></div>
          </div>
        </motion.div>
      </section>

      {/* Features Bento Grid */}
      <section className="features-section" id="features">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.1 }}
          variants={containerVariants}
          className="section-header"
        >
          <motion.h2 variants={itemVariants} className="section-title">Product Capabilities</motion.h2>
          <motion.p variants={itemVariants} className="section-subtitle">Factual intelligence across every cloud dimension.</motion.p>
        </motion.div>

        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.1 }}
          variants={containerVariants}
          className="bento-grid"
        >
          <motion.div variants={itemVariants} className="bento-card large glass-card">
            <div className="card-header-icon cyan"><Icon icon="lucide:search" width="24" height="24" /></div>
            <h3>Autonomous Crawling</h3>
            <p>Our agentic crawlers continuously index technical policies, limits, and pricing across 400+ services.</p>
            <div className="card-animation-crawling">
              <div className="scan-bar"></div>
              <div className="grid-overlay"></div>
            </div>
          </motion.div>

          <motion.div variants={itemVariants} className="bento-card glass-card">
            <div className="card-header-icon purple"><Icon icon="lucide:globe" width="24" height="24" /></div>
            <h3>Multi-Cloud Sync</h3>
            <p>Real-time parity analysis between AWS, GCP, and Azure regions with no manual overhead.</p>
          </motion.div>

          <motion.div variants={itemVariants} className="bento-card glass-card">
            <div className="card-header-icon pink"><Icon icon="lucide:zap" width="24" height="24" /></div>
            <h3>SLA Optimization</h3>
            <p>Design for 99.999% availability with automated node placement and redundancy logic.</p>
          </motion.div>

          <motion.div variants={itemVariants} id="product" className="bento-card wide glass-card showcase">
            <div className="showcase-info">
              <div className="card-header-icon blue"><Icon icon="lucide:cpu" width="24" height="24" /></div>
              <h3>Intelligent Canvas</h3>
              <p>Manipulate nodes and watch as our AI validates your architecture against 1,200+ compliance rules in real-time.</p>
              <ul className="mini-features">
                <li><Icon icon="lucide:check-circle" className="cyan-text" /> Live Cost Impact</li>
                <li><Icon icon="lucide:check-circle" className="cyan-text" /> Compliance Guardrails</li>
                <li><Icon icon="lucide:check-circle" className="cyan-text" /> 1-Click Terraform Export</li>
              </ul>
            </div>
            <div className="canvas-mockup">
              <div className="mockup-chrome">
                <div className="chrome-dots"><span className="r"></span><span className="y"></span><span className="g"></span></div>
                <div className="chrome-tab">project-alpha.tf</div>
              </div>
              <div className="mockup-content">
                <div className="mock-sidebar"></div>
                <div className="mock-workspace">
                  <motion.div 
                    animate={{ scale: [1, 1.05, 1], opacity: [0.8, 1, 0.8] }}
                    transition={{ duration: 4, repeat: Infinity }}
                    className="mock-node active"
                  >App Service</motion.div>
                  <div className="mock-node secondary">Database</div>
                </div>
              </div>
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* Team Section */}
      <section className="team-section" id="team">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.1 }}
          variants={containerVariants}
          className="section-header"
        >
          <motion.h2 variants={itemVariants} className="section-title">Technical Leadership</motion.h2>
          <motion.p variants={itemVariants} className="section-subtitle">Architecting the future of multi-cloud autonomy.</motion.p>
        </motion.div>

        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.1 }}
          variants={containerVariants}
          className="team-grid"
        >
          {[
            { name: "kanak goel", role: "Chief Architect", img: "/kanak.png", bio: "Fullstack developer and AI Enthusiasts" },
            { name: "Mehul Sharma", role: "Policy Engineer", img: "/mehul.jpg", bio: "Frontend Designer and Tech enthusiasts who designed the knowledge pipeline for this project" },
            { name: "Vivek Kumar Sahani", role: "VP Engineering", img: "/vivek.png", bio: "Backend Developer and AI Enthusiasts who worked on the database schemas and context management" }
          ].map((m, i) => (
            <motion.div key={i} variants={itemVariants} className="member-card glass-card">
              <div className="avatar-wrapper">
                <Image src={m.img} alt={m.name} width={100} height={100} className="member-avatar" />
              </div>
              <h3>{m.name}</h3>
              <p className="member-role">{m.role}</p>
              <p className="member-bio">{m.bio}</p>
              <div className="member-social">
                <Icon icon="ri:twitter-x-fill" width="18" />
                <Icon icon="ri:linkedin-box-fill" width="18" />
              </div>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Final CTA */}
      <section className="cta-section">
        <motion.div 
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, amount: 0.1 }}
          variants={itemVariants}
          className="cta-card glass-card accent-glow"
        >
          <h2>Ready to design with absolute facts?</h2>
          <p>Join 2,000+ engineers building reliable multi-cloud systems.</p>
          <Link href="/signup" className="btn-cta">
            Launch Architect Now
          </Link>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="footer-site">
        <div className="footer-main">
          <div className="footer-info">
            <div className="nav-logo">
              <Icon icon="lucide:cloud" className="logo-icon" width="24" height="24" />
              <span className="logo-text">CLOS AI</span>
            </div>
            <p className="footer-desc">Autonomous system design and multi-cloud optimization. Fact-based, agent-driven.</p>
            <div className="footer-social">
              <Icon icon="ri:twitter-x-fill" width="20" />
              <Icon icon="ri:linkedin-box-fill" width="20" />
              <Icon icon="ri:github-fill" width="20" />
            </div>
          </div>
          <div className="footer-links">
            <div className="footer-group">
              <h4>Platform</h4>
              <a href="#features">Features</a>
              <a href="#">Architecture Lab</a>
              <a href="#">Security</a>
            </div>
            <div className="footer-group">
              <h4>Company</h4>
              <a href="#team">Team</a>
              <a href="#">About</a>
              <a href="#">Careers</a>
            </div>
            <div className="footer-group">
              <h4>Resources</h4>
              <a href="#">Documentation</a>
              <a href="#">API</a>
              <a href="#">Legal</a>
            </div>
          </div>
        </div>
        <div className="footer-bottom">
          <p>&copy; 2026 ClosAI v2. All infrastructure validated.</p>
        </div>
      </footer>

      <style jsx>{`
        .landing-container {
          background-color: var(--bg-primary);
          color: var(--text-primary);
          min-height: 100vh;
          position: relative;
          overflow-x: hidden;
        }

        /* Background Effects */
        .bg-mesh {
          position: fixed;
          inset: 0;
          background-image: radial-gradient(circle at 2px 2px, rgba(255,255,255,0.03) 1px, transparent 0);
          background-size: 32px 32px;
          z-index: 0;
        }
        .bg-gradient-top {
          position: fixed;
          top: -10%; left: 50%;
          transform: translateX(-50%);
          width: 80%; height: 50%;
          background: radial-gradient(circle, rgba(157, 80, 255, 0.08) 0%, transparent 70%);
          z-index: 0;
          filter: blur(80px);
        }

        /* Navbar Redesign: Floating Island */
        .navbar-wrapper {
          position: fixed;
          top: 32px;
          left: 0; right: 0;
          display: flex;
          justify-content: center;
          z-index: 1000;
          padding: 0 24px;
        }

        .floating-island {
          background: rgba(10, 15, 30, 0.4);
          backdrop-filter: blur(24px) saturate(180%);
          -webkit-backdrop-filter: blur(24px) saturate(180%);
          border: 1px solid rgba(255, 255, 255, 0.08);
          border-radius: 100px;
          display: flex;
          align-items: center;
          padding: 8px 12px 8px 32px;
          gap: 60px;
          box-shadow: 0 16px 40px -12px rgba(0, 0, 0, 0.5);
        }

        .nav-brand {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .brand-icon-wrapper {
          width: 36px; height: 36px;
          background: rgba(0, 245, 255, 0.1);
          border-radius: 10px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--accent-primary);
        }
        .logo-text { font-weight: 800; font-size: 1.1rem; letter-spacing: -0.02em; }

        .nav-main-links {
          display: flex;
          gap: 32px;
        }
        .nav-item {
          text-decoration: none;
          position: relative;
          padding: 4px 0;
        }
        .nav-label {
          font-weight: 600;
          font-size: 0.95rem;
          color: var(--text-secondary);
          transition: color 0.3s;
        }
        .nav-indicator {
          position: absolute;
          bottom: -4px; left: 0; width: 0; height: 2px;
          background: var(--accent-primary);
          transition: width 0.3s ease;
        }
        .nav-item:hover .nav-label { color: var(--text-primary); }
        .nav-item:hover .nav-indicator { width: 100%; }

        .btn-get-started {
          display: flex;
          align-items: center;
          gap: 10px;
          background: var(--text-primary);
          color: var(--bg-primary);
          padding: 12px 24px;
          border-radius: 100px;
          font-weight: 700;
          font-size: 0.9rem;
          text-decoration: none;
          transition: all 0.3s;
        }
        .btn-get-started:hover {
          transform: translateY(-2px);
          box-shadow: 0 8px 20px rgba(255, 255, 255, 0.15);
        }

        /* Hero Styling */
        .hero {
          min-height: 100vh;
          max-width: 1400px;
          margin: 0 auto;
          display: flex;
          align-items: center;
          padding: 0 80px;
          gap: 40px;
          position: relative;
          z-index: 1;
        }
        .hero-content { flex: 1.2; max-width: 700px; }
        .hero-title { font-size: 4.5rem; font-weight: 900; line-height: 1.05; margin-bottom: 24px; letter-spacing: -0.04em; }
        .gradient-text {
          background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
        }
        .hero-subtitle { font-size: 1.35rem; color: var(--text-secondary); margin-bottom: 48px; line-height: 1.5; max-width: 600px; }
        
        .cta-group { display: flex; gap: 20px; }
        .btn-hero-primary {
          background: var(--accent-primary);
          color: #000;
          padding: 18px 36px;
          border-radius: 100px;
          font-weight: 800;
          text-decoration: none;
          transition: all 0.3s;
          box-shadow: 0 0 20px rgba(0, 245, 255, 0.2);
        }
        .btn-hero-primary:hover {
          transform: translateY(-2px);
          box-shadow: 0 0 40px rgba(0, 245, 255, 0.4);
        }
        .btn-hero-secondary {
          background: rgba(255, 255, 255, 0.05);
          color: var(--text-primary);
          padding: 18px 36px;
          border-radius: 100px;
          font-weight: 700;
          text-decoration: none;
          border: 1px solid rgba(255, 255, 255, 0.1);
          transition: background 0.3s;
        }
        .btn-hero-secondary:hover { background: rgba(255, 255, 255, 0.1); }

        .image-wrapper { position: relative; }
        .floating-image {
          animation: float 8s ease-in-out infinite;
          filter: drop-shadow(0 0 40px rgba(0, 245, 255, 0.15));
        }
        @keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-30px); } }
        .visual-glow {
          position: absolute;
          top: 50%; left: 50%; transform: translate(-50%, -50%);
          width: 80%; height: 80%; background: radial-gradient(circle, var(--accent-primary) 0%, transparent 70%);
          opacity: 0.1; filter: blur(100px); z-index: -1;
        }

        /* Features Section */
        .features-section { padding: 160px 80px; max-width: 1400px; margin: 0 auto; z-index: 1; position: relative; }
        .section-header { text-align: center; margin-bottom: 100px; }
        .section-title { font-size: 3rem; font-weight: 800; margin-bottom: 20px; letter-spacing: -0.02em; }
        .section-subtitle { color: var(--text-secondary); font-size: 1.25rem; }

        .bento-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 24px; }
        .glass-card {
          background: rgba(255, 255, 255, 0.03);
          border: 1px solid rgba(255, 255, 255, 0.08);
          backdrop-filter: blur(16px);
          padding: 40px; border-radius: 32px;
          transition: all 0.3s;
        }
        .glass-card:hover { border-color: rgba(255, 255, 255, 0.15); transform: translateY(-5px); }
        .card-header-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 32px; }
        .card-header-icon.cyan { background: rgba(0, 245, 255, 0.1); color: var(--accent-primary); }
        .card-header-icon.purple { background: rgba(157, 80, 255, 0.1); color: var(--accent-secondary); }
        .card-header-icon.pink { background: rgba(255, 0, 200, 0.1); color: var(--accent-tertiary); }
        .card-header-icon.blue { background: rgba(0, 100, 255, 0.1); color: #0088ff; }

        .bento-card.large { grid-row: span 2; }
        .bento-card.wide { grid-column: span 2; }
        .bento-card h3 { font-size: 1.5rem; margin-bottom: 20px; }
        .bento-card p { color: var(--text-secondary); font-size: 1rem; line-height: 1.6; }

        .card-animation-crawling {
          height: 140px; background: rgba(0,0,0,0.2); border-radius: 16px; margin-top: 32px;
          position: relative; overflow: hidden;
        }
        .scan-bar { position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--accent-primary); box-shadow: 0 0 15px var(--accent-primary); animation: scan 4s linear infinite; }
        @keyframes scan { 0% { top: 0% } 100% { top: 100% } }
        .grid-overlay { position: absolute; inset: 0; background-image: radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px); background-size: 20px 20px; }

        .showcase { display: flex; flex-direction: row !important; gap: 40px; align-items: center; }
        .showcase-info { flex: 1; }
        .mini-features { list-style: none; margin-top: 32px; display: flex; flex-direction: column; gap: 16px; }
        .mini-features li { display: flex; align-items: center; gap: 12px; font-size: 0.95rem; color: var(--text-secondary); }
        .cyan-text { color: var(--accent-primary); }

        .canvas-mockup { flex: 1.5; background: #05081a; border-radius: 20px 20px 0 0; border: 1px solid rgba(255,255,255,0.1); overflow: hidden; display: flex; flex-direction: column; height: 260px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); }
        .mockup-chrome { padding: 12px 20px; background: rgba(255,255,255,0.02); display: flex; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.05); }
        .chrome-dots { display: flex; gap: 6px; flex: 1; }
        .chrome-dots span { width: 8px; height: 8px; border-radius: 50%; opacity: 0.4; }
        .r { background: #ff5f56; } .y { background: #ffbd2e; } .g { background: #27c93f; }
        .chrome-tab { font-size: 0.75rem; color: var(--text-muted); background: rgba(255,255,255,0.05); padding: 4px 12px; border-radius: 4px; }
        
        .mockup-content { flex: 1; padding: 20px; display: flex; gap: 20px; position: relative; }
        .mock-sidebar { width: 40px; background: rgba(255,255,255,0.02); border-radius: 6px; }
        .mock-workspace { flex: 1; position: relative; background-image: radial-gradient(rgba(255,255,255,0.05) 1px, transparent 1px); background-size: 20px 20px; }
        .mock-node { position: absolute; padding: 6px 14px; border-radius: 6px; font-size: 0.7rem; font-weight: 700; white-space: nowrap; }
        .mock-node.active { background: rgba(0, 245, 255, 0.1); border: 1px solid var(--accent-primary); color: var(--accent-primary); top: 20%; left: 15%; }
        .mock-node.secondary { background: rgba(157, 80, 255, 0.1); border: 1px solid var(--accent-secondary); color: var(--accent-secondary); bottom: 30%; right: 15%; }

        /* Team Section */
        .team-section { padding: 100px 80px; max-width: 1400px; margin: 0 auto; position: relative; z-index: 1; }
        .team-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; }
        .member-card { padding: 40px 32px; text-align: center; }
        .avatar-wrapper { width: 100px; height: 100px; margin: 0 auto 24px; border-radius: 50%; overflow: hidden; border: 2px solid var(--glass-border); position: relative; }
        .member-avatar { object-fit: cover; filter: grayscale(1); transition: filter 0.4s; }
        .member-card:hover .member-avatar { filter: grayscale(0); }
        .member-role { color: var(--accent-primary); font-size: 0.85rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; margin: 8px 0 20px; }
        .member-bio { font-size: 0.95rem; color: var(--text-secondary); line-height: 1.5; margin-bottom: 24px; }
        .member-social { display: flex; justify-content: center; gap: 16px; color: var(--text-muted); cursor: pointer; }
        .member-social :global(svg):hover { color: var(--text-primary); }

        /* CTA Section */
        .cta-section { padding: 120px 80px; position: relative; z-index: 1; }
        .cta-card {
          max-width: 1100px; margin: 0 auto; padding: 100px 80px; text-align: center;
          display: flex; flex-direction: column; align-items: center; gap: 32px;
        }
        .cta-card h2 { font-size: 3.5rem; font-weight: 800; letter-spacing: -0.03em; }
        .cta-card p { font-size: 1.35rem; color: var(--text-secondary); max-width: 600px; margin: 0 auto; }
        .btn-cta {
          background: var(--text-primary); color: var(--bg-primary); padding: 20px 48px;
          border-radius: 100px; font-weight: 800; font-size: 1.1rem; text-decoration: none;
          transition: all 0.3s;
        }
        .btn-cta:hover { transform: scale(1.05); box-shadow: 0 0 50px rgba(255, 255, 255, 0.2); }
        .accent-glow { position: relative; overflow: visible; }
        .accent-glow::after {
          content: ''; position: absolute; inset: -1px; border-radius: 32px; padding: 1px;
          background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
          -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite: xor; mask-composite: exclude;
          pointer-events: none; opacity: 0.5;
        }

        /* Footer */
        .footer-site { padding: 120px 80px 60px; background: rgba(0,0,0,0.2); border-top: 1px solid rgba(255,255,255,0.05); position: relative; z-index: 1; }
        .footer-main { max-width: 1200px; margin: 0 auto; display: flex; justify-content: space-between; gap: 80px; margin-bottom: 100px; }
        .footer-info { max-width: 300px; }
        .footer-desc { margin: 24px 0; color: var(--text-secondary); line-height: 1.6; }
        .footer-social { display: flex; gap: 20px; color: var(--text-muted); cursor: pointer; }
        .footer-social :global(svg):hover { color: var(--accent-primary); }
        .footer-links { display: flex; gap: 80px; }
        .footer-group h4 { margin-bottom: 32px; font-size: 1rem; font-weight: 700; color: var(--text-primary); }
        .footer-group a { display: block; margin-bottom: 20px; color: var(--text-secondary); text-decoration: none; font-size: 0.95rem; transition: color 0.3s; }
        .footer-group a:hover { color: var(--accent-primary); }
        .footer-bottom { border-top: 1px solid rgba(255,255,255,0.05); padding-top: 40px; text-align: center; color: var(--text-muted); font-size: 0.9rem; }

        @media (max-width: 1200px) {
          .hero-title { font-size: 3.5rem; }
          .hero { flex-direction: column; text-align: center; padding-top: 160px; }
          .hero-content { align-items: center; }
          .cta-group { justify-content: center; }
          .features-section, .team-section, .cta-section { padding: 80px 40px; }
          .bento-grid, .team-grid { grid-template-columns: repeat(2, 1fr); }
          .bento-card.wide { grid-column: span 2; }
          .footer-main { flex-direction: column; gap: 60px; }
          .footer-links { gap: 40px; flex-wrap: wrap; }
        }

        @media (max-width: 768px) {
          .navbar-wrapper { top: 16px; padding: 0 16px; }
          .floating-island { gap: 20px; padding: 8px 8px 8px 20px; }
          .nav-main-links { display: none; }
          .logo-text { font-size: 0.9rem; }
          .hero-title { font-size: 2.5rem; }
          .bento-grid, .team-grid { grid-template-columns: 1fr; }
          .bento-card.wide { grid-column: span 1; }
          .showcase { flex-direction: column !important; }
          .cta-card h2 { font-size: 2rem; }
        }
      `}</style>
    </div>
  );
}
