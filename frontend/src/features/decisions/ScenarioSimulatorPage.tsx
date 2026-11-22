import React, { useEffect, useState } from 'react';
import {
  Row, Col, Card, Typography, Tag, Button, Space, Spin, Form, InputNumber, Select, Alert, Table, Divider, message
} from 'antd';
import {
  ThunderboltOutlined,
  PlayCircleOutlined,
  ArrowRightOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  FieldTimeOutlined,
  TeamOutlined,
  DollarOutlined
} from '@ant-design/icons';
import {
  fetchScenarioCatalog,
  runScenarioSimulation,
  SimulationResult
} from '../../services/decisions';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

export const ScenarioSimulatorPage: React.FC = () => {
  const [catalog, setCatalog] = useState<any[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>('increased_patient_arrivals');
  const [params, setParams] = useState<Record<string, any>>({ surge_count: 15, surge_duration_h: 6 });
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    fetchScenarioCatalog()
      .then((data) => setCatalog(data))
      .catch((err) => console.error(err));
  }, []);

  const handleScenarioChange = (val: string) => {
    setSelectedScenario(val);
    const item = catalog.find((c) => c.scenario_type === val);
    if (item && item.parameters) {
      const defaultParams: Record<string, any> = {};
      item.parameters.forEach((p: any) => {
        defaultParams[p.name] = p.default;
      });
      setParams(defaultParams);
    }
  };

  const handleRunSimulation = async () => {
    setLoading(true);
    try {
      const res = await runScenarioSimulation(selectedScenario, params, true);
      setResult(res);
      message.success('Scenario simulation completed.');
    } catch (err) {
      message.error('Simulation execution failed.');
    } finally {
      setLoading(false);
    }
  };

  const selectedCatalogItem = catalog.find((c) => c.scenario_type === selectedScenario);

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header */}
      <div>
        <Title level={3} style={{ margin: 0 }}>
          <PlayCircleOutlined style={{ color: '#2563eb', marginRight: 8 }} />
          Scenario Simulation & Operational Impact Engine
        </Title>
        <Text type="secondary">Simulate What-If Scenarios & Predict Downstream Operational Effects Across the Hospital</Text>
      </div>

      <Row gutter={[16, 16]}>
        {/* SCENARIO CONFIGURATION PANEL */}
        <Col span={8}>
          <Card title={<Space><ThunderboltOutlined style={{ color: '#2563eb' }} /><Text strong>Scenario Configuration</Text></Space>}>
            <Form layout="vertical">
              <Form.Item label="Select Scenario Type">
                <Select value={selectedScenario} onChange={handleScenarioChange}>
                  {catalog.map((cat) => (
                    <Option key={cat.scenario_type} value={cat.scenario_type}>
                      {cat.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>

              {selectedCatalogItem && (
                <Paragraph type="secondary" style={{ fontSize: 13, background: '#f8fafc', padding: 8, borderRadius: 4 }}>
                  {selectedCatalogItem.description}
                </Paragraph>
              )}

              <Divider style={{ margin: '12px 0' }} />

              {selectedCatalogItem?.parameters?.map((p: any) => (
                <Form.Item key={p.name} label={p.label}>
                  {p.type === 'int' || p.type === 'float' ? (
                    <InputNumber
                      style={{ width: '100%' }}
                      min={p.min}
                      max={p.max}
                      value={params[p.name]}
                      onChange={(val) => setParams({ ...params, [p.name]: val })}
                    />
                  ) : (
                    <Select
                      style={{ width: '100%' }}
                      value={params[p.name]}
                      onChange={(val) => setParams({ ...params, [p.name]: val })}
                    >
                      <Option value="Emergency">Emergency</Option>
                      <Option value="MedSurg">MedSurg</Option>
                      <Option value="ICU">ICU</Option>
                      <Option value="Day">Day Shift</Option>
                    </Select>
                  )}
                </Form.Item>
              ))}

              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                block
                size="large"
                loading={loading}
                onClick={handleRunSimulation}
              >
                Execute Simulation
              </Button>
            </Form>
          </Card>
        </Col>

        {/* SIMULATION RESULTS & CASCADING IMPACT */}
        <Col span={16}>
          {!result ? (
            <Card style={{ textAlign: 'center', padding: '60px 0' }}>
              <PlayCircleOutlined style={{ fontSize: 48, color: '#94a3b8', marginBottom: 16 }} />
              <Title level={4}>No Simulation Results</Title>
              <Text type="secondary">Configure scenario parameters on the left and click "Execute Simulation".</Text>
            </Card>
          ) : (
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {/* DELTA KPI SUMMARY */}
              <Card title={<Text strong>Simulation Impact Summary ({result.scenario_label})</Text>}>
                <Row gutter={16}>
                  <Col span={6}>
                    <Card size="small" style={{ background: '#f8fafc', textAlign: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>ED Wait Time Delta</Text>
                      <Title level={4} style={{ margin: 0, color: result.delta?.ed_wait_time_delta_min > 0 ? '#dc2626' : '#059669' }}>
                        {result.delta?.ed_wait_time_delta_min > 0 ? '+' : ''}{result.delta?.ed_wait_time_delta_min} min
                      </Title>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card size="small" style={{ background: '#f8fafc', textAlign: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>Bed Occupancy Delta</Text>
                      <Title level={4} style={{ margin: 0, color: result.delta?.bed_occupancy_delta_pct > 0 ? '#dc2626' : '#059669' }}>
                        {result.delta?.bed_occupancy_delta_pct > 0 ? '+' : ''}{result.delta?.bed_occupancy_delta_pct}%
                      </Title>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card size="small" style={{ background: '#f8fafc', textAlign: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>Staffing FTE Gap</Text>
                      <Title level={4} style={{ margin: 0, color: '#ea580c' }}>
                        {result.delta?.staffing_fte_gap_delta} FTE
                      </Title>
                    </Card>
                  </Col>
                  <Col span={6}>
                    <Card size="small" style={{ background: '#f8fafc', textAlign: 'center' }}>
                      <Text type="secondary" style={{ fontSize: 12 }}>Cost Impact</Text>
                      <Title level={4} style={{ margin: 0, color: '#7c3aed' }}>
                        ₹{result.delta?.operational_cost_delta_inr?.toLocaleString()}
                      </Title>
                    </Card>
                  </Col>
                </Row>

                <Alert
                  message={`Cascade Severity: ${result.cascade_severity?.toUpperCase()}`}
                  description={result.cascade_summary}
                  type={result.cascade_severity === 'critical' ? 'error' : 'warning'}
                  showIcon
                  style={{ marginTop: 16 }}
                />
              </Card>

              {/* DOMAIN IMPACT DETAILS */}
              <Card title={<Text strong>Cascading Downstream Effects (7 Domains)</Text>}>
                <Row gutter={[16, 16]}>
                  <Col span={12}>
                    <Card size="small" type="inner" title={<Space><FieldTimeOutlined /><Text strong>ED Flow & Boarding</Text></Space>}>
                      <Paragraph style={{ margin: 0 }}>
                        <Text strong>Direct:</Text> {result.cascade_effects?.ed_wait_time_impact?.direct_effect}<br />
                        <Text strong>Indirect:</Text> {result.cascade_effects?.ed_wait_time_impact?.indirect_effect}
                      </Paragraph>
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small" type="inner" title={<Space><TeamOutlined /><Text strong>Staffing Demand & Ratios</Text></Space>}>
                      <Paragraph style={{ margin: 0 }}>
                        <Text strong>Direct:</Text> {result.cascade_effects?.staffing_demand_impact?.direct_effect}<br />
                        <Text strong>Indirect:</Text> {result.cascade_effects?.staffing_demand_impact?.indirect_effect}
                      </Paragraph>
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small" type="inner" title={<Space><DollarOutlined /><Text strong>Financial & Cost Exposure</Text></Space>}>
                      <Paragraph style={{ margin: 0 }}>
                        <Text strong>Direct:</Text> {result.cascade_effects?.operational_cost_impact?.direct_effect}<br />
                        <Text strong>Indirect:</Text> {result.cascade_effects?.operational_cost_impact?.indirect_effect}
                      </Paragraph>
                    </Card>
                  </Col>
                  <Col span={12}>
                    <Card size="small" type="inner" title={<Space><InfoCircleOutlined /><Text strong>Quality & Readmission Risk</Text></Space>}>
                      <Paragraph style={{ margin: 0 }}>
                        <Text strong>Direct:</Text> {result.cascade_effects?.readmission_risk_impact?.direct_effect}<br />
                        <Text strong>Indirect:</Text> {result.cascade_effects?.readmission_risk_impact?.indirect_effect}
                      </Paragraph>
                    </Card>
                  </Col>
                </Row>
              </Card>

              {/* RECOMMENDED MITIGATION ACTIONS */}
              <Card title={<Text strong>Scenario Mitigation Recommendations</Text>}>
                {result.recommendations?.map((rec: any, idx: number) => {
                  const actionText = typeof rec === 'string' ? rec : (rec?.action || rec?.recommendation_text || rec?.title || JSON.stringify(rec));
                  const detailText = typeof rec === 'object' ? (rec?.action_detail || rec?.description || '') : '';
                  const priorityTier = typeof rec === 'object' ? (rec?.priority_tier || 'P2') : 'P2';
                  return (
                    <Card key={idx} type="inner" style={{ marginBottom: 8 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Text strong>{actionText}</Text>
                        <Tag color="purple">{String(priorityTier)}</Tag>
                      </div>
                      {detailText && <Text type="secondary" style={{ fontSize: 12 }}>{detailText}</Text>}
                    </Card>
                  );
                })}
              </Card>
            </Space>
          )}
        </Col>
      </Row>
    </Space>
  );
};
