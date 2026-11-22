import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { LoginPage } from './features/auth/LoginPage';
import { CommandCenter } from './features/dashboard/CommandCenter';
import { DemandForecastPage } from './features/predictions/DemandForecastPage';
import { BedOccupancyPage } from './features/predictions/BedOccupancyPage';
import { EDWaitTimePage } from './features/predictions/EDWaitTimePage';
import { ReadmissionRiskPage } from './features/predictions/ReadmissionRiskPage';
import { ModelRegistryPage } from './features/predictions/ModelRegistryPage';
import { ModelMonitoringPage } from './features/predictions/ModelMonitoringPage';
import { DatasetManagementPage } from './features/data/DatasetManagementPage';
import { StaffingAnalyticsPage } from './features/analytics/StaffingAnalyticsPage';
import { FinancialAnalyticsPage } from './features/analytics/FinancialAnalyticsPage';
import { EDAnalyticsPage } from './features/analytics/EDAnalyticsPage';
import { QualitySafetyPage } from './features/analytics/QualitySafetyPage';
import { AlertsCenterPage } from './features/decisions/AlertsCenterPage';
import { ExecutiveDecisionCenter } from './features/decisions/ExecutiveDecisionCenter';
import { ScenarioSimulatorPage } from './features/decisions/ScenarioSimulatorPage';
import { DecisionHistoryPage } from './features/decisions/DecisionHistoryPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const token = localStorage.getItem('access_token');
  if (!token) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<CommandCenter />} />
        <Route path="analytics/staffing" element={<StaffingAnalyticsPage />} />
        <Route path="analytics/financial" element={<FinancialAnalyticsPage />} />
        <Route path="analytics/ed-flow" element={<EDAnalyticsPage />} />
        <Route path="analytics/quality" element={<QualitySafetyPage />} />
        <Route path="predictions/demand" element={<DemandForecastPage />} />
        <Route path="predictions/bed-occupancy" element={<BedOccupancyPage />} />
        <Route path="predictions/ed-wait-time" element={<EDWaitTimePage />} />
        <Route path="predictions/readmission-risk" element={<ReadmissionRiskPage />} />
        <Route path="predictions/registry" element={<ModelRegistryPage />} />
        <Route path="predictions/monitoring" element={<ModelMonitoringPage />} />
        <Route path="decisions/executive" element={<ExecutiveDecisionCenter />} />
        <Route path="decisions/simulator" element={<ScenarioSimulatorPage />} />
        <Route path="decisions/history" element={<DecisionHistoryPage />} />
        <Route path="alerts" element={<AlertsCenterPage />} />
        <Route path="data" element={<DatasetManagementPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

