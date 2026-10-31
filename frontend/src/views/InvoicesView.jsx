import React, { useState, useEffect } from 'react';
import { api, formatMoney, formatDate } from '../api';

export default function InvoicesView({ onRefreshDashboard, initialPayInvoice, onClearInitialPay }) {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedInvoice, setSelectedInvoice] = useState(null);
  const [showPayModal, setShowPayModal] = useState(false);
  const [payTarget, setPayTarget] = useState(null);
  const [showVoidModal, setShowVoidModal] = useState(false);
  const [voidReason, setVoidReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Payment Form
  const [paymentData, setPaymentData] = useState({
    amount: '',
    method: 'bank_transfer',
    date: new Date().toISOString().split('T')[0],
    reference: '',
    note: '',
  });

  const fetchInvoices = async () => {
    try {
      setLoading(true);
      const params = {};
      if (statusFilter) params.status = statusFilter;
      const res = await api.getInvoices(params);
      setInvoices(res.data || []);
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [statusFilter]);

  // Handle external open from dashboard
  useEffect(() => {
    if (initialPayInvoice) {
      handleOpenPaymentModal(initialPayInvoice);
      if (onClearInitialPay) onClearInitialPay();
    }
  }, [initialPayInvoice]);

  const handleOpenDetail = async (uuid) => {
    try {
      setActionLoading(true);
      const res = await api.getInvoice(uuid);
      setSelectedInvoice(res.data);
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleOpenPaymentModal = (inv) => {
    setPayTarget(inv);
    setPaymentData({
      amount: inv.balance_due || '',
      method: 'bank_transfer',
      date: new Date().toISOString().split('T')[0],
      reference: '',
      note: '',
    });
    setShowPayModal(true);
  };

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    if (!payTarget) return;

    try {
      setActionLoading(true);
      const res = await api.recordPayment(payTarget.uuid, paymentData);
      setNotification({ type: 'success', message: res.message });
      setShowPayModal(false);
      setPayTarget(null);
      fetchInvoices();
      if (selectedInvoice && selectedInvoice.uuid === payTarget.uuid) {
        handleOpenDetail(payTarget.uuid);
      }
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmInvoice = async (uuid) => {
    try {
      setActionLoading(true);
      const res = await api.confirmInvoice(uuid);
      setNotification({ type: 'success', message: res.message });
      fetchInvoices();
      if (selectedInvoice && selectedInvoice.uuid === uuid) {
        handleOpenDetail(uuid);
      }
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handleVoidInvoice = async () => {
    if (!selectedInvoice || !voidReason.trim()) return;

    try {
      setActionLoading(true);
      const res = await api.voidInvoice(selectedInvoice.uuid, voidReason);
      setNotification({ type: 'success', message: res.message });
      setShowVoidModal(false);
      setVoidReason('');
      fetchInvoices();
      handleOpenDetail(selectedInvoice.uuid);
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setActionLoading(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div style={{ padding: '24px', maxWidth: '1280px', margin: '0 auto' }}>
      {notification && (
        <div className={`banner-alert ${notification.type} no-print`}>
          <span>{notification.message}</span>
          <button onClick={() => setNotification(null)} style={{ background: 'none', border: 'none', color: 'inherit' }}>
            &times;
          </button>
        </div>
      )}

      {/* Header bar */}
      <div className="no-print" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 600 }}>Invoices & Billing</h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginTop: '2px' }}>
            Snapshotted line-item billing records, sequential numbering, and atomic payment accounting.
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['', 'confirmed', 'paid', 'draft', 'void'].map((st) => (
            <button
              key={st}
              className={`btn btn-sm ${statusFilter === st ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setStatusFilter(st)}
            >
              {st ? st.charAt(0).toUpperCase() + st.slice(1) : 'All Invoices'}
            </button>
          ))}
        </div>
      </div>

      {/* Invoices Table */}
      <div className="table-wrapper no-print">
        <table className="data-table">
          <thead>
            <tr>
              <th>Invoice #</th>
              <th>Customer</th>
              <th>Period</th>
              <th>Issue Date</th>
              <th>Due Date</th>
              <th className="money">Total</th>
              <th className="money">Balance Due</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  Loading invoices...
                </td>
              </tr>
            ) : invoices.length > 0 ? (
              invoices.map((inv) => (
                <tr key={inv.uuid}>
                  <td>
                    <strong><code>{inv.invoice_number}</code></strong>
                  </td>
                  <td>{inv.customer.name}</td>
                  <td style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    {formatDate(inv.period_start)} &rarr; {formatDate(inv.period_end)}
                  </td>
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
                    <div style={{ display: 'flex', gap: '6px' }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => handleOpenDetail(inv.uuid)}>
                        View
                      </button>
                      {inv.status === 'confirmed' && parseFloat(inv.balance_due) > 0 && (
                        <button className="btn btn-primary btn-sm" onClick={() => handleOpenPaymentModal(inv)}>
                          Pay
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="9" style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  No invoices found matching filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Invoice Detail / Print Modal */}
      {selectedInvoice && (
        <div className="modal-backdrop" onClick={() => setSelectedInvoice(null)}>
          <div className="modal-dialog" style={{ maxWidth: '800px', backgroundColor: '#ffffff' }} onClick={(e) => e.stopPropagation()}>
            <div className="no-print" style={{ padding: '16px 24px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span className={`badge ${selectedInvoice.status === 'paid' ? 'badge-success' : selectedInvoice.status === 'confirmed' ? 'badge-warning' : 'badge-neutral'}`}>
                  {selectedInvoice.status_display}
                </span>
                <span style={{ fontWeight: 600 }}>{selectedInvoice.invoice_number}</span>
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button className="btn btn-secondary btn-sm" onClick={handlePrint}>
                  Print Invoice
                </button>
                {selectedInvoice.status === 'draft' && (
                  <button className="btn btn-primary btn-sm" onClick={() => handleConfirmInvoice(selectedInvoice.uuid)}>
                    Confirm Invoice
                  </button>
                )}
                {selectedInvoice.status === 'confirmed' && parseFloat(selectedInvoice.balance_due) > 0 && (
                  <button className="btn btn-primary btn-sm" onClick={() => handleOpenPaymentModal(selectedInvoice)}>
                    Record Payment
                  </button>
                )}
                {selectedInvoice.status !== 'void' && selectedInvoice.status !== 'paid' && (
                  <button className="btn btn-secondary btn-sm" style={{ color: 'var(--color-danger)' }} onClick={() => setShowVoidModal(true)}>
                    Void
                  </button>
                )}
                <button onClick={() => setSelectedInvoice(null)} style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer' }}>
                  &times;
                </button>
              </div>
            </div>

            {/* Printable Invoice Sheet */}
            <div style={{ padding: '32px 36px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
                <div>
                  <h1 style={{ fontSize: '24px', fontWeight: 700, letterSpacing: '-0.02em', margin: 0 }}>ProofBill</h1>
                  <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                    Tax Invoice & Remittance Statement
                  </p>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '18px', fontWeight: 700, fontFamily: 'var(--font-mono)' }}>
                    {selectedInvoice.invoice_number}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                    Issue Date: {formatDate(selectedInvoice.issue_date)}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>
                    Due Date: {formatDate(selectedInvoice.due_date)}
                  </div>
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', padding: '16px 0', borderTop: '1px solid var(--color-border)', borderBottom: '1px solid var(--color-border)', marginBottom: '24px' }}>
                <div>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Billed To</div>
                  <div style={{ fontSize: '14px', fontWeight: 600, marginTop: '4px' }}>{selectedInvoice.customer.name}</div>
                  {selectedInvoice.customer.company_name && (
                    <div style={{ fontSize: '13px' }}>{selectedInvoice.customer.company_name}</div>
                  )}
                  <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                    {selectedInvoice.customer.email}
                  </div>
                  {selectedInvoice.customer.billing_address && (
                    <div style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '4px', whiteSpace: 'pre-line' }}>
                      {selectedInvoice.customer.billing_address}
                    </div>
                  )}
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Billing Period</div>
                  <div style={{ fontSize: '13px', marginTop: '4px' }}>
                    {formatDate(selectedInvoice.period_start)} to {formatDate(selectedInvoice.period_end)}
                  </div>
                  <div style={{ marginTop: '12px' }}>
                    <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--color-text-secondary)', fontWeight: 600 }}>Status</div>
                    <span className={`badge ${selectedInvoice.status === 'paid' ? 'badge-success' : selectedInvoice.status === 'confirmed' ? 'badge-warning' : 'badge-neutral'}`} style={{ marginTop: '4px' }}>
                      {selectedInvoice.status_display}
                    </span>
                  </div>
                </div>
              </div>

              {/* Snapshotted Line Items Table */}
              <table className="data-table" style={{ border: '1px solid var(--color-border)', marginBottom: '24px' }}>
                <thead>
                  <tr>
                    <th>Description</th>
                    <th className="money">Unit Price</th>
                    <th>Qty</th>
                    <th className="money">Subtotal</th>
                    <th className="money">Discount</th>
                    <th className="money">Tax</th>
                    <th className="money">Line Total</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedInvoice.items?.map((it) => (
                    <tr key={it.id}>
                      <td><strong>{it.description}</strong></td>
                      <td className="money">{formatMoney(it.unit_price)}</td>
                      <td>{it.quantity}</td>
                      <td className="money">{formatMoney(it.line_subtotal)}</td>
                      <td className="money" style={{ color: parseFloat(it.discount_amount) > 0 ? 'var(--color-success)' : 'inherit' }}>
                        {formatMoney(it.discount_amount)}
                      </td>
                      <td className="money">{formatMoney(it.tax_amount)}</td>
                      <td className="money">{formatMoney(it.line_total)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Invoice Totals & Balance Due */}
              <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '24px' }}>
                <div style={{ width: '280px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '13px' }}>
                    <span style={{ color: 'var(--color-text-secondary)' }}>Subtotal:</span>
                    <span className="money">{formatMoney(selectedInvoice.subtotal)}</span>
                  </div>
                  {parseFloat(selectedInvoice.discount_amount) > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '13px', color: 'var(--color-success)' }}>
                      <span>Discount:</span>
                      <span className="money">-{formatMoney(selectedInvoice.discount_amount)}</span>
                    </div>
                  )}
                  {parseFloat(selectedInvoice.tax_amount) > 0 && (
                    <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '13px' }}>
                      <span style={{ color: 'var(--color-text-secondary)' }}>Tax:</span>
                      <span className="money">+{formatMoney(selectedInvoice.tax_amount)}</span>
                    </div>
                  )}
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderTop: '1px solid var(--color-border)', fontSize: '15px', fontWeight: 700 }}>
                    <span>Total Amount:</span>
                    <span className="money">{formatMoney(selectedInvoice.total)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', fontSize: '13px', color: 'var(--color-success)' }}>
                    <span>Amount Paid:</span>
                    <span className="money">{formatMoney(selectedInvoice.amount_paid)}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderTop: '2px solid var(--color-text-primary)', fontSize: '16px', fontWeight: 700, color: parseFloat(selectedInvoice.balance_due) > 0 ? 'var(--color-danger)' : 'var(--color-success)' }}>
                    <span>Balance Due:</span>
                    <span className="money">{formatMoney(selectedInvoice.balance_due)}</span>
                  </div>
                </div>
              </div>

              {/* Recorded Payments History */}
              {selectedInvoice.payments && selectedInvoice.payments.length > 0 && (
                <div>
                  <h4 style={{ fontSize: '13px', fontWeight: 600, marginBottom: '8px' }}>Payment Receipts on this Invoice</h4>
                  <table className="data-table" style={{ border: '1px solid var(--color-border)', fontSize: '12px' }}>
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Method</th>
                        <th>Reference</th>
                        <th className="money">Amount</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedInvoice.payments.map((p) => (
                        <tr key={p.uuid}>
                          <td>{formatDate(p.date)}</td>
                          <td>{p.method_display}</td>
                          <td><code>{p.reference || '—'}</code></td>
                          <td className="money" style={{ color: 'var(--color-success)' }}>{formatMoney(p.amount)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Record Payment Modal */}
      {showPayModal && payTarget && (
        <div className="modal-backdrop" onClick={() => setShowPayModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <form onSubmit={handleRecordPayment}>
              <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)' }}>
                <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Record Payment: {payTarget.invoice_number}</h3>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                  Remaining balance due: <strong>{formatMoney(payTarget.balance_due)}</strong>
                </p>
              </div>

              <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Payment Amount (Rs.) *
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    max={payTarget.balance_due}
                    value={paymentData.amount}
                    onChange={(e) => setPaymentData({ ...paymentData, amount: e.target.value })}
                    required
                  />
                  <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '4px' }}>
                    Supports partial payment. Overpayment is strictly rejected by atomic transaction.
                  </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      Payment Method *
                    </label>
                    <select
                      value={paymentData.method}
                      onChange={(e) => setPaymentData({ ...paymentData, method: e.target.value })}
                    >
                      <option value="bank_transfer">Bank Transfer (NEFT/RTGS)</option>
                      <option value="upi">UPI / Instant</option>
                      <option value="card">Credit / Debit Card</option>
                      <option value="cash">Cash / Cheque</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                      Payment Date *
                    </label>
                    <input
                      type="date"
                      value={paymentData.date}
                      onChange={(e) => setPaymentData({ ...paymentData, date: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div>
                  <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                    Transaction Reference / UTR
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. UTR-982103445"
                    value={paymentData.reference}
                    onChange={(e) => setPaymentData({ ...paymentData, reference: e.target.value })}
                  />
                </div>
              </div>

              <div style={{ padding: '14px 24px', backgroundColor: 'var(--color-surface-muted)', borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowPayModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary btn-sm" disabled={actionLoading}>
                  {actionLoading ? 'Recording...' : 'Record Payment'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Void Modal */}
      {showVoidModal && selectedInvoice && (
        <div className="modal-backdrop" onClick={() => setShowVoidModal(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)' }}>
              <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Void Invoice: {selectedInvoice.invoice_number}</h3>
              <p style={{ fontSize: '12px', color: 'var(--color-danger)', marginTop: '2px' }}>
                Voiding will cancel this invoice and release the billing period for regeneration. A mandatory reason is required.
              </p>
            </div>

            <div style={{ padding: '20px 24px' }}>
              <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '4px' }}>
                Mandatory Void Reason *
              </label>
              <textarea
                rows="3"
                value={voidReason}
                onChange={(e) => setVoidReason(e.target.value)}
                placeholder="e.g. Invoiced wrong subscription cycle / duplicate generated by fault injection..."
                required
              />
            </div>

            <div style={{ padding: '14px 24px', backgroundColor: 'var(--color-surface-muted)', borderTop: '1px solid var(--color-border)', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button type="button" className="btn btn-secondary btn-sm" onClick={() => setShowVoidModal(false)}>
                Cancel
              </button>
              <button
                type="button"
                className="btn btn-danger btn-sm"
                disabled={!voidReason.trim() || actionLoading}
                onClick={handleVoidInvoice}
              >
                {actionLoading ? 'Voiding...' : 'Confirm Void'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
