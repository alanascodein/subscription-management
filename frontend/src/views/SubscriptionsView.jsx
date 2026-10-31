import React, { useState, useEffect } from 'react';
import { api, formatMoney, formatDate } from '../api';

export default function SubscriptionsView() {
  const [subscriptions, setSubscriptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedSub, setSelectedSub] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [catalogue, setCatalogue] = useState(null);
  const [customers, setCustomers] = useState([]);
  const [transitionReason, setTransitionReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // New Subscription Form State
  const [formData, setFormData] = useState({
    customer_uuid: '',
    plan_id: '',
    start_date: new Date().toISOString().split('T')[0],
    tax_rule_id: '',
    discount_id: '',
    items: [{ product_id: '', variant_id: '', quantity: 1 }],
  });

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      const res = await api.getSubscriptions(statusFilter);
      setSubscriptions(res.data || []);
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const fetchPrerequisites = async () => {
    try {
      const [catRes, custRes] = await Promise.all([
        api.getCatalogue(),
        api.getCustomers(),
      ]);
      setCatalogue(catRes.data);
      setCustomers(custRes.data || []);
      if (custRes.data?.length > 0) {
        setFormData((prev) => ({ ...prev, customer_uuid: custRes.data[0].uuid }));
      }
      if (catRes.data?.plans?.length > 0) {
        setFormData((prev) => ({ ...prev, plan_id: catRes.data.plans[0].id }));
      }
      if (catRes.data?.products?.length > 0) {
        setFormData((prev) => ({
          ...prev,
          items: [{ product_id: catRes.data.products[0].id, variant_id: '', quantity: 1 }],
        }));
      }
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchSubscriptions();
  }, [statusFilter]);

  useEffect(() => {
    fetchPrerequisites();
  }, []);

  const handleOpenDetail = async (uuid) => {
    try {
      setActionLoading(true);
      const res = await api.getSubscription(uuid);
      setSelectedSub(res.data);
      setTransitionReason('');
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleTransition = async (action) => {
    if (!selectedSub) return;
    try {
      setActionLoading(true);
      const res = await api.transitionSubscription(selectedSub.uuid, action, transitionReason);
      setNotification({ type: 'success', message: res.message });
      const updated = await api.getSubscription(selectedSub.uuid);
      setSelectedSub(updated.data);
      setTransitionReason('');
      fetchSubscriptions();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateSubscription = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      const res = await api.createSubscription(formData);
      setNotification({ type: 'success', message: res.message });
      setShowCreateModal(false);
      fetchSubscriptions();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'active':
        return 'badge-success';
      case 'paused':
      case 'quotation':
        return 'badge-warning';
      case 'closed':
        return 'badge-danger';
      default:
        return 'badge-neutral';
    }
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1280px', margin: '0 auto' }}>
      {notification && (
        <div className={`banner-alert ${notification.type}`}>
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)} style={{ background: 'none', border: 'none', color: 'inherit' }}>
            &times;
          </button>
        </div>
      )}

      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 600 }}>Subscriptions Management</h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginTop: '2px' }}>
            Strict state machine lifecycle with automated period tracking and event auditing.
          </p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowCreateModal(true)}>
          Create Subscription
        </button>
      </div>

      {/* Filter Tabs */}
      <div style={{ display: 'flex', gap: '6px', marginBottom: '16px', flexWrap: 'wrap' }}>
        {['', 'active', 'quotation', 'draft', 'paused', 'closed'].map((st) => (
          <button
            key={st}
            className={`btn btn-sm ${statusFilter === st ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter(st)}
          >
            {st ? st.charAt(0).toUpperCase() + st.slice(1) : 'All Subscriptions'}
          </button>
        ))}
      </div>

      {/* Subscriptions Table */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Customer</th>
              <th>Plan</th>
              <th>Billing Cycle</th>
              <th>Start Date</th>
              <th>Next Billing</th>
              <th className="money">Est. Period Total</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  Loading subscriptions...
                </td>
              </tr>
            ) : subscriptions.length > 0 ? (
              subscriptions.map((s) => (
                <tr key={s.uuid}>
                  <td><strong>#{s.id}</strong></td>
                  <td>
                    <div><strong>{s.customer.name}</strong></div>
                    {s.customer.company_name && (
                      <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)' }}>{s.customer.company_name}</div>
                    )}
                  </td>
                  <td>{s.plan.name}</td>
                  <td><span className="badge badge-neutral">{s.plan.cycle_display}</span></td>
                  <td>{formatDate(s.start_date)}</td>
                  <td>{formatDate(s.next_billing_date)}</td>
                  <td className="money">{formatMoney(s.estimated_period_total)}</td>
                  <td>
                    <span className={`badge ${getStatusBadge(s.status)}`}>
                      {s.status_display}
                    </span>
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => handleOpenDetail(s.uuid)}>
                      Inspect
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  No subscriptions found matching this filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Subscription Detail & Lifecycle Modal */}
      {selectedSub && (
        <div className="modal-backdrop" onClick={() => setSelectedSub(null)}>
          <div className="modal-dialog" style={{ maxWidth: '720px' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span className={`badge ${getStatusBadge(selectedSub.status)}`} style={{ marginRight: '8px' }}>
                  {selectedSub.status_display}
                </span>
                <span style={{ fontSize: '16px', fontWeight: 600 }}>Subscription #{selectedSub.id}</span>
              </div>
              <button onClick={() => setSelectedSub(null)} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer' }}>
                &times;
              </button>
            </div>

            <div style={{ padding: '20px 24px' }}>
              {/* Customer and Plan Info */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Customer</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>{selectedSub.customer.name}</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{selectedSub.customer.email}</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Plan & Frequency</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>{selectedSub.plan.name}</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>{selectedSub.plan.cycle_display} (Grace: {selectedSub.plan.grace_days}d)</div>
                </div>
                <div>
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Next Billing</div>
                  <div style={{ fontSize: '14px', fontWeight: 600 }}>{formatDate(selectedSub.next_billing_date)}</div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Started: {formatDate(selectedSub.start_date)}</div>
                </div>
              </div>

              {/* Items Table */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Contracted Plan Items</h4>
                <table className="data-table" style={{ border: '1px solid var(--color-border)' }}>
                  <thead>
                    <tr>
                      <th>Product</th>
                      <th>Variant</th>
                      <th>Qty</th>
                      <th className="money">Unit Price</th>
                      <th className="money">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedSub.items?.map((it) => (
                      <tr key={it.id}>
                        <td>{it.product_name}</td>
                        <td>{it.variant_name || 'Standard'}</td>
                        <td>{it.quantity}</td>
                        <td className="money">{formatMoney(it.unit_price)}</td>
                        <td className="money">{formatMoney(it.line_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Lifecycle Actions */}
              <div style={{
                backgroundColor: 'var(--color-surface-muted)',
                border: '1px solid var(--color-border)',
                borderRadius: '4px',
                padding: '16px',
                marginBottom: '20px',
              }}>
                <div style={{ fontSize: '12px', fontWeight: 600, marginBottom: '8px' }}>
                  Lifecycle State Machine Actions:
                </div>

                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '12px' }}>
                  {selectedSub.status === 'draft' && (
                    <>
                      <button className="btn btn-secondary btn-sm" disabled={actionLoading} onClick={() => handleTransition('send_quotation')}>
                        Send Quotation
                      </button>
                      <button className="btn btn-primary btn-sm" disabled={actionLoading} onClick={() => handleTransition('confirm')}>
                        Confirm Subscription
                      </button>
                    </>
                  )}

                  {selectedSub.status === 'quotation' && (
                    <button className="btn btn-primary btn-sm" disabled={actionLoading} onClick={() => handleTransition('confirm_quotation')}>
                      Accept Quotation
                    </button>
                  )}

                  {selectedSub.status === 'confirmed' && (
                    <button className="btn btn-primary btn-sm" disabled={actionLoading} onClick={() => handleTransition('activate')}>
                      Activate Billing
                    </button>
                  )}

                  {selectedSub.status === 'active' && (
                    <>
                      {selectedSub.plan.pause_allowed && (
                        <button className="btn btn-secondary btn-sm" disabled={actionLoading} onClick={() => handleTransition('pause')}>
                          Pause Subscription
                        </button>
                      )}
                      {selectedSub.plan.early_close_allowed && (
                        <button className="btn btn-danger btn-sm" disabled={actionLoading} onClick={() => handleTransition('close')}>
                          Close Subscription
                        </button>
                      )}
                    </>
                  )}

                  {selectedSub.status === 'paused' && (
                    <>
                      <button className="btn btn-primary btn-sm" disabled={actionLoading} onClick={() => handleTransition('resume')}>
                        Resume Subscription
                      </button>
                      <button className="btn btn-danger btn-sm" disabled={actionLoading} onClick={() => handleTransition('close')}>
                        Close Subscription
                      </button>
                    </>
                  )}

                  {selectedSub.status === 'closed' && selectedSub.plan.renewal_allowed && (
                    <button className="btn btn-primary btn-sm" disabled={actionLoading} onClick={() => handleTransition('renew')}>
                      Renew Subscription
                    </button>
                  )}
                </div>

                <input
                  type="text"
                  placeholder="Reason for lifecycle transition (recorded in audit event history)..."
                  value={transitionReason}
                  onChange={(e) => setTransitionReason(e.target.value)}
                  style={{ width: '100%', fontSize: '12px' }}
                />
              </div>

              {/* Event Audit History */}
              <div>
                <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Audit Event History</h4>
                <div style={{ maxHeight: '160px', overflowY: 'auto', border: '1px solid var(--color-border)', borderRadius: '4px' }}>
                  <table className="data-table" style={{ fontSize: '12px' }}>
                    <thead>
                      <tr>
                        <th>Time</th>
                        <th>Transition</th>
                        <th>Actor</th>
                        <th>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedSub.events?.map((ev) => (
                        <tr key={ev.id}>
                          <td>{formatDate(ev.created_at)}</td>
                          <td>
                            <code>{ev.from_status || 'start'} &rarr; {ev.to_status}</code>
                          </td>
                          <td>{ev.actor_email}</td>
                          <td>{ev.reason || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            <div style={{ padding: '12px 24px', backgroundColor: 'var(--color-surface-muted)', borderTop: '1px solid var(--color-border)', textAlign: 'right' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelectedSub(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Create Subscription Modal */}
      {showCreateModal && (
        <div className="modal-backdrop" onClick={() => setShowCreateModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleCreateSubscription}>
              <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Create New Subscription</h3>
              </div>

              <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Customer *</label>
                  <select
                    value={formData.customer_uuid}
                    onChange={(e) => setFormData({ ...formData, customer_uuid: e.target.value })}
                    required
                  >
                    {customers.map((c) => (
                      <option key={c.uuid} value={c.uuid}>
                        {c.name} ({c.company_name || c.email})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Plan *</label>
                  <select
                    value={formData.plan_id}
                    onChange={(e) => setFormData({ ...formData, plan_id: e.target.value })}
                    required
                  >
                    {catalogue?.plans?.map((pl) => (
                      <option key={pl.id} value={pl.id}>
                        {pl.name} ({pl.cycle_display})
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Start Date *</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Product & Variant *</label>
                  <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '8px' }}>
                    <select
                      value={formData.items[0]?.product_id}
                      onChange={(e) => {
                        const pid = e.target.value;
                        setFormData({
                          ...formData,
                          items: [{ ...formData.items[0], product_id: pid, variant_id: '' }],
                        });
                      }}
                      required
                    >
                      {catalogue?.products?.map((p) => (
                        <option key={p.id} value={p.id}>
                          {p.name} ({formatMoney(p.sales_price)})
                        </option>
                      ))}
                    </select>

                    <input
                      type="number"
                      min="1"
                      value={formData.items[0]?.quantity}
                      onChange={(e) => {
                        const q = parseInt(e.target.value) || 1;
                        setFormData({
                          ...formData,
                          items: [{ ...formData.items[0], quantity: q }],
                        });
                      }}
                      placeholder="Qty"
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Tax Rule</label>
                    <select
                      value={formData.tax_rule_id}
                      onChange={(e) => setFormData({ ...formData, tax_rule_id: e.target.value })}
                    >
                      <option value="">None (0%)</option>
                      {catalogue?.tax_rules?.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name} ({t.rate_percent}%)
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>Discount Code</label>
                    <select
                      value={formData.discount_id}
                      onChange={(e) => setFormData({ ...formData, discount_id: e.target.value })}
                    >
                      <option value="">None</option>
                      {catalogue?.discounts?.map((d) => (
                        <option key={d.id} value={d.id}>
                          {d.code} ({d.discount_type === 'percent' ? `${d.value}%` : formatMoney(d.value)})
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div style={{ padding: '14px 24px', backgroundColor: 'var(--color-surface-muted)', borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm" disabled={actionLoading}>
                  {actionLoading ? 'Creating...' : 'Create Draft Subscription'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
