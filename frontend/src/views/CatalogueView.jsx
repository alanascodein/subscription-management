import React, { useState, useEffect } from 'react';
import { api, formatMoney } from '../api';

export default function CatalogueView() {
  const [catalogue, setCatalogue] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showPlanModal, setShowPlanModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const [planForm, setPlanForm] = useState({
    code: '',
    name: '',
    cycle: 'monthly',
    grace_days: 3,
    minimum_quantity: 1,
    pause_allowed: true,
    early_close_allowed: true,
    renewal_allowed: true,
  });

  const fetchCatalogue = async () => {
    try {
      setLoading(true);
      const res = await api.getCatalogue();
      setCatalogue(res.data);
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCatalogue();
  }, []);

  const handleCreatePlan = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      const res = await api.createPlan(planForm);
      setNotification({ type: 'success', message: res.message });
      setShowPlanModal(false);
      setPlanForm({
        code: '',
        name: '',
        cycle: 'monthly',
        grace_days: 3,
        minimum_quantity: 1,
        pause_allowed: true,
        early_close_allowed: true,
        renewal_allowed: true,
      });
      fetchCatalogue();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        Loading product catalogue...
      </div>
    );
  }

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
          <h2 style={{ fontSize: '20px', fontWeight: 600 }}>Product Catalogue & Plans</h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginTop: '2px' }}>
            Recurring plans, variants with extra prices, check constraints, and tax/discount rules.
          </p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowPlanModal(true)}>
          Create Recurring Plan
        </button>
      </div>

      {/* Plans Section */}
      <div className="surface" style={{ marginBottom: '28px' }}>
        <div className="surface-header">
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Configured Billing Plans</h3>
            <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              Defines billing periodicity, grace days for missed invoices, and lifecycle allowance rules.
            </p>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Code</th>
                <th>Plan Name</th>
                <th>Frequency</th>
                <th>Grace Days</th>
                <th>Pause Allowed</th>
                <th>Early Close</th>
                <th>Renewal Allowed</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {catalogue?.plans?.map((pl) => (
                <tr key={pl.id}>
                  <td><code>{pl.code}</code></td>
                  <td><strong>{pl.name}</strong></td>
                  <td><span className="badge badge-neutral">{pl.cycle_display}</span></td>
                  <td>{pl.grace_days} days</td>
                  <td>{pl.pause_allowed ? 'Yes' : 'No'}</td>
                  <td>{pl.early_close_allowed ? 'Yes' : 'No'}</td>
                  <td>{pl.renewal_allowed ? 'Yes' : 'No'}</td>
                  <td>
                    <span className="badge badge-success">active</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Products & Variants Section */}
      <div className="surface" style={{ marginBottom: '28px' }}>
        <div className="surface-header">
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Products & Editions</h3>
            <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
              Base items with cost price and sales price, plus variant price modifiers.
            </p>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Product</th>
                <th>Description</th>
                <th className="money">Cost Price</th>
                <th className="money">Base Sales Price</th>
                <th>Available Variants & Extra Price</th>
              </tr>
            </thead>
            <tbody>
              {catalogue?.products?.map((p) => (
                <tr key={p.id}>
                  <td><strong>{p.name}</strong></td>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)', maxWidth: '300px' }}>
                    {p.description || '—'}
                  </td>
                  <td className="money">{formatMoney(p.cost_price)}</td>
                  <td className="money">{formatMoney(p.sales_price)}</td>
                  <td>
                    {p.variants?.length > 0 ? (
                      <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {p.variants.map((v) => (
                          <span key={v.id} className="badge badge-neutral">
                            {v.name} (+{formatMoney(v.extra_price)})
                          </span>
                        ))}
                      </div>
                    ) : (
                      <span style={{ color: 'var(--color-text-muted)', fontSize: '12px' }}>Standard single tier</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Tax Rules & Discounts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Tax Rules */}
        <div className="surface">
          <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Tax Rules</h3>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Rule Name</th>
                  <th className="money">Rate Percent</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {catalogue?.tax_rules?.map((t) => (
                  <tr key={t.id}>
                    <td><strong>{t.name}</strong></td>
                    <td className="money">{t.rate_percent}%</td>
                    <td><span className="badge badge-success">active</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Discounts */}
        <div className="surface">
          <h3 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Discount Codes</h3>
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Code</th>
                  <th>Discount Name</th>
                  <th>Value</th>
                  <th>Usage</th>
                </tr>
              </thead>
              <tbody>
                {catalogue?.discounts?.map((d) => (
                  <tr key={d.id}>
                    <td><code>{d.code}</code></td>
                    <td>{d.name}</td>
                    <td>{d.discount_type === 'percent' ? `${d.value}%` : formatMoney(d.value)}</td>
                    <td><span className="badge badge-neutral">{d.times_used} / {d.usage_limit || '∞'}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Create Plan Modal */}
      {showPlanModal && (
        <div className="modal-backdrop" onClick={() => setShowPlanModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleCreatePlan}>
              <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Create Recurring Billing Plan</h3>
              </div>

              <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      Plan Code *
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. quarterly-pro"
                      value={planForm.code}
                      onChange={(e) => setPlanForm({ ...planForm, code: e.target.value })}
                      required
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      Plan Name *
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Quarterly Pro Tier"
                      value={planForm.name}
                      onChange={(e) => setPlanForm({ ...planForm, name: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      Billing Cycle *
                    </label>
                    <select
                      value={planForm.cycle}
                      onChange={(e) => setPlanForm({ ...planForm, cycle: e.target.value })}
                    >
                      <option value="monthly">Monthly</option>
                      <option value="yearly">Yearly</option>
                      <option value="weekly">Weekly</option>
                      <option value="daily">Daily</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      Grace Days *
                    </label>
                    <input
                      type="number"
                      min="0"
                      value={planForm.grace_days}
                      onChange={(e) => setPlanForm({ ...planForm, grace_days: parseInt(e.target.value) || 0 })}
                      required
                    />
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '20px', marginTop: '6px' }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={planForm.pause_allowed}
                      onChange={(e) => setPlanForm({ ...planForm, pause_allowed: e.target.checked })}
                    />
                    Pause Allowed
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={planForm.early_close_allowed}
                      onChange={(e) => setPlanForm({ ...planForm, early_close_allowed: e.target.checked })}
                    />
                    Early Close Allowed
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', cursor: 'pointer' }}>
                    <input
                      type="checkbox"
                      checked={planForm.renewal_allowed}
                      onChange={(e) => setPlanForm({ ...planForm, renewal_allowed: e.target.checked })}
                    />
                    Renewal Allowed
                  </label>
                </div>
              </div>

              <div style={{ padding: '14px 24px', backgroundColor: 'var(--color-surface-muted)', borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowPlanModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm" disabled={actionLoading}>
                  {actionLoading ? 'Creating...' : 'Create Plan'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
