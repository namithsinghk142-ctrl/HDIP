import React, { useEffect, useState } from 'react';
import {
  Row, Col, Card, Typography, Tag, Button, Space, Spin, Alert, Progress, Tooltip, Table, Modal, message, Badge, Statistic
} from 'antd';
import {
  SafetyCertificateOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  FundOutlined,
  BulbOutlined,
  ArrowUpOutlined,
  LineChartOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import {
  fetchExecutiveSummary,
  acceptRecommendation,
  rejectRecommendation,
  ExecutiveSummary,
  RecommendationItem
} from '../../services/decisions';

const { Title, Text, Paragraph } = Typography;

export const ExecutiveDecisionCenter: React.FC = () => {
  const [summary, setSummary] = useState<ExecutiveSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedRec, setSelectedRec] = useState<RecommendationItem | null>(null);
  const [modalVisible, setModalVisible] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);

  const loadData = () => {
    setLoading(true);
    fetchExecutiveSummary()
      .then((data) => {
        setSummary(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        message.error('Failed to load Executive Decision Center data');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAction = async (rec: RecommendationItem, action: 'accept' | 'reject' | 'defer') => {
    setActionLoading(true);
    try {
      if (action === 'accept') {
        await acceptRecommendation(rec.model_type, rec, 'Accepted via Executive Decision Center');
        message.success('Recommendation accepted and logged to Audit Trail.');
      } else {
        await rejectRecommendation(rec.model_type, rec, action === 'reject' ? 'rejected' : 'deferred', 'Processed via Executive Decision Center');
        message.info(`Recommendation ${action}ed.`);
      }
      setModalVisible(false);
      loadData();
    } catch (err) {
      message.error('Action failed.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const kpis = summary?.kpis;
  const effectiveness = summary?.effectiveness;
  const recommendations = summary?.top_recommendations || [];

  const getEffectivenessChartOption = () => {
    const models = effectiveness?.by_model.map(m => m.model_type.replace('_', ' ').toUpperCase()) || [];
    const predAcc = effectiveness?.by_model.map(m => m.prediction_accuracy_pct) || [];
    const recEff = effectiveness?.by_model.map(m => m.effectiveness_pct) || [];

    return {
      title: { text: 'Recommendation Quality & Accuracy by Model Type', left: 'center', textStyle: { fontSize: 13 } },
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0 },
      xAxis: { type: 'category', data: models },
      yAxis: { type: 'value', min: 70, max: 100, name: 'Accuracy (%)' },
      series: [
        {
          name: 'Prediction Accuracy (%)',
          type: 'bar',
          data: predAcc,
          itemStyle: { color: '#2563eb' }
        },
        {
          name: 'Recommendation Effectiveness (%)',
          type: 'bar',
          data: recEff,
          itemStyle: { color: '#059669' }
        }
      ]
    };
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>
            <SafetyCertificateOutlined style={{ color: '#7c3aed', marginRight: 8 }} />
            Executive Decision Center
          </Title>
          <Text type="secondary">Centralized Operational Risk Governance, Quantitative Recommendations & Outcome Quality Tracking</Text>
        </div>
        <Tag color="purple" style={{ padding: '6px 12px', fontSize: 14 }}>
          Phase 4 Decision Intelligence Active
        </Tag>
      </div>

      {/* PANEL 1: KPI CARDS */}
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title={<Text type="secondary" style={{ fontSize: 13 }}>ACTIVE OPERATIONAL RISKS</Text>}
              value={kpis?.active_risk_alerts_count || 0}
              valueStyle={{ color: '#dc2626', fontWeight: 700 }}
              prefix={<ThunderboltOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Proactive alerts requiring review</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title={<Text type="secondary" style={{ fontSize: 13 }}>CRITICAL (P1) RECOMMENDATIONS</Text>}
              value={kpis?.p1_recommendations_count || 0}
              valueStyle={{ color: '#ea580c', fontWeight: 700 }}
              prefix={<Badge status="error" />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Immediate operational actions</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title={<Text type="secondary" style={{ fontSize: 13 }}>DECISIONS LOGGED IN AUDIT TRAIL</Text>}
              value={kpis?.decisions_logged_count || 0}
              valueStyle={{ color: '#2563eb', fontWeight: 700 }}
              prefix={<CheckCircleOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Total governance history</Text>
          </Card>
        </Col>
        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title={<Text type="secondary" style={{ fontSize: 13 }}>OVERALL DECISION CONFIDENCE</Text>}
              value={kpis?.overall_decision_confidence_pct || 87.5}
              suffix="%"
              valueStyle={{ color: '#059669', fontWeight: 700 }}
              prefix={<FundOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Weighted multi-level confidence</Text>
          </Card>
        </Col>
      </Row>

      {/* PANEL 2 & PANEL 3 */}
      <Row gutter={[16, 16]}>
        {/* TOP PRIORITY RECOMMENDATIONS */}
        <Col span={14}>
          <Card
            title={
              <Space>
                <BulbOutlined style={{ color: '#2563eb' }} />
                <Text strong>Priority Prescriptive Recommendations</Text>
              </Space>
            }
            extra={<Tag color="blue">{recommendations.length} Active Actions</Tag>}
          >
            {recommendations.length === 0 ? (
              <Alert message="No active recommendations. Hospital operating within nominal parameters." type="success" showIcon />
            ) : (
              recommendations.map((rec) => {
                const conf = rec.confidence_profile || {
                  prediction_confidence: 0.88,
                  recommendation_confidence: 0.82,
                  overall_decision_confidence: 0.85
                };
                const confPct = Math.round(conf.overall_decision_confidence * 100);
                return (
                  <Card
                    key={rec.recommendation_id}
                    type="inner"
                    style={{
                      marginBottom: 12,
                      borderLeft: `6px solid ${rec.priority_tier === 'P1' ? '#dc2626' : rec.priority_tier === 'P2' ? '#ea580c' : '#d97706'}`,
                    }}
                  >
                    <Row justify="space-between" align="top">
                      <Col span={17}>
                        <Space style={{ marginBottom: 6 }}>
                          <Tag color={rec.priority_tier === 'P1' ? 'red' : 'volcano'}>{rec.priority_tier}</Tag>
                          <Tag color="purple">{rec.category.toUpperCase()}</Tag>
                          <Tag color="cyan">{rec.department}</Tag>
                        </Space>
                        <Title level={5} style={{ margin: '4px 0 8px 0' }}>{rec.action}</Title>
                        <Paragraph type="secondary" style={{ fontSize: 12, margin: 0 }}>{rec.action_detail}</Paragraph>
                      </Col>
                      <Col span={7} style={{ textAlign: 'right' }}>
                        <Text strong style={{ fontSize: 13, color: rec.expected_financial_impact_inr > 0 ? '#dc2626' : '#059669', display: 'block' }}>
                          Est. Cost: ₹{Math.abs(rec.expected_financial_impact_inr).toLocaleString()}
                        </Text>
                        <Space style={{ marginTop: 8 }}>
                          <Tooltip title={`Prediction: ${(conf.prediction_confidence*100).toFixed(0)}% | Recommendation: ${(conf.recommendation_confidence*100).toFixed(0)}%`}>
                            <Progress type="circle" percent={confPct} width={36} format={() => `${confPct}%`} />
                          </Tooltip>
                          <Button
                            type="primary"
                            size="small"
                            onClick={() => {
                              setSelectedRec(rec);
                              setModalVisible(true);
                            }}
                          >
                            Review & Act
                          </Button>
                        </Space>
                      </Col>
                    </Row>
                  </Card>
                );
              })
            )}
          </Card>
        </Col>

        {/* RECOMMENDATION QUALITY & FEEDBACK LOOP */}
        <Col span={10}>
          <Space direction="vertical" style={{ width: '100%' }} size="middle">
            <Card
              title={
                <Space>
                  <LineChartOutlined style={{ color: '#059669' }} />
                  <Text strong>Recommendation Quality Framework</Text>
                </Space>
              }
            >
              <Row gutter={12} style={{ marginBottom: 16 }}>
                <Col span={8}>
                  <Card size="small" style={{ textAlign: 'center', background: '#f8fafc' }}>
                    <Text type="secondary" style={{ fontSize: 11 }}>Prediction Accuracy</Text>
                    <Title level={4} style={{ margin: 0, color: '#2563eb' }}>{effectiveness?.overall_prediction_accuracy_pct}%</Title>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" style={{ textAlign: 'center', background: '#f8fafc' }}>
                    <Text type="secondary" style={{ fontSize: 11 }}>Effectiveness</Text>
                    <Title level={4} style={{ margin: 0, color: '#059669' }}>{effectiveness?.overall_recommendation_effectiveness_pct}%</Title>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" style={{ textAlign: 'center', background: '#f8fafc' }}>
                    <Text type="secondary" style={{ fontSize: 11 }}>Cost Accuracy</Text>
                    <Title level={4} style={{ margin: 0, color: '#7c3aed' }}>{effectiveness?.overall_cost_estimation_accuracy_pct}%</Title>
                  </Card>
                </Col>
              </Row>
              <ReactECharts option={getEffectivenessChartOption()} style={{ height: 220 }} />
            </Card>

            <Alert
              message="Decision Outcome Feedback Loop"
              description="After executing a recommendation, track actual operational outcomes in Decision History to continuously validate model accuracy."
              type="info"
              showIcon
            />
          </Space>
        </Col>
      </Row>

      {/* DETAIL & ACTION MODAL */}
      <Modal
        title={<Space><SafetyCertificateOutlined style={{ color: '#7c3aed' }} /><Text strong>Decision Explainability & Governance Review</Text></Space>}
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        width={720}
        footer={[
          <Button key="defer" onClick={() => selectedRec && handleAction(selectedRec, 'defer')} loading={actionLoading}>
            Defer Decision
          </Button>,
          <Button key="reject" danger onClick={() => selectedRec && handleAction(selectedRec, 'reject')} loading={actionLoading}>
            Reject Action
          </Button>,
          <Button key="accept" type="primary" icon={<CheckCircleOutlined />} onClick={() => selectedRec && handleAction(selectedRec, 'accept')} loading={actionLoading}>
            Accept & Log Action
          </Button>,
        ]}
      >
        {selectedRec && (
          <Space direction="vertical" size="middle" style={{ width: '100%' }}>
            <Alert message={selectedRec.action} description={selectedRec.action_detail} type="warning" showIcon />

            {/* MULTI-LEVEL CONFIDENCE BREAKDOWN */}
            <Card size="small" title="Multi-Level Decision Confidence Profile" style={{ background: '#f8fafc' }}>
              <Row gutter={16}>
                <Col span={8}>
                  <Text type="secondary" style={{ fontSize: 12 }}>Prediction Confidence</Text>
                  <Progress percent={Math.round((selectedRec.confidence_profile?.prediction_confidence || 0.85)*100)} status="active" />
                </Col>
                <Col span={8}>
                  <Text type="secondary" style={{ fontSize: 12 }}>Recommendation Confidence</Text>
                  <Progress percent={Math.round((selectedRec.confidence_profile?.recommendation_confidence || 0.80)*100)} status="active" strokeColor="#059669" />
                </Col>
                <Col span={8}>
                  <Text type="secondary" style={{ fontSize: 12 }}>Overall Decision Confidence</Text>
                  <Progress percent={Math.round((selectedRec.confidence_profile?.overall_decision_confidence || 0.83)*100)} status="active" strokeColor="#7c3aed" />
                </Col>
              </Row>
            </Card>

            {/* REASONING CHAIN */}
            <Card size="small" title="Reasoning Chain (Predict -> Explain -> Impact -> Recommend)">
              <ul style={{ paddingLeft: 20, margin: 0 }}>
                {selectedRec.reasoning_chain?.map((step, idx) => (
                  <li key={idx} style={{ marginBottom: 6 }}>
                    <Text strong>{step.step}:</Text> <Text type="secondary">{step.description}</Text>
                  </li>
                ))}
              </ul>
            </Card>
          </Space>
        )}
      </Modal>
    </Space>
  );
};
