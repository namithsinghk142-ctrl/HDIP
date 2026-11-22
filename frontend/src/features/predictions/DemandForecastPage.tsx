import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Typography, Tag, Button, Space, Spin, Alert, Table, Badge } from 'antd';
import { LineChartOutlined, BulbOutlined, CheckCircleOutlined, ThunderboltOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import apiClient from '../../services/apiClient';
import { ENDPOINTS } from '../../config/api';

const { Title, Text, Paragraph } = Typography;

export const DemandForecastPage: React.FC = () => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiClient.post(ENDPOINTS.PREDICTIONS.DEMAND, { horizon_days: 7 })
      .then(res => {
        setData(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const prediction = data?.prediction;
  const explanation = data?.explanation;
  const impact = data?.impact;
  const recommendations = data?.recommendations || [];

  const getForecastChartOption = () => {
    const dates = prediction?.values?.map((v: any) => v.timestamp) || [];
    const values = prediction?.values?.map((v: any) => v.value) || [];
    const lowerCi = prediction?.values?.map((v: any) => v.lower_ci) || [];
    const upperCi = prediction?.values?.map((v: any) => v.upper_ci) || [];

    return {
      title: { text: '7-Day Projected Daily Admissions', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0 },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', name: 'Admissions / Day' },
      series: [
        {
          name: 'Forecasted Patient Admissions',
          type: 'line',
          data: values,
          itemStyle: { color: '#2563eb' },
          lineStyle: { width: 3 },
          symbolSize: 8
        },
        {
          name: 'Upper Confidence (90%)',
          type: 'line',
          data: upperCi,
          lineStyle: { type: 'dashed', color: '#94a3b8' }
        },
        {
          name: 'Lower Confidence (90%)',
          type: 'line',
          data: lowerCi,
          lineStyle: { type: 'dashed', color: '#94a3b8' }
        }
      ]
    };
  };

  const getSHAPChartOption = () => {
    const factors = explanation?.top_factors || [];
    const categories = factors.map((f: any) => f.feature);
    const impacts = factors.map((f: any) => f.impact);

    return {
      title: { text: 'SHAP Feature Contribution to Demand Surge', left: 'center', textStyle: { fontSize: 13 } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
      xAxis: { type: 'value', name: 'SHAP Value (Impact on Volume)' },
      yAxis: { type: 'category', data: categories.reverse() },
      series: [
        {
          name: 'Feature Impact',
          type: 'bar',
          data: impacts.reverse(),
          itemStyle: {
            color: (params: any) => params.value > 0 ? '#ef4444' : '#10b981'
          }
        }
      ]
    };
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Page Header */}
      <div>
        <Title level={3} style={{ margin: 0 }}>
          <LineChartOutlined style={{ color: '#2563eb', marginRight: 8 }} />
          Patient Demand Forecast
        </Title>
        <Text type="secondary">Multi-step Machine Learning Time-Series Prediction & Decision Intelligence</Text>
      </div>

      {/* PANEL 1: PREDICTION */}
      <Card title={<Space><ThunderboltOutlined style={{ color: '#2563eb' }} /><Text strong>Panel 1: Forecast Model Prediction</Text></Space>}>
        <Row gutter={16}>
          <Col span={16}>
            <ReactECharts option={getForecastChartOption()} style={{ height: 320 }} />
          </Col>
          <Col span={8}>
            <Card type="inner" title="Forecast & Model Registry Metadata" style={{ background: '#f8fafc' }}>
              <Paragraph><Text type="secondary">Model Algorithm:</Text> <Tag color="blue">{data?.model_metadata?.algorithm || 'LightGBM_Regressor'}</Tag></Paragraph>
              <Paragraph><Text type="secondary">Model Version:</Text> <Tag color="purple">{data?.model_metadata?.model_version || 'v1.0.0'}</Tag></Paragraph>
              <Paragraph><Text type="secondary">Last Trained:</Text> <Text strong>{new Date(data?.model_metadata?.last_trained || Date.now()).toLocaleDateString()} {new Date(data?.model_metadata?.last_trained || Date.now()).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</Text></Paragraph>
              <Paragraph><Text type="secondary">Predicted Average Volume:</Text> <Text strong>{prediction?.average_volume} pts/day</Text></Paragraph>
              <Paragraph><Text type="secondary">Volume Surge Delta:</Text> <Tag color="red">+{prediction?.predicted_volume_surge_pct}%</Tag></Paragraph>
              <Paragraph><Text type="secondary">Model Confidence Score:</Text> <Badge status="success" text={`${(prediction?.confidence_score * 100).toFixed(0)}% Confidence (90% CI)`} /></Paragraph>
            </Card>
          </Col>
        </Row>
      </Card>

      {/* PANEL 2 & PANEL 3 */}
      <Row gutter={[16, 16]}>
        {/* PANEL 2: EXPLAINABILITY */}
        <Col span={12}>
          <Card title={<Space><BulbOutlined style={{ color: '#d97706' }} /><Text strong>Panel 2: Explainable AI (SHAP Attribution)</Text></Space>} style={{ height: '100%' }}>
            <ReactECharts option={getSHAPChartOption()} style={{ height: 260 }} />
            <Alert message={explanation?.summary} type="info" showIcon style={{ marginTop: 12 }} />
          </Card>
        </Col>

        {/* PANEL 3: DECISION INTELLIGENCE */}
        <Col span={12}>
          <Card title={<Space><CheckCircleOutlined style={{ color: '#059669' }} /><Text strong>Panel 3: Decision Intelligence & Recommendations</Text></Space>} style={{ height: '100%' }}>
            <div style={{ marginBottom: 16 }}>
              <Text strong style={{ fontSize: 15 }}>Operational Impact Assessment:</Text>
              <Paragraph style={{ marginTop: 4 }}>{impact?.summary}</Paragraph>
              <Space style={{ marginTop: 4 }}>
                <Tag color="volcano">Risk Level: {impact?.risk_level?.toUpperCase()}</Tag>
                <Tag color="gold">Staffing Shortfall: {impact?.staffing_gap?.nurses} Nurses</Tag>
                <Tag color="red">Est. Cost Impact: ${impact?.financial_cost_impact_usd}</Tag>
              </Space>
            </div>

            <Text strong style={{ fontSize: 15 }}>Recommended Actions:</Text>
            <div style={{ marginTop: 8 }}>
              {recommendations.map((rec: any, idx: number) => {
                const actionText = typeof rec === 'string' ? rec : (rec?.action || rec?.recommendation_text || rec?.title || JSON.stringify(rec));
                const urgency = typeof rec === 'object' ? (rec?.urgency ? String(rec.urgency).toUpperCase() : 'IMMEDIATE') : 'IMMEDIATE';
                const expImpact = typeof rec === 'object' ? (rec?.expected_impact || rec?.action_detail || '') : '';
                return (
                  <Card key={idx} type="inner" style={{ marginBottom: 8, borderColor: '#e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text strong>{actionText}</Text>
                      <Tag color={urgency === 'IMMEDIATE' ? 'red' : 'orange'}>{urgency}</Tag>
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
