import React, { useState, useEffect } from 'react';
import { api, formatMoney, formatDate } from '../api';

export default function CustomerPortalView({ currentUser, onPayInvoice }) {
  const [portalData, setPortalData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notification, setNotification] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  const fetchPortalData = async () => {
    try {
      setLoading(true);
      const res = await api.getPortalData();
      setPortalData(res.data);
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortalData();
  }, [currentUser]);

  const handleCancelSub = async (uuid) => {
    if (!window.confirm("Are you sure you want to request cancellation of this subscription?")) return;
    try {
      setActionLoading(true);
      const res = await api.transitionSubscription(uuid, 'close', 'Customer requested cancellation via portal');
      setNotification({ type: 'success', message: res.message });
      fetchPortalData();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleRenewSub = async (uuid) => {
    try {
      setActionLoading(true);
      const res = await api.transitionSubscription(uuid, 'renew', 'Renewed via customer portal');
      setNotification({ type: 'success', message: res.message });
      fetchPortalData();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        Loading customer portal...
      </div>
    );
  }

  const customer = portalData?.customer;

  return (
    <div style={{ padding: '24px', maxWidth: '1080px', margin: '0 auto' }}>
      {notification && (
        <div className={`banner-alert ${notification.type}`}>
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)} style={{ background: 'none', border: 'none', color: 'inherit' }}>
            &times;
          </button>
        </div>
      )}

      {/* Profile Header */}
      <div className="surface" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <span className="badge badge-neutral" style={{ marginBottom: '6px' }}>Subscriber Account</span>
            <h2 style={{ fontSize: '20px', fontWeight: 600 }}>{customer?.name || 'Customer Account'}</h2>
            <div style={{ fontSize: '13px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              {customer?.company_name} &bull; {customer?.email}
            </div>
            {customer?.billing_address && (
              <div style={{ fontSize: '12px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
                {customer.billing_address}
              </div>
            )}
          </div>

          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>
              Active Subscriptions
            </div>
            <div style={{ fontSize: '20px', fontWeight: 700 }}>
              {portalData?.subscriptions?.filter((s) => s.status === 'active').length || 0}
            </div>
          </div>
        </div>
      </div>

      {/* Active Subscriptions Section */}
      <div className="surface" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>Your Subscriptions</h3>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Plan Name</th>
                <th>Cycle</th>
                <th>Status</th>
                <th>Next Billing Date</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {portalData?.subscriptions?.length > 0 ? (
                portalData.subscriptions.map((s) => (
                  <tr key={s.uuid}>
                    <td><strong>{s.plan_name}</strong></td>
                    <td><span className="badge badge-neutral">{s.cycle_display}</span></td>
                    <td>
                      <span className={`badge ${s.status === 'active' ? 'badge-success' : s.status === 'paused' ? 'badge-warning' : 'badge-neutral'}`}>
                        {s.status_display}
                      </span>
                    </td>
                    <td>{formatDate(s.next_billing_date)}</td>
                    <td>
                      <div style={{ display: 'flex', gap: '6px' }}>
                        {s.can_cancel && (
                          <button
                            className="btn btn-secondary btn-sm"
                            disabled={actionLoading}
                            style={{ color: 'var(--color-danger)' }}
                            onClick={() => handleCancelSub(s.uuid)}
                          >
                            Cancel
                          </button>
                        )}
                        {s.can_renew && s.status === 'closed' && (
                          <button
                            className="btn btn-primary btn-sm"
                            disabled={actionLoading}
                            onClick={() => handleRenewSub(s.uuid)}
                          >
                            Renew
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '24px', color: 'var(--color-text-secondary)' }}>
                    No subscriptions currently active under this account.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Invoices & Statements */}
      <div className="surface" style={{ marginBottom: '24px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>Invoices & Balances</h3>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Issue Date</th>
                <th>Due Date</th>
                <th className="money">Total</th>
                <th className="money">Balance Due</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {portalData?.invoices?.length > 0 ? (
                portalData.invoices.map((inv) => (
                  <tr key={inv.uuid}>
                    <td><code>{inv.invoice_number}</code></td>
                    <td>{formatDate(inv.issue_date)}</td>
                    <td>{formatDate(inv.due_date)}</td>
                    <td className="money">{formatMoney(inv.total)}</td>
                    <td className="money" style={{ color: parseFloat(inv.balance_due) > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>
                      {formatMoney(inv.balance_due)}
                    </td>
                    <td>
                      <span className={`badge ${inv.status === 'paid' ? 'badge-success' : inv.status === 'confirmed' ? (inv.is_overdue ? 'badge-danger' : 'badge-warning') : 'badge-neutral'}`}>
                        {inv.is_overdue ? 'overdue' : inv.status_display}
                      </span>
                    </td>
                    <td>
                      {inv.status === 'confirmed' && parseFloat(inv.balance_due) > 0 ? (
                        <button
                          className="btn btn-primary btn-sm"
                          onClick={() => onPayInvoice(inv)}
                        >
                          Pay Online
                        </button>
                      ) : (
                        <span style={{ fontSize: '12px', color: 'var(--color-text-muted)' }}>Settled</span>
                      )}
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: '24px', color: 'var(--color-text-secondary)' }}>
                    No invoices generated yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Payment Receipts History */}
      <div className="surface">
        <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '14px' }}>Payment History</h3>
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Payment Date</th>
                <th>Invoice Reference</th>
                <th>Method</th>
                <th>Transaction Ref</th>
                <th className="money">Amount</th>
              </tr>
            </thead>
            <tbody>
              {portalData?.payments?.length > 0 ? (
                portalData.payments.map((p) => (
                  <tr key={p.uuid}>
                    <td>{formatDate(p.date)}</td>
                    <td><code>{p.invoice_number}</code></td>
                    <td>{p.method}</td>
                    <td><code>{p.reference || '—'}</code></td>
                    <td className="money" style={{ color: 'var(--color-success)' }}>{formatMoney(p.amount)}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: '20px', color: 'var(--color-text-secondary)' }}>
                    No recorded payments on this account.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
