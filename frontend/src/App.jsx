import React, { useState, useEffect } from 'react';
import { api } from './api';
import Header from './components/Header';
import DemoBar from './components/DemoBar';
import DashboardView from './views/DashboardView';
import AlertsView from './views/AlertsView';
import SubscriptionsView from './views/SubscriptionsView';
import InvoicesView from './views/InvoicesView';
import CustomersView from './views/CustomersView';
import CatalogueView from './views/CatalogueView';
import CustomerPortalView from './views/CustomerPortalView';
import AuthModal from './views/AuthModal';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isAuthOpen, setIsAuthOpen] = useState(false);
  const [initialPayInvoice, setInitialPayInvoice] = useState(null);

  const fetchSessionAndDashboard = async () => {
    try {
      const [authRes, dashRes] = await Promise.allSettled([
        api.getMe(),
        api.getDashboard(),
      ]);

      if (authRes.status === 'fulfilled' && authRes.value.user) {
        setCurrentUser(authRes.value.user);
        if (authRes.value.user.role === 'customer') {
          setActiveTab('portal');
        }
      }

      if (dashRes.status === 'fulfilled') {
        setDashboardData(dashRes.value.data);
      }
    } catch (err) {
      console.error('Initialization error:', err);
    }
  };

  useEffect(() => {
    fetchSessionAndDashboard();
  }, []);

  const handleLogout = async () => {
    try {
      await api.logout();
      setCurrentUser(null);
      setActiveTab('dashboard');
      fetchSessionAndDashboard();
    } catch (err) {
      console.error(err);
    }
  };

  const handlePayFromDashboard = (invRow) => {
    setInitialPayInvoice(invRow);
    setActiveTab('invoices');
  };

  const openAlertsCount = dashboardData?.high_priority_alerts_count || 0;

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Hackathon Top Interactive Demo Bar */}
      <DemoBar
        currentUser={currentUser}
        onUserChange={(usr) => {
          setCurrentUser(usr);
          if (usr?.role === 'customer') {
            setActiveTab('portal');
          } else {
            setActiveTab('dashboard');
          }
        }}
        onRefresh={fetchSessionAndDashboard}
      />

      {/* Main Top Header */}
      <Header
        activeTab={activeTab}
        onTabChange={(tab) => {
          if (tab === 'auth') {
            setIsAuthOpen(true);
          } else {
            setActiveTab(tab);
          }
        }}
        currentUser={currentUser}
        onLogout={handleLogout}
        openAlertsCount={openAlertsCount}
      />

      {/* Main Surface View */}
      <main style={{ flex: 1, paddingBottom: '40px' }}>
        {activeTab === 'dashboard' && (
          <DashboardView
            data={dashboardData}
            onNavigate={(tab) => setActiveTab(tab)}
            onPayInvoice={handlePayFromDashboard}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertsView onRefreshDashboard={fetchSessionAndDashboard} />
        )}

        {activeTab === 'subscriptions' && (
          <SubscriptionsView />
        )}

        {activeTab === 'invoices' && (
          <InvoicesView
            onRefreshDashboard={fetchSessionAndDashboard}
            initialPayInvoice={initialPayInvoice}
            onClearInitialPay={() => setInitialPayInvoice(null)}
          />
        )}

        {activeTab === 'customers' && (
          <CustomersView />
        )}

        {activeTab === 'catalogue' && (
          <CatalogueView />
        )}

        {activeTab === 'portal' && (
          <CustomerPortalView
            currentUser={currentUser}
            onPayInvoice={(inv) => {
              setInitialPayInvoice(inv);
              setActiveTab('invoices');
            }}
          />
        )}
      </main>

      {/* Auth Modal for explicit sign in / registration */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={(usr) => {
          setCurrentUser(usr);
          if (usr.role === 'customer') {
            setActiveTab('portal');
          } else {
            setActiveTab('dashboard');
          }
          fetchSessionAndDashboard();
        }}
      />
    </div>
  );
}
