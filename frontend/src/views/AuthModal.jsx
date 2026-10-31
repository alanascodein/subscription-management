import React, { useState } from 'react';
import { api } from '../api';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // Login form
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Register form
  const [regData, setRegData] = useState({
    name: '',
    email: '',
    company_name: '',
    phone: '',
    billing_address: '',
    password: '',
    confirm_password: '',
  });

  if (!isOpen) return null;

  const handleLogin = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setErrorMsg('');
      const res = await api.login(email, password);
      onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (regData.password !== regData.confirm_password) {
      setErrorMsg("Passwords do not match.");
      return;
    }

    try {
      setLoading(true);
      setErrorMsg('');
      const res = await api.register(regData);
      onAuthSuccess(res.user);
      onClose();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fillPreset = (em, pw) => {
    setEmail(em);
    setPassword(pw);
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-dialog" style={{ maxWidth: '440px' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>
            {isRegister ? 'Register Customer Account' : 'Sign in to ProofBill'}
          </h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer' }}>
            &times;
          </button>
        </div>

        <div style={{ padding: '20px 24px' }}>
          {errorMsg && (
            <div className="banner-alert error" style={{ marginBottom: '16px' }}>
              <span>{errorMsg}</span>
            </div>
          )}

          {!isRegister ? (
            <form onSubmit={handleLogin}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Email Address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Password
                </label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Password"
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginBottom: '16px' }} disabled={loading}>
                {loading ? 'Signing in...' : 'Sign in'}
              </button>

              <div style={{ fontSize: '12px', textAlign: 'center', marginBottom: '16px' }}>
                Don't have an account?{' '}
                <a onClick={() => { setIsRegister(true); setErrorMsg(''); }}>
                  Register as Customer
                </a>
              </div>

              {/* Demo Credentials Helper */}
              <div style={{
                backgroundColor: 'var(--color-surface-muted)',
                border: '1px solid var(--color-border)',
                borderRadius: '4px',
                padding: '12px',
                fontSize: '12px',
              }}>
                <div style={{ fontWeight: 600, marginBottom: '6px', color: 'var(--color-text-secondary)' }}>
                  Quick Demo Accounts:
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <a style={{ textDecoration: 'none', color: 'inherit' }} onClick={() => fillPreset('admin@proofbill.io', 'AdminPass123!')}>
                    &bull; <strong>Admin:</strong> <code>admin@proofbill.io</code> / <code>AdminPass123!</code>
                  </a>
                  <a style={{ textDecoration: 'none', color: 'inherit' }} onClick={() => fillPreset('staff@proofbill.io', 'StaffPass123!')}>
                    &bull; <strong>Staff:</strong> <code>staff@proofbill.io</code> / <code>StaffPass123!</code>
                  </a>
                  <a style={{ textDecoration: 'none', color: 'inherit' }} onClick={() => fillPreset('billing@acme.com', 'CustomerPass123!')}>
                    &bull; <strong>Customer:</strong> <code>billing@acme.com</code> / <code>CustomerPass123!</code>
                  </a>
                </div>
              </div>
            </form>
          ) : (
            <form onSubmit={handleRegister}>
              <div style={{ marginBottom: '12px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Full Name *
                </label>
                <input
                  type="text"
                  placeholder="Jane Doe"
                  value={regData.name}
                  onChange={(e) => setRegData({ ...regData, name: e.target.value })}
                  required
                />
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Email Address *
                </label>
                <input
                  type="email"
                  placeholder="jane@acme.com"
                  value={regData.email}
                  onChange={(e) => setRegData({ ...regData, email: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Company
                  </label>
                  <input
                    type="text"
                    placeholder="Acme Corp"
                    value={regData.company_name}
                    onChange={(e) => setRegData({ ...regData, company_name: e.target.value })}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Phone
                  </label>
                  <input
                    type="text"
                    placeholder="+91..."
                    value={regData.phone}
                    onChange={(e) => setRegData({ ...regData, phone: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ marginBottom: '12px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Password * (Min 9 chars, upper, lower, special)
                </label>
                <input
                  type="password"
                  value={regData.password}
                  onChange={(e) => setRegData({ ...regData, password: e.target.value })}
                  required
                />
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                  Confirm Password *
                </label>
                <input
                  type="password"
                  value={regData.confirm_password}
                  onChange={(e) => setRegData({ ...regData, confirm_password: e.target.value })}
                  required
                />
              </div>

              <button type="submit" className="btn btn-primary" style={{ width: '100%', marginBottom: '16px' }} disabled={loading}>
                {loading ? 'Creating account...' : 'Register Account'}
              </button>

              <div style={{ fontSize: '12px', textAlign: 'center' }}>
                Already have an account?{' '}
                <a onClick={() => { setIsRegister(false); setErrorMsg(''); }}>
                  Sign in
                </a>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
