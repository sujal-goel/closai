'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function SignupPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [organization, setOrganization] = useState('');
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSignup = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || '';
      
      const res = await fetch(`${API_BASE}/api/auth/signup`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, organization }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Signup failed. Please try again.');
      }

      const data = await res.json();
      // Store token
      localStorage.setItem('cc_token', data.access_token);
      
      // Redirect to protected workspace
      router.push('/workspace');
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card glass">
        <Link href="/" className="back-link">← Back to home</Link>
        <div className="auth-header">
          <h2>Create Account</h2>
          <p>Join to access the Principal Architect engine.</p>
        </div>

        {error && <div className="error-box">{error}</div>}

        <form onSubmit={handleSignup} className="auth-form">
          <div className="input-group">
            <label>Full Name</label>
            <input 
              type="text" 
              required 
              placeholder="Jane Doe"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label>Work Email</label>
            <input 
              type="email" 
              required 
              placeholder="engineer@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          
          <div className="input-group">
            <label>Password</label>
            <input 
              type="password" 
              required 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <div className="input-group">
            <label>Organization (Optional)</label>
            <input 
              type="text" 
              placeholder="Acme Corp"
              value={organization}
              onChange={(e) => setOrganization(e.target.value)}
            />
          </div>

          <button type="submit" className="submit-btn" disabled={isLoading}>
            {isLoading ? 'Creating Account...' : 'Get Started →'}
          </button>
        </form>

        <p className="auth-footer">
          Already have an account? <Link href="/login">Sign in.</Link>
        </p>
      </div>

      <style jsx>{`
        .auth-container {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: var(--bg-primary);
          position: relative;
        }

        .auth-container::before {
          content: "";
          position: absolute;
          width: 500px;
          height: 500px;
          background: radial-gradient(circle, var(--accent-primary) 0%, transparent 70%);
          opacity: 0.1;
          top: 50%; left: 50%;
          transform: translate(-50%, -50%);
          pointer-events: none;
        }

        .auth-card {
          width: 100%;
          max-width: 440px;
          padding: 40px;
          border-radius: var(--radius-soft);
          box-shadow: var(--shadow-electric);
          position: relative;
          z-index: 10;
        }

        .back-link {
          position: absolute;
          top: 24px;
          left: 24px;
          font-size: 11px;
          color: var(--text-muted);
          text-decoration: none;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          font-weight: 700;
          transition: color 0.2s;
        }
        .back-link:hover { color: var(--text-primary); }

        .auth-header { margin-bottom: 32px; margin-top: 16px; }
        .auth-header h2 { font-size: 28px; font-weight: 800; margin-bottom: 8px; }
        .auth-header p { color: var(--text-secondary); font-size: 14px; }

        .error-box {
          background: rgba(255, 68, 68, 0.1);
          border: 1px solid rgba(255, 68, 68, 0.3);
          color: #ff4444;
          padding: 12px 16px;
          border-radius: var(--radius-precise);
          font-size: 12px;
          margin-bottom: 24px;
        }

        .auth-form { display: flex; flex-direction: column; gap: 20px; }

        .input-group { display: flex; flex-direction: column; gap: 8px; }
        .input-group label {
          font-size: 11px;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          font-weight: 700;
          color: var(--text-secondary);
        }
        .input-group input {
          background: rgba(0, 0, 0, 0.2);
          border: 1px solid var(--border-muted);
          padding: 14px 16px;
          border-radius: var(--radius-precise);
          color: var(--text-primary);
          font-family: inherit;
          font-size: 14px;
          outline: none;
          transition: all 0.3s;
        }
        .input-group input:focus {
          border-color: var(--accent-primary);
          box-shadow: 0 0 10px rgba(0, 245, 255, 0.1);
        }

        .submit-btn {
          margin-top: 12px;
          background: var(--accent-primary);
          color: #000;
          font-weight: 800;
          font-size: 14px;
          padding: 16px;
          border-radius: var(--radius-precise);
          border: none;
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .submit-btn:hover:not(:disabled) {
          transform: translateY(-1px);
          box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
        }
        .submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }

        .auth-footer {
          margin-top: 24px;
          text-align: center;
          font-size: 13px;
          color: var(--text-secondary);
        }
        .auth-footer a {
          color: var(--accent-primary);
          text-decoration: none;
          font-weight: 600;
        }
        .auth-footer a:hover { text-decoration: underline; }
      `}</style>
    </div>
  );
}
