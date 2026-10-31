import React, { useState } from 'react';
import { api } from '../api';

export default function DemoBar({ currentUser, onUserChange, onRefresh }) {
  const [running, setRunning] = useState(false);
  const [statusMsg, setStatusMsg] = useState('');

  const handleRoleSwitch = async (email, password) => {
    try {
      setRunning(true);
      setStatusMsg(`Switching account to ${email}...`);
      const res = await api.login(email, password);
      onUserChange(res.user);
      setStatusMsg(`Active user: ${res.user.email} (${res.user.role})`);
      if (onRefresh) onRefresh();
    } catch (err) {
      setStatusMsg(`Failed to switch: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleRunBilling = async () => {
    try {
      setRunning(true);
      setStatusMsg('Running batch billing...');
      const res = await api.runBilling();
      setStatusMsg(res.message);
      if (onRefresh) onRefresh();
    } catch (err) {
      setStatusMsg(`Billing error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleRunDetection = async () => {
    try {
      setRunning(true);
      setStatusMsg('Running Proof Engine detection...');
      const res = await api.runDetection();
      setStatusMsg(res.message);
      if (onRefresh) onRefresh();
    } catch (err) {
      setStatusMsg(`Detection error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  const handleLeakInjection = async () => {
    try {
      setRunning(true);
      setStatusMsg('Injecting synthetic billing leaks for demo...');
      const res = await api.injectLeaks();
      setStatusMsg(res.message);
      if (onRefresh) onRefresh();
    } catch (err) {
      setStatusMsg(`Injection error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div style={{
      backgroundColor: '#1e2124',
      color: '#ffffff',
      padding: '8px 24px',
      fontSize: '12px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '12px',
      borderBottom: '1px solid #32363a'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <span style={{ fontWeight: 600, color: '#a0a6ad', textTransform: 'uppercase', letterSpacing: '0.04em' }}>Demo Controls:</span>
        <button
          className="btn btn-secondary btn-sm"
          disabled={running}
          style={{ backgroundColor: '#2b2f33', color: '#ffffff', borderColor: '#40454a' }}
          onClick={() => handleRoleSwitch('admin@proofbill.io', 'AdminPass123!')}
        >
          Admin (admin@proofbill.io)
        </button>
        <button
          className="btn btn-secondary btn-sm"
          disabled={running}
          style={{ backgroundColor: '#2b2f33', color: '#ffffff', borderColor: '#40454a' }}
          onClick={() => handleRoleSwitch('staff@proofbill.io', 'StaffPass123!')}
        >
          Staff (staff@proofbill.io)
        </button>
        <button
          className="btn btn-secondary btn-sm"
          disabled={running}
          style={{ backgroundColor: '#2b2f33', color: '#ffffff', borderColor: '#40454a' }}
          onClick={() => handleRoleSwitch('billing@acme.com', 'CustomerPass123!')}
        >
          Customer (billing@acme.com)
        </button>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
        <button
          className="btn btn-secondary btn-sm"
          disabled={running}
          style={{ backgroundColor: '#ffffff', color: '#1e2124' }}
          onClick={handleRunBilling}
        >
          Run Billing
        </button>
        <button
          className="btn btn-secondary btn-sm"
          disabled={running}
          style={{ backgroundColor: '#ffffff', color: '#1e2124' }}
          onClick={handleRunDetection}
        >
          Run Detection
        </button>
        <button
          className="btn btn-secondary btn-sm"
          disabled={running}
          style={{ backgroundColor: '#b3261e', color: '#ffffff', borderColor: '#b3261e' }}
          onClick={handleLeakInjection}
          title="Inject synthetic skipped, duplicate, and mispriced invoices to test Proof Engine"
        >
          Inject Leaks
        </button>
        {statusMsg && (
          <span style={{ color: '#d9dbdd', marginLeft: '6px', fontStyle: 'italic' }}>
            {statusMsg}
          </span>
        )}
      </div>
    </div>
  );
}
