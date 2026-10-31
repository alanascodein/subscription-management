import React from 'react';
import { formatMoney, formatDate } from '../api';

export default function DashboardView({ data, onNavigate, onPayInvoice }) {
  if (!data) {
    return (
      <div style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-secondary)' }}>
        Loading dashboard metrics...
      </div>
    );
  }

  const hasRevenueAtRisk = parseFloat(data.revenue_at_risk || 0) > 0;

  return (
    <div style={{ padding: '24px', maxWidth: '1280px', margin: '0 auto' }}>
      {/* Revenue at Risk Headline Banner */}
      {hasRevenueAtRisk && (
        <div style={{
          backgroundColor: '#ffffff',
          border: '1px solid var(--color-danger)',
          borderRadius: '4px',

          padding: '16px 20px',
          marginBottom: '24px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '16px',
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span className="badge badge-danger">Proof Engine Alert</span>
              <span style={{ fontWeight: 600, fontSize: '15px' }}>Potential Revenue at Risk Detected</span>
            </div>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginTop: '4px' }}>
              The mathematical Proof Engine identified discrepancies between contracted subscription schedules and actual billing outcomes.
            </p>
          </div>
          <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div>
              <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
                Unreconciled Exposure
              </div>
              <div className="money" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--color-danger)' }}>
                {formatMoney(data.revenue_at_risk)}
              </div>
            </div>
            <button className="btn btn-danger btn-sm" onClick={() => onNavigate('alerts')}>
              Review Alerts & Fix
            </button>
          </div>
        </div>
      )}

      {/* Metric Cards Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '16px',
        marginBottom: '28px'
      }}>
        <div className="surface" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
            Monthly Recurring Revenue (MRR)
          </div>
          <div className="money" style={{ fontSize: '22px', fontWeight: 700, marginTop: '6px' }}>
            {formatMoney(data.mrr)}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
            Normalized across active plans
          </div>
        </div>

        <div className="surface" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
            Active Subscriptions
          </div>
          <div style={{ fontSize: '22px', fontWeight: 700, marginTop: '6px' }}>
            {data.active_count}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
            Billable customer accounts
          </div>
        </div>

        <div className="surface" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
            Collected This Month
          </div>
          <div className="money" style={{ fontSize: '22px', fontWeight: 700, color: 'var(--color-success)', marginTop: '6px' }}>
            {formatMoney(data.collected_month)}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
            Reconciled payments
          </div>
        </div>

        <div className="surface" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
            Outstanding Balance
          </div>
          <div className="money" style={{ fontSize: '22px', fontWeight: 700, marginTop: '6px' }}>
            {formatMoney(data.outstanding)}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
            Total confirmed unpaid invoices
          </div>
        </div>

        <div className="surface" style={{ padding: '16px' }}>
          <div style={{ fontSize: '11px', color: 'var(--color-text-secondary)', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
            Overdue Balance
          </div>
          <div className="money" style={{ fontSize: '22px', fontWeight: 700, color: data.overdue_count > 0 ? 'var(--color-danger)' : 'inherit', marginTop: '6px' }}>
            {formatMoney(data.overdue_amount)}
          </div>
          <div style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '4px' }}>
            {data.overdue_count} invoice{data.overdue_count !== 1 ? 's' : ''} past due date
          </div>
        </div>
      </div>

      {/* Main Content Grid: Overdue Invoices & Upcoming Renewals */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(480px, 1fr))', gap: '24px' }}>
        {/* Overdue Accounts Table */}
        <div className="surface">
          <div className="surface-header">
            <div>
              <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Overdue Invoices</h3>
              <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                Confirmed invoices requiring payment follow-up
              </p>
            </div>
            <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('invoices')}>
              View all invoices
            </button>
          </div>

          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Invoice</th>
                  <th>Customer</th>
                  <th>Due Date</th>
                  <th>Overdue</th>
                  <th className="money">Balance</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {data.overdue_rows && data.overdue_rows.length > 0 ? (
                  data.overdue_rows.map((row) => (
                    <tr key={row.uuid}>
                      <td>
                        <strong>{row.invoice_number}</strong>
                      </td>
                      <td>{row.customer_name}</td>
                      <td>{formatDate(row.due_date)}</td>
                      <td>
                        <span className="badge badge-danger">
                          +{row.days_overdue}d
                        </span>
                      </td>
                      <td className="money" style={{ color: 'var(--color-danger)' }}>
                        {formatMoney(row.balance_due)}
                      </td>
                      <td>
                        <button
                          className="btn btn-secondary btn-sm"
                          style={{ padding: '3px 8px' }}
                          onClick={() => onPayInvoice(row)}
                        >
                          Record Pay
                        </button>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" style={{ textAlign: 'center', color: 'var(--color-text-secondary)', padding: '24px' }}>
                      No overdue invoices. All accounts are up to date.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Upcoming Renewals & Live Payments */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {/* Upcoming Renewals */}
          <div className="surface">
            <div className="surface-header">
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Upcoming Renewals & Billing</h3>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                  Next recurring period billing dates
                </p>
              </div>
              <button className="btn btn-secondary btn-sm" onClick={() => onNavigate('subscriptions')}>
                Subscriptions
              </button>
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Customer</th>
                    <th>Plan</th>
                    <th>Next Bill Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.upcoming_renewals && data.upcoming_renewals.length > 0 ? (
                    data.upcoming_renewals.map((r) => (
                      <tr key={r.uuid}>
                        <td><strong>{r.customer_name}</strong></td>
                        <td>{r.plan_name}</td>
                        <td>{formatDate(r.next_billing_date)}</td>
                        <td>
                          <span className={`badge ${r.status === 'active' ? 'badge-success' : 'badge-neutral'}`}>
                            {r.status_display}
                          </span>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="4" style={{ textAlign: 'center', color: 'var(--color-text-secondary)', padding: '20px' }}>
                        No upcoming billing cycles scheduled.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Recent Payments */}
          <div className="surface">
            <div className="surface-header">
              <div>
                <h3 style={{ fontSize: '15px', fontWeight: 600 }}>Recent Recorded Payments</h3>
                <p style={{ fontSize: '12px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>
                  Latest customer remittances
                </p>
              </div>
            </div>

            <div className="table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Customer</th>
                    <th>Invoice</th>
                    <th>Method</th>
                    <th className="money">Amount</th>
                  </tr>
                </thead>
                <tbody>
                  {data.recent_payments && data.recent_payments.length > 0 ? (
                    data.recent_payments.map((p, idx) => (
                      <tr key={idx}>
                        <td>{formatDate(p.date)}</td>
                        <td>{p.customer_name}</td>
                        <td><code>{p.invoice_number}</code></td>
                        <td>{p.method}</td>
                        <td className="money" style={{ color: 'var(--color-success)' }}>
                          {formatMoney(p.amount)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan="5" style={{ textAlign: 'center', color: 'var(--color-text-secondary)', padding: '20px' }}>
                        No recent payments recorded.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
