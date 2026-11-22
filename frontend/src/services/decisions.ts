import apiClient from './apiClient';

export interface ConfidenceProfile {
  prediction_confidence: number;
  recommendation_confidence: number;
  scenario_simulation_confidence?: number;
  overall_decision_confidence: number;
}

export interface RecommendationItem {
  recommendation_id: string;
  model_type: string;
  action: string;
  action_detail: string;
  category: string;
  priority_score: number;
  priority_tier: string;
  priority_tier_label: string;
  urgency: string;
  department: string;
  quantity: number;
  time_window: string;
  expected_improvement: number;
  expected_wait_reduction_min?: number;
  expected_occupancy_change_pct?: number;
  expected_staffing_change?: number;
  expected_financial_impact_inr: number;
  implementation_difficulty: string;
  confidence_profile: ConfidenceProfile;
  reasoning_chain: {
    step: string;
    description: string;
    source: string;
  }[];
}

export interface AuditLogEntry {
  id: string;
  model_type: string;
  category: string;
  priority_tier: string;
  priority_score: number;
  recommendation_text: string;
  action_detail?: string;
  confidence_profile: ConfidenceProfile;
  expected_outcome: Record<string, any>;
  reasoning_chain?: any[];
  action: string;
  action_note?: string;
  acted_by_name?: string;
  status: string;
  created_at: string;
  implemented_at?: string;
}

export interface DecisionOutcomeSubmission {
  actual_improvement?: number;
  actual_cost_inr?: number;
  actual_wait_reduction_min?: number;
  actual_occupancy_change_pct?: number;
  actual_staffing_change?: number;
  actual_resource_utilization_pct?: number;
  notes?: string;
}

export interface EffectivenessMetrics {
  total_outcomes_recorded: number;
  overall_prediction_accuracy_pct: number;
  overall_recommendation_effectiveness_pct: number;
  overall_cost_estimation_accuracy_pct: number;
  by_model: {
    model_type: string;
    prediction_accuracy_pct: number;
    effectiveness_pct: number;
    outcomes_count: number;
  }[];
}

export interface SimulationResult {
  scenario_type: string;
  scenario_label: string;
  scenario_params: Record<string, any>;
  simulated_at: string;
  confidence_profile: ConfidenceProfile;
  baseline_state: Record<string, any>;
  simulated_state: Record<string, any>;
  delta: Record<string, any>;
  cascade_effects: Record<string, any>;
  recommendations: RecommendationItem[];
  cascade_severity: string;
  cascade_summary: string;
  scenario_id?: string;
}

export interface ExecutiveSummary {
  kpis: {
    active_risk_alerts_count: number;
    p1_recommendations_count: number;
    total_recommendations_count: number;
    decisions_logged_count: number;
    overall_decision_confidence_pct: number;
  };
  active_alerts: any[];
  top_recommendations: RecommendationItem[];
  effectiveness: EffectivenessMetrics;
}

export const fetchScenarioCatalog = async () => {
  const res = await apiClient.get('/api/v1/decisions/scenarios/catalog');
  return res.data;
};

export const runScenarioSimulation = async (
  scenarioType: string,
  params: Record<string, any>,
  saveToDb: boolean = false,
  name?: string
): Promise<SimulationResult> => {
  const res = await apiClient.post('/api/v1/decisions/simulate', {
    scenario_type: scenarioType,
    scenario_params: params,
    name,
  }, {
    params: { save_to_db: saveToDb }
  });
  return res.data;
};

export const fetchSavedScenarios = async () => {
  const res = await apiClient.get('/api/v1/decisions/scenarios');
  return res.data;
};

export const fetchScenarioDetail = async (scenarioId: string) => {
  const res = await apiClient.get(`/api/v1/decisions/scenarios/${scenarioId}`);
  return res.data;
};

export const fetchActiveRecommendations = async (): Promise<RecommendationItem[]> => {
  const res = await apiClient.get('/api/v1/decisions/recommendations');
  return res.data;
};

export const acceptRecommendation = async (
  modelType: string,
  recommendation: RecommendationItem,
  note?: string
) => {
  const res = await apiClient.post('/api/v1/decisions/recommendations/accept', {
    model_type: modelType,
    recommendation,
    note
  });
  return res.data;
};

export const rejectRecommendation = async (
  modelType: string,
  recommendation: RecommendationItem,
  action: 'rejected' | 'deferred' = 'rejected',
  note?: string
) => {
  const res = await apiClient.post('/api/v1/decisions/recommendations/reject', {
    model_type: modelType,
    recommendation,
    action,
    note
  });
  return res.data;
};

export const fetchDecisionAuditLog = async (
  action?: string,
  modelType?: string,
  status?: string
): Promise<AuditLogEntry[]> => {
  const params: any = {};
  if (action && action !== 'all') params.action = action;
  if (modelType && modelType !== 'all') params.model_type = modelType;
  if (status && status !== 'all') params.status = status;

  const res = await apiClient.get('/api/v1/decisions/audit-log', { params });
  return res.data;
};

export const markDecisionImplemented = async (auditId: string) => {
  const res = await apiClient.post(`/api/v1/decisions/audit-log/${auditId}/mark-implemented`);
  return res.data;
};

export const submitDecisionOutcome = async (
  auditId: string,
  outcome: DecisionOutcomeSubmission
) => {
  const res = await apiClient.post(`/api/v1/decisions/audit-log/${auditId}/outcome`, outcome);
  return res.data;
};

export const fetchDecisionEffectiveness = async (): Promise<EffectivenessMetrics> => {
  const res = await apiClient.get('/api/v1/decisions/effectiveness');
  return res.data;
};

export const fetchExecutiveSummary = async (): Promise<ExecutiveSummary> => {
  const res = await apiClient.get('/api/v1/decisions/executive-summary');
  return res.data;
};
