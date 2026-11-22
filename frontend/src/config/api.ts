export const API_BASE_URL = '/api/v1';

export const ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_BASE_URL}/auth/login`,
    REGISTER: `${API_BASE_URL}/auth/register`,
    ME: `${API_BASE_URL}/auth/me`,
  },
  ANALYTICS: {
    KPIS: `${API_BASE_URL}/analytics/kpis`,
    DEPARTMENTS: `${API_BASE_URL}/analytics/scorecards`,
    STAFFING: `${API_BASE_URL}/analytics/staffing`,
    FINANCIAL: `${API_BASE_URL}/analytics/financial`,
    ED_FLOW: `${API_BASE_URL}/analytics/ed-flow`,
    QUALITY: `${API_BASE_URL}/analytics/quality`,
    DATA_HEALTH: `${API_BASE_URL}/analytics/data-health`,
  },
  PREDICTIONS: {
    DEMAND: `${API_BASE_URL}/predictions/demand_forecast/forecast`,
    OCCUPANCY: `${API_BASE_URL}/predictions/bed_occupancy/forecast`,
    ED_WAIT_TIME: `${API_BASE_URL}/predictions/ed_wait_time/forecast`,
    READMISSION_RISK: `${API_BASE_URL}/predictions/readmission_risk/forecast`,
    REGISTRY: `${API_BASE_URL}/predictions/models`,
    BENCHMARK: `${API_BASE_URL}/predictions/benchmark`,
  },
  DECISIONS: {
    ALERTS: `${API_BASE_URL}/decisions/alerts`,
    EXECUTIVE: `${API_BASE_URL}/decisions/executive-summary`,
    RECOMMENDATIONS: `${API_BASE_URL}/decisions/recommendations`,
    SIMULATE: `${API_BASE_URL}/decisions/simulate`,
    SCENARIOS: `${API_BASE_URL}/decisions/scenarios`,
    AUDIT_LOG: `${API_BASE_URL}/decisions/audit-log`,
    EFFECTIVENESS: `${API_BASE_URL}/decisions/effectiveness`,
  },
  DATA: {
    DATASETS: `${API_BASE_URL}/data/datasets`,
    UPLOAD: `${API_BASE_URL}/data/datasets/upload`,
  },
};

