import React, { useState, useEffect } from 'react';
import { api, formatMoney, formatDate } from '../api';

export default function AlertsView({ onRefreshDashboard }) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [processingFix, setProcessingFix] = useState(false);
  const [reviewNotes, setReviewNotes] = useState('');
  const [notification, setNotification] = useState(null);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      const res = await api.getAlerts(params);
      setAlerts(res.data || []);
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [statusFilter, priorityFilter]);

  const handleApplyFix = async (alertId) => {
    try {
      setProcessingFix(true);
      const res = await api.applyAlertFix(alertId);
      setNotification({ type: 'success', message: res.message });
      setSelectedAlert(null);
      fetchAlerts();
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setProcessingFix(false);
    }
  };

  const handleUpdateStatus = async (alertId, newStatus) => {
    try {
      setProcessingFix(true);
      const res = await api.reviewAlert(alertId, newStatus, reviewNotes);
      setNotification({ type: 'success', message: res.message });
      setSelectedAlert(null);
      setReviewNotes('');
      fetchAlerts();
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setProcessingFix(false);
    }
  };

  const handleRunDetection = async () => {
    try {
      setLoading(true);
      const res = await api.runDetection();
      setNotification({ type: 'success', message: res.message });
      fetchAlerts();
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const handleInjectLeaks = async () => {
    try {
      setLoading(true);
      const res = await api.injectLeaks();
      setNotification({ type: 'success', message: res.message });
      fetchAlerts();
      if (onRefreshDashboard) onRefreshDashboard();
    } catch (err) {
      setNotification({ type: 'error', message: err.message });
    } finally {
      setLoading(false);
    }
  };

  const totalAtRisk = alerts.reduce((acc, a) => {
    if (a.status !== 'resolved' && a.status !== 'dismissed') {
      return acc + parseFloat(a.amount_at_risk || 0);
    }
    return acc;
  }, 0);

  return (
    <div style={{ padding: '24px', maxWidth: '1280px', margin: '0 auto' }}>
      {notification && (
        <div className={`banner-alert ${notification.type}`}>
          <span>{notification.message}</span>
          <button
            onClick={() => setNotification(null)}
            style={{ background: 'none', border: 'none', color: 'inherit', fontWeight: 'bold' }}
          >
            &times;
          </button>
        </div>
      )}

      {/* Header bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px', flexWrap: 'wrap', gap: '16px' }}>
        <div>
          <h2 style={{ fontSize: '20px', fontWeight: 600 }}>Proof Engine: Revenue Leak Alerts</h2>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginTop: '2px' }}>
            Deterministic audit rules comparing expected contract billing against actual database records.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn btn-secondary btn-sm" onClick={handleRunDetection} disabled={loading}>
            Run Detection
          </button>
          <button className="btn btn-secondary btn-sm" style={{ borderColor: 'var(--color-danger)', color: 'var(--color-danger)' }} onClick={handleInjectLeaks} disabled={loading}>
            Inject Faults
          </button>
        </div>
      </div>

      {/* Filters and Summary Bar */}
      <div className="surface" style={{ padding: '14px 20px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>Status:</span>
          <button
            className={`btn btn-sm ${statusFilter === '' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter('')}
          >
            All
          </button>
          <button
            className={`btn btn-sm ${statusFilter === 'new' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter('new')}
          >
            New
          </button>
          <button
            className={`btn btn-sm ${statusFilter === 'in_review' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter('in_review')}
          >
            In Review
          </button>
          <button
            className={`btn btn-sm ${statusFilter === 'resolved' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setStatusFilter('resolved')}
          >
            Resolved
          </button>

          <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)', marginLeft: '12px' }}>Priority:</span>
          <button
            className={`btn btn-sm ${priorityFilter === 'high' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setPriorityFilter(priorityFilter === 'high' ? '' : 'high')}
          >
            High
          </button>
          <button
            className={`btn btn-sm ${priorityFilter === 'medium' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setPriorityFilter(priorityFilter === 'medium' ? '' : 'medium')}
          >
            Medium
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
          <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Current Exposure:</span>
          <span className="money" style={{ fontSize: '16px', fontWeight: 700, color: 'var(--color-danger)' }}>
            {formatMoney(totalAtRisk)}
          </span>
        </div>
      </div>

      {/* Alerts Table */}
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Priority</th>
              <th>Rule / Type</th>
              <th>Summary</th>
              <th>Target</th>
              <th className="money">Amount at Risk</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  Loading alerts...
                </td>
              </tr>
            ) : alerts.length > 0 ? (
              alerts.map((a) => (
                <tr key={a.id}>
                  <td>
                    <span className={`badge ${a.priority === 'high' ? 'badge-danger' : a.priority === 'medium' ? 'badge-warning' : 'badge-neutral'}`}>
                      {a.priority}
                    </span>
                  </td>
                  <td>
                    <strong>{a.rule_type_display}</strong>
                  </td>
                  <td style={{ maxWidth: '340px' }}>
                    <div style={{ fontWeight: 500 }}>{a.summary}</div>
                    <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                      {a.explanation.length > 100 ? `${a.explanation.slice(0, 100)}...` : a.explanation}
                    </div>
                  </td>
                  <td>
                    {a.customer?.name || (a.invoice_number ? `Inv ${a.invoice_number}` : `Sub #${a.subscription_id}`)}
                  </td>
                  <td className="money" style={{ color: parseFloat(a.amount_at_risk) > 0 ? 'var(--color-danger)' : 'inherit' }}>
                    {formatMoney(a.amount_at_risk)}
                  </td>
                  <td>
                    <span className={`badge ${a.status === 'resolved' ? 'badge-success' : a.status === 'in_review' ? 'badge-warning' : a.status === 'new' ? 'badge-danger' : 'badge-neutral'}`}>
                      {a.status_display}
                    </span>
                  </td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => {
                        setSelectedAlert(a);
                        setReviewNotes(a.review_notes || '');
                      }}
                    >
                      Inspect & Fix
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-secondary)' }}>
                  No alerts match your filter criteria. The Proof Engine reports clean reconciliation.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Alert Inspection & Fix Modal */}
      {selectedAlert && (
        <div className="modal-backdrop" onClick={() => setSelectedAlert(null)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div style={{ padding: '20px 24px', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span className={`badge ${selectedAlert.priority === 'high' ? 'badge-danger' : 'badge-warning'}`} style={{ marginRight: '8px' }}>
                  {selectedAlert.priority} priority
                </span>
                <span style={{ fontSize: '16px', fontWeight: 600 }}>{selectedAlert.rule_type_display}</span>
              </div>
              <button
                onClick={() => setSelectedAlert(null)}
                style={{ background: 'none', border: 'none', fontSize: '18px', cursor: 'pointer', color: 'var(--color-text-secondary)' }}
              >
                &times;
              </button>
            </div>

            <div style={{ padding: '20px 24px' }}>
              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Summary</h4>
                <p style={{ marginTop: '4px', fontSize: '14px', fontWeight: 500 }}>{selectedAlert.summary}</p>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--color-text-secondary)', textTransform: 'uppercase' }}>Proof Engine Mathematical Evidence</h4>
                <div style={{
                  backgroundColor: 'var(--color-surface-muted)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '4px',
                  padding: '12px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap',
                  marginTop: '6px'
                }}>
                  {JSON.stringify(selectedAlert.evidence, null, 2)}
                </div>
              </div>

              <div style={{ marginBottom: '16px', display: 'flex', gap: '20px' }}>
                <div>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Amount at Risk:</span>
                  <div className="money" style={{ fontSize: '18px', fontWeight: 700, color: 'var(--color-danger)' }}>
                    {formatMoney(selectedAlert.amount_at_risk)}
                  </div>
                </div>
                <div>
                  <span style={{ fontSize: '12px', color: 'var(--color-text-secondary)' }}>Status:</span>
                  <div style={{ marginTop: '2px' }}>
                    <span className={`badge ${selectedAlert.status === 'resolved' ? 'badge-success' : 'badge-warning'}`}>
                      {selectedAlert.status_display}
                    </span>
                  </div>
                </div>
              </div>

              {/* Guarded One-Click Fix Action */}
              {selectedAlert.fix_action && selectedAlert.fix_action !== 'none' && selectedAlert.status !== 'resolved' && (
                <div style={{
                  backgroundColor: 'var(--color-surface-muted)',
                  border: '1px solid var(--color-border)',
                  borderRadius: '4px',
                  padding: '14px',
                  marginBottom: '16px',
                }}>
                  <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--color-text-secondary)' }}>
                    Recommended Deterministic Fix:
                  </div>
                  <div style={{ fontSize: '13px', marginTop: '2px', marginBottom: '10px' }}>
                    {selectedAlert.fix_action_display}
                  </div>
                  <button
                    className="btn btn-primary btn-sm"
                    disabled={processingFix}
                    onClick={() => handleApplyFix(selectedAlert.id)}
                  >
                    {processingFix ? 'Applying Fix...' : `Apply Fix: ${selectedAlert.fix_action_display}`}
                  </button>
                </div>
              )}

              {/* Review Notes & Manual Status Update */}
              <div style={{ marginTop: '16px' }}>
                <label style={{ fontSize: '12px', fontWeight: 600, display: 'block', marginBottom: '6px' }}>
                  Audit Review Notes:
                </label>
                <textarea
                  rows="2"
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Record verification notes or reason for manual resolution..."
                  style={{ width: '100%' }}
                />
              </div>
            </div>

            <div style={{
              padding: '14px 24px',
              backgroundColor: 'var(--color-surface-muted)',
              borderTop: '1px solid var(--color-border)',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div>
                {selectedAlert.status !== 'in_review' && selectedAlert.status !== 'resolved' && (
                  <button
                    className="btn btn-secondary btn-sm"
                    disabled={processingFix}
                    onClick={() => handleUpdateStatus(selectedAlert.id, 'in_review')}
                  >
                    Mark In Review
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', gap: '8px' }}>
                {selectedAlert.status !== 'resolved' && (
                  <button
                    className="btn btn-primary btn-sm"
                    style={{ backgroundColor: 'var(--color-success)', borderColor: 'var(--color-success)' }}
                    disabled={processingFix}
                    onClick={() => handleUpdateStatus(selectedAlert.id, 'resolved')}
                  >
                    Mark Resolved
                  </button>
                )}
                {selectedAlert.status !== 'dismissed' && (
                  <button
                    className="btn btn-secondary btn-sm"
                    disabled={processingFix}
                    onClick={() => handleUpdateStatus(selectedAlert.id, 'dismissed')}
                  >
                    Dismiss
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
