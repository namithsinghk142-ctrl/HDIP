import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Typography, Tag, Space, Spin, Alert, Badge, InputNumber, Button } from 'antd';
import { FieldTimeOutlined, BulbOutlined, CheckCircleOutlined, ThunderboltOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import apiClient from '../../services/apiClient';
import { ENDPOINTS } from '../../config/api';

const { Title, Text, Paragraph } = Typography;

export const EDWaitTimePage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [edCensus, setEdCensus] = useState(28);
  const [waitingCount, setWaitingCount] = useState(8);
  const [acuityLevel, setAcuityLevel] = useState(3);

  const fetchPrediction = () => {
    setLoading(true);
    apiClient.post(ENDPOINTS.PREDICTIONS.ED_WAIT_TIME, {
      ed_census: edCensus,
      waiting_count: waitingCount,
      acuity_level: acuityLevel
    })
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchPrediction();
  }, []);

  if (loading && !data) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const prediction = data?.prediction;
  const explanation = data?.explanation;
  const impact = data?.impact;
  const recommendations = data?.recommendations || [];
  const modelMetadata = data?.model_metadata || {};

  const getAcuityBreakdownOption = () => {
    const items = prediction?.acuity_breakdown || [];
    const labels = items.map((i: any) => `ESI ${i.esi_level}: ${i.label}`);
    const waits = items.map((i: any) => i.estimated_wait_minutes);

    return {
      title: { text: 'Estimated Wait Time by ESI Triage Level', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis', formatter: '{b}: {c} min' },
      xAxis: { type: 'category', data: labels },
      yAxis: { type: 'value', name: 'Wait Time (Minutes)' },
      series: [
        {
          type: 'bar',
          data: waits,
          itemStyle: {
            color: (params: any) => {
              const colors = ['#dc2626', '#ea580c', '#d97706', '#2563eb', '#16a34a'];
              return colors[params.dataIndex] || '#2563eb';
            }
          }
        }
      ]
    };
  };

  const getSHAPChartOption = () => {
    const factors = explanation?.top_factors || [];
    return {
      title: { text: 'TreeSHAP Feature Attributions', left: 'center', textStyle: { fontSize: 13 } },
      tooltip: { trigger: 'axis' },
      xAxis: { type: 'value', name: 'Impact on Wait Time (Min)' },
      yAxis: { type: 'category', data: factors.map((f: any) => f.feature).reverse() },
      series: [
        {
          type: 'bar',
          data: factors.map((f: any) => f.impact).reverse(),
          itemStyle: { color: '#8b5cf6' }
        }
      ]
    };
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header */}
      <div>
        <Title level={3} style={{ margin: 0 }}>
          <FieldTimeOutlined style={{ color: '#2563eb', marginRight: 8 }} />
          ED Wait Time Prediction & Queue Optimization
        </Title>
        <Text type="secondary">XGBoost Regressor Machine Learning Model & Triage Flow Intelligence</Text>
      </div>

      {/* Interactive Controls */}
      <Card>
        <Row gutter={16} align="middle">
          <Col span={6}>
            <Text strong>Current ED Census:</Text>
            <InputNumber min={5} max={60} value={edCensus} onChange={v => setEdCensus(v || 20)} style={{ width: '100%', marginTop: 4 }} />
          </Col>
          <Col span={6}>
            <Text strong>Patients Waiting Triage:</Text>
            <InputNumber min={0} max={30} value={waitingCount} onChange={v => setWaitingCount(v || 5)} style={{ width: '100%', marginTop: 4 }} />
          </Col>
          <Col span={6}>
            <Text strong>Target Patient Acuity (ESI):</Text>
            <InputNumber min={1} max={5} value={acuityLevel} onChange={v => setAcuityLevel(v || 3)} style={{ width: '100%', marginTop: 4 }} />
          </Col>
          <Col span={6}>
            <Button type="primary" icon={<ThunderboltOutlined />} onClick={fetchPrediction} style={{ marginTop: 20, width: '100%' }}>
              Run Wait Time Model
            </Button>
          </Col>
        </Row>
      </Card>

      {/* PANEL 1: PREDICTION RESULTS */}
      <Card title={<Space><ThunderboltOutlined style={{ color: '#2563eb' }} /><Text strong>Panel 1: Prediction Results & Confidence Bounds</Text></Space>}>
        <Row gutter={16}>
          <Col span={16}>
            <ReactECharts option={getAcuityBreakdownOption()} style={{ height: 300 }} />
          </Col>
          <Col span={8}>
            <Card type="inner" title="Prediction & Model Registry Metadata" style={{ background: '#f8fafc' }}>
              <Paragraph><Text type="secondary">Model Algorithm:</Text> <Tag color="blue">{modelMetadata?.algorithm || 'XGBoost_Regressor'}</Tag></Paragraph>
              <Paragraph><Text type="secondary">Model Version:</Text> <Tag color="purple">{modelMetadata?.model_version || 'v1.0.0'}</Tag></Paragraph>
              <Paragraph><Text type="secondary">Last Trained:</Text> <Text strong>{new Date(modelMetadata?.last_trained || Date.now()).toLocaleDateString()} {new Date(modelMetadata?.last_trained || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</Text></Paragraph>
              <Paragraph><Text type="secondary">Predicted ED Wait Time:</Text> <Text strong style={{ fontSize: 18, color: '#dc2626' }}>{prediction?.predicted_wait_minutes} Minutes</Text></Paragraph>
              <Paragraph><Text type="secondary">95% Confidence Interval:</Text> <Tag color="orange">[{prediction?.lower_ci_minutes} - {prediction?.upper_ci_minutes} min]</Tag></Paragraph>
              <Paragraph><Text type="secondary">Model Confidence Score:</Text> <Badge status="success" text={`${((prediction?.confidence_score || 0.87) * 100).toFixed(0)}% Confidence`} /></Paragraph>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* PANEL 2 & PANEL 3 */}
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title={<Space><BulbOutlined style={{ color: '#d97706' }} /><Text strong>Panel 2: TreeSHAP Feature Attributions</Text></Space>} style={{ height: '100%' }}>
            <ReactECharts option={getSHAPChartOption()} style={{ height: 260 }} />
            <Alert message={explanation?.summary} type="info" showIcon style={{ marginTop: 12 }} />
          </Card>
        </Col>

        <Col span={12}>
          <Card title={<Space><CheckCircleOutlined style={{ color: '#059669' }} /><Text strong>Panel 3: Operational Impact & Recommendations</Text></Space>} style={{ height: '100%' }}>
            <div style={{ marginBottom: 16 }}>
              <Text strong style={{ fontSize: 15 }}>Operational Risk Assessment:</Text>
              <Paragraph style={{ marginTop: 4 }}>{impact?.summary}</Paragraph>
              <Space>
                <Tag color={impact?.risk_level === 'critical' ? 'red' : 'volcano'}>Risk Level: {impact?.risk_level?.toUpperCase()}</Tag>
                <Tag color="orange">LWBS Risk: {impact?.estimated_lwbs_risk_pct}%</Tag>
              </Space>
            </div>

            <Text strong style={{ fontSize: 15 }}>Recommended Operational Actions:</Text>
            <div style={{ marginTop: 8 }}>
              {recommendations.map((rec: any, idx: number) => {
                const actionText = typeof rec === 'string' ? rec : (rec?.action || rec?.recommendation_text || rec?.title || JSON.stringify(rec));
                const urgency = typeof rec === 'object' ? (rec?.urgency ? String(rec.urgency).toUpperCase() : 'IMMEDIATE') : 'IMMEDIATE';
                const expImpact = typeof rec === 'object' ? (rec?.expected_impact || rec?.action_detail || '') : '';
                return (
                  <Card key={idx} type="inner" style={{ marginBottom: 8, borderColor: '#e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text strong>{actionText}</Text>
                      <Tag color="red">{urgency}</Tag>
                    </div>
                    {expImpact && <Text type="secondary" style={{ fontSize: 12 }}>Expected Impact: {expImpact}</Text>}
                  </Card>
                );
              })}
            </div>
          </Card>
        </Col>
      </Row>
    </Space>
  );
};
