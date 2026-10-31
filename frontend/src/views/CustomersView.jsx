import React, { useState, useEffect } from 'react';
import { api, formatMoney, formatDate } from '../api';

export default function CustomersView() {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company_name: '',
    phone: '',
    billing_address: '',
  });

  const fetchCustomers = async () => {
    try {
      setLoading(true);
      const res = await api.getCustomers();
      setCustomers(res.data || []);
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  const handleOpenDetail = async (uuid) => {
    try {
      setActionLoading(true);
      const res = await api.getCustomer(uuid);
      setSelectedCustomer(res.data);
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateCustomer = async (e) => {
    e.preventDefault();
    try {
      setActionLoading(true);
      const res = await api.createCustomer(formData);
      setNotification({ type: 'success', message: res.message });
      setShowCreateModal(false);
      setFormData({ name: '', email: '', company_name: '', phone: '', billing_address: '' });
      fetchCustomers();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
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
          <h2 style={{ fontSize: '20px', fontWeight: 600 }}>Customers Directory</h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginTop: '2px' }}>
            Registered business subscribers linked to user accounts and portal credentials.
          </p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowCreateModal(true)}>
          Register Customer
        </button>
      </div>

      {/* Customers Table */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Customer Name</th>
              <th>Company</th>
              <th>Email</th>
              <th>Phone</th>
              <th>Active Plans</th>
              <th className="money">Unpaid Balance</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  Loading customer records...
                </td>
              </tr>
            ) : customers.length > 0 ? (
              customers.map((c) => (
                <tr key={c.uuid}>
                  <td><strong>{c.name}</strong></td>
                  <td>{c.company_name || '—'}</td>
                  <td>{c.email}</td>
                  <td>{c.phone || '—'}</td>
                  <td>
                    <span className="badge badge-neutral">
                      {c.active_subscriptions_count} active / {c.total_subscriptions_count} total
                    </span>
                  </td>
                  <td className="money" style={{ color: parseFloat(c.unpaid_balance) > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>
                    {formatMoney(c.unpaid_balance)}
                  </td>
                  <td>
                    <button className="btn btn-secondary btn-sm" onClick={() => handleOpenDetail(c.uuid)}>
                      View Profile
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  No customer records registered yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Customer Detail Modal */}
      {selectedCustomer && (
        <div className="modal-backdrop" onClick={() => setSelectedCustomer(null)}>
          <div className="modal-dialog" style={{ maxWidth: '680px' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h3 style={{ fontSize: '16px', fontWeight: 600 }}>{selectedCustomer.name}</h3>
                <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                  {selectedCustomer.company_name} &bull; {selectedCustomer.email}
                </div>
              </div>
              <button onClick={() => setSelectedCustomer(null)} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer' }}>
                &times;
              </button>
            </div>

            <div style={{ padding: '20px 24px' }}>
              {selectedCustomer.billing_address && (
                <div style={{ marginBottom: '16px' }}>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', fontWeight: 600 }}>
                    Billing Address
                  </div>
                  <div style={{ fontSize: '13px', marginTop: '2px', whiteSpace: 'pre-line' }}>
                    {selectedCustomer.billing_address}
                  </div>
                </div>
              )}

              {/* Subscriptions */}
              <div style={{ marginBottom: '20px' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Subscriptions</h4>
                <table className="data-table" style={{ border: '1px solid var(--color-border)', fontSize: '12px' }}>
                  <thead>
                    <tr>
                      <th>Plan</th>
                      <th>Cycle</th>
                      <th>Status</th>
                      <th>Next Billing</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedCustomer.subscriptions?.length > 0 ? (
                      selectedCustomer.subscriptions.map((s) => (
                        <tr key={s.uuid}>
                          <td><strong>{s.plan_name}</strong></td>
                          <td>{s.cycle}</td>
                          <td>
                            <span className={`badge ${s.status === 'active' ? 'badge-success' : 'badge-neutral'}`}>
                              {s.status_display}
                            </span>
                          </td>
                          <td>{formatDate(s.next_billing_date)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="4" style={{ textAlign: 'center', padding: '16px', color: 'var(--color-text-secondary)' }}>
                          No subscriptions linked.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>

              {/* Invoices */}
              <div>
                <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Invoices</h4>
                <table className="data-table" style={{ border: '1px solid var(--color-border)', fontSize: '12px' }}>
                  <thead>
                    <tr>
                      <th>Invoice #</th>
                      <th>Status</th>
                      <th className="money">Total</th>
                      <th className="money">Balance Due</th>
                      <th>Due Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {selectedCustomer.invoices?.length > 0 ? (
                      selectedCustomer.invoices.map((inv) => (
                        <tr key={inv.uuid}>
                          <td><code>{inv.invoice_number}</code></td>
                          <td>
                            <span className={`badge ${inv.status === 'paid' ? 'badge-success' : 'badge-warning'}`}>
                              {inv.status_display}
                            </span>
                          </td>
                          <td className="money">{formatMoney(inv.total)}</td>
                          <td className="money" style={{ color: parseFloat(inv.balance_due) > 0 ? 'var(--color-danger)' : 'inherit' }}>
                            {formatMoney(inv.balance_due)}
                          </td>
                          <td>{formatDate(inv.due_date)}</td>
                        </tr>
                      ))
                    ) : (
                      <tr>
                        <td colSpan="5" style={{ textAlign: 'center', padding: '16px', color: 'var(--color-text-secondary)' }}>
                          No invoices generated.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={{ padding: '12px 24px', backgroundColor: 'var(--color-surface-muted)', borderTop: '1px solid var(--color-border)', textAlign: 'right' }}>
              <button className="btn btn-secondary btn-sm" onClick={() => setSelectedCustomer(null)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Register Customer Modal */}
      {showCreateModal && (
        <div className="modal-backdrop" onClick={() => setShowCreateModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleCreateCustomer}>
              <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Register New Customer</h3>
              </div>

              <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Full Name / Contact *
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. Acme Corp Billing Contact"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Email Address *
                  </label>
                  <input
                    type="email"
                    placeholder="name@company.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      Company Name
                    </label>
                    <input
                      type="text"
                      placeholder="e.g. Acme Software Ltd"
                      value={formData.company_name}
                      onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    />
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      Phone
                    </label>
                    <input
                      type="text"
                      placeholder="+91 98765 43210"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Billing Address
                  </label>
                  <textarea
                    rows="2"
                    placeholder="Street, City, Postal Code"
                    value={formData.billing_address}
                    onChange={(e) => setFormData({ ...formData, billing_address: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ padding: '14px 24px', backgroundColor: 'var(--color-surface-muted)', borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm" disabled={actionLoading}>
                  {actionLoading ? 'Registering...' : 'Register Customer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
