import apiClient from './apiClient';

export interface StaffingOverview {
  total_scheduled: number;
  total_actual: number;
  staffing_deficit: number;
  overall_avg_ratio: number;
  strain_level: string;
  fill_rate_pct: number;
  shifts: {
    shift_type: string;
    avg_ratio: number;
    nurses_scheduled: number;
    nurses_actual: number;
    fill_rate_pct: number;
  }[];
  department_ratios: {
    department: string;
    current_ratio: number;
    target_ratio: number;
    status: string;
  }[];
}

export interface FinancialOverview {
  total_revenue: number;
  total_expense: number;
  net_margin: number;
  margin_pct: number;
  avg_cost_per_case: number;
  categories: {
    category: string;
    amount: number;
    share_pct: number;
  }[];
  payer_mix: {
    payer: string;
    count: number;
    total_cost: number;
    share_pct: number;
  }[];
  departments: {
    department: string;
    revenue: number;
    expense: number;
    net_margin: number;
    status: string;
  }[];
}

export interface EDFlowOverview {
  total_ed_visits: number;
  avg_wait_time_min: number;
  avg_treatment_time_min: number;
  estimated_lwbs_pct: number;
  triage_levels: {
    triage_level: number;
    triage_name: string;
    patient_count: number;
    share_pct: number;
    avg_wait_min: number;
  }[];
  dispositions: {
    disposition: string;
    count: number;
    share_pct: number;
  }[];
  hourly_trend: {
    hour: string;
    avg_wait_min: number;
    volume: number;
  }[];
}

export interface QualityOverview {
  total_encounters: number;
  readmissions_30d_count: number;
  readmission_rate_pct: number;
  total_quality_events: number;
  events_by_type: {
    event_type: string;
    count: number;
  }[];
  severity_counts: {
    Low: number;
    Medium: number;
    High: number;
    Critical: number;
  };
  department_safety: {
    department: string;
    events_count: number;
    safety_score: number;
    status: string;
  }[];
  recent_events: {
    id: string;
    event_date: string;
    event_type: string;
    department: string;
    severity: string;
    details: string;
  }[];
}

export interface OperationalAlertItem {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  context: any;
  recommendations: any[];
  is_acknowledged: boolean;
  created_at: string;
}

export interface DataHealthProfile {
  dataset_name: string;
  total_rows: number;
  total_columns: number;
  completeness_pct: number;
  duplicate_count: number;
  duplicate_pct: number;
  health_score: number;
  status: string;
  column_profiles: any[];
  summary: string;
}

export const fetchStaffingAnalytics = async (department?: string): Promise<StaffingOverview> => {
  const params = department && department !== 'All' ? { department } : {};
  const res = await apiClient.get('/api/v1/analytics/staffing', { params });
  return res.data;
};

export const simulateStaffing = async (currentPatients: number, targetRatio: number) => {
  const res = await apiClient.post(`/api/v1/analytics/staffing/simulate?current_patients=${currentPatients}&target_ratio=${targetRatio}`);
  return res.data;
};

export const fetchFinancialAnalytics = async (department?: string): Promise<FinancialOverview> => {
  const params = department && department !== 'All' ? { department } : {};
  const res = await apiClient.get('/api/v1/analytics/financial', { params });
  return res.data;
};

export const fetchEDFlowAnalytics = async (): Promise<EDFlowOverview> => {
  const res = await apiClient.get('/api/v1/analytics/ed-flow');
  return res.data;
};

export const fetchQualityAnalytics = async (department?: string): Promise<QualityOverview> => {
  const params = department && department !== 'All' ? { department } : {};
  const res = await apiClient.get('/api/v1/analytics/quality', { params });
  return res.data;
};

export const fetchDataHealthProfile = async (): Promise<DataHealthProfile> => {
  const res = await apiClient.get('/api/v1/analytics/data-health');
  return res.data;
};

export const fetchOperationalAlerts = async (severity?: string, isAcknowledged?: boolean): Promise<OperationalAlertItem[]> => {
  const params: any = {};
  if (severity && severity !== 'all') params.severity = severity;
  if (isAcknowledged !== undefined) params.is_acknowledged = isAcknowledged;
  const res = await apiClient.get('/api/v1/decisions/alerts', { params });
  return res.data;
};

export const acknowledgeOperationalAlert = async (alertId: string) => {
  const res = await apiClient.post(`/api/v1/decisions/alerts/${alertId}/acknowledge`);
  return res.data;
};
