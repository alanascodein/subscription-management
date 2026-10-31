import React from 'react';

export default function Header({ activeTab, onTabChange, currentUser, onLogout, openAlertsCount = 0 }) {
  const isCustomer = currentUser?.role === 'customer';

  return (
    <header style={{
      backgroundColor: '#ffffff',
      borderBottom: '1px solid var(--color-border)',
      padding: '0 24px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      height: '56px',
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.02em', color: 'var(--color-text-primary)' }}>
            ProofBill
          </span>
          <span style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: 500 }}>
            Audit-First Billing
          </span>
        </div>

        <nav style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          {!isCustomer ? (
            <>
              <button
                className={`btn btn-sm ${activeTab === 'dashboard' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ border: 'none', background: activeTab === 'dashboard' ? 'var(--color-text-primary)' : 'transparent' }}
                onClick={() => onTabChange('dashboard')}
              >
                Dashboard
              </button>
              <button
                className={`btn btn-sm ${activeTab === 'alerts' ? 'btn-primary' : 'btn-secondary'}`}
                style={{
                  border: 'none',
                  background: activeTab === 'alerts' ? 'var(--color-text-primary)' : 'transparent',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
                onClick={() => onTabChange('alerts')}
              >
                <span>Proof Engine</span>
                {openAlertsCount > 0 && (
                  <span style={{
                    backgroundColor: activeTab === 'alerts' ? '#ffffff' : 'var(--color-danger)',
                    color: activeTab === 'alerts' ? '#1e2124' : '#ffffff',
                    fontSize: '10px',
                    fontWeight: 700,
                    padding: '1px 5px',
                    borderRadius: '10px'
                  }}>
                    {openAlertsCount}
                  </span>
                )}
              </button>
              <button
                className={`btn btn-sm ${activeTab === 'subscriptions' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ border: 'none', background: activeTab === 'subscriptions' ? 'var(--color-text-primary)' : 'transparent' }}
                onClick={() => onTabChange('subscriptions')}
              >
                Subscriptions
              </button>
              <button
                className={`btn btn-sm ${activeTab === 'invoices' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ border: 'none', background: activeTab === 'invoices' ? 'var(--color-text-primary)' : 'transparent' }}
                onClick={() => onTabChange('invoices')}
              >
                Invoices
              </button>
              <button
                className={`btn btn-sm ${activeTab === 'customers' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ border: 'none', background: activeTab === 'customers' ? 'var(--color-text-primary)' : 'transparent' }}
                onClick={() => onTabChange('customers')}
              >
                Customers
              </button>
              <button
                className={`btn btn-sm ${activeTab === 'catalogue' ? 'btn-primary' : 'btn-secondary'}`}
                style={{ border: 'none', background: activeTab === 'catalogue' ? 'var(--color-text-primary)' : 'transparent' }}
                onClick={() => onTabChange('catalogue')}
              >
                Catalogue
              </button>
            </>
          ) : null}

          <button
            className={`btn btn-sm ${activeTab === 'portal' ? 'btn-primary' : 'btn-secondary'}`}
            style={{ border: 'none', background: activeTab === 'portal' ? 'var(--color-text-primary)' : 'transparent' }}
            onClick={() => onTabChange('portal')}
          >
            Customer Portal
          </button>
        </nav>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        {currentUser ? (
          <>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '12px', fontWeight: 500 }}>{currentUser.email}</div>
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2px' }}>
                <span className={`badge ${currentUser.role === 'admin' ? 'badge-danger' : currentUser.role === 'staff' ? 'badge-warning' : 'badge-neutral'}`}>
                  {currentUser.role}
                </span>
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={onLogout}>
              Sign out
            </button>
          </>
        ) : (
          <button className="btn btn-primary btn-sm" onClick={() => onTabChange('auth')}>
            Sign in
          </button>
        )}
      </div>
    </header>
  );
}
