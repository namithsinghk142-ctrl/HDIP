import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Tag, Alert, Table, Typography, Space, Spin, Button } from 'antd';
import { ArrowUpOutlined, ArrowDownOutlined, WarningOutlined, FieldTimeOutlined, TeamOutlined, ClusterOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../services/apiClient';
import { ENDPOINTS } from '../../config/api';

const { Title, Text } = Typography;

export const CommandCenter: React.FC = () => {
  const [kpis, setKpis] = useState<any>(null);
  const [departments, setDepartments] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      apiClient.get(ENDPOINTS.ANALYTICS.KPIS),
      apiClient.get(ENDPOINTS.ANALYTICS.DEPARTMENTS),
      apiClient.get(ENDPOINTS.DECISIONS.ALERTS)
    ]).then(([kpiRes, deptRes, alertRes]) => {
      setKpis(kpiRes.data);
      setDepartments(deptRes.data);
      setAlerts(alertRes.data);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const getForecastChartOption = () => {
    return {
      title: { text: '72-Hour Bed Occupancy & Patient Volume Forecast', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0 },
      xAxis: {
        type: 'category',
        data: ['Mon 08:00', 'Mon 16:00', 'Tue 00:00', 'Tue 08:00', 'Tue 16:00', 'Wed 00:00', 'Wed 08:00', 'Wed 16:00']
      },
      yAxis: { type: 'value', min: 60, max: 100, axisLabel: { formatter: '{value}%' } },
      series: [
        {
          name: 'Occupancy Forecast (%)',
          type: 'line',
          smooth: true,
          data: [78, 82, 85, 89, 94, 91, 87, 83],
          itemStyle: { color: '#2563eb' },
          lineStyle: { width: 3 },
          areaStyle: {
            color: {
              type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [{ offset: 0, color: 'rgba(37, 99, 235, 0.4)' }, { offset: 1, color: 'rgba(37, 99, 235, 0.05)' }]
            }
          }
        },
        {
          name: 'Upper Confidence Limit (95%)',
          type: 'line',
          smooth: true,
          lineStyle: { type: 'dashed', color: '#94a3b8' },
          data: [82, 86, 89, 93, 98, 95, 91, 87]
        }
      ]
    };
  };

  const columns = [
    { title: 'Department', dataIndex: 'department', key: 'department', render: (text: string) => <Text strong>{text}</Text> },
    { title: 'Occupancy Rate', dataIndex: 'occupancy_pct', key: 'occupancy_pct', render: (val: number) => <Text>{val}%</Text> },
    { title: 'Avg LOS', dataIndex: 'avg_los_days', key: 'avg_los_days', render: (val: number) => <Text>{val} days</Text> },
    { title: 'Staffing Ratio', dataIndex: 'staffing_ratio', key: 'staffing_ratio' },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'critical' ? 'red' : (status === 'warning' ? 'gold' : 'green');
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      }
    }
  ];

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Executive Command Center</Title>
          <Text type="secondary">Real-Time Operational Intelligence & Decision Support</Text>
        </div>
        <Space>
          <Button type="primary" onClick={() => navigate('/predictions/demand')}>
            View Demand Forecast
          </Button>
          <Button onClick={() => navigate('/predictions/bed-occupancy')}>
            View Bed Occupancy
          </Button>
        </Space>
      </div>

      {/* Proactive Alert Banner */}
      {alerts.length > 0 && (
        <Alert
          message={
            <Space>
              <WarningOutlined style={{ color: '#dc2626' }} />
              <Text strong>{alerts[0].title}</Text>
            </Space>
          }
          description={
            <div>
              <p style={{ margin: '4px 0' }}>{alerts[0].description}</p>
              {alerts[0].recommendations && alerts[0].recommendations.length > 0 && (
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Recommended Action:{' '}
                  {typeof alerts[0].recommendations[0] === 'object'
                    ? (alerts[0].recommendations[0].action ||
                       alerts[0].recommendations[0].recommendation_text ||
                       alerts[0].recommendations[0].title ||
                       JSON.stringify(alerts[0].recommendations[0]))
                    : alerts[0].recommendations[0]}
                </Text>
              )}
            </div>
          }
          type="warning"
          showIcon={false}
          style={{ borderLeft: '6px solid #dc2626', background: '#fef2f2' }}
        />
      )}

      {/* KPI Cards */}
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Hospital Occupancy %"
              value={kpis?.occupancy_pct}
              suffix="%"
              valueStyle={{ color: kpis?.occupancy_pct > 85 ? '#cf1322' : '#3f8600' }}
              prefix={<ClusterOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              <ArrowUpOutlined style={{ color: '#cf1322' }} /> {kpis?.occupancy_trend} vs last week
            </Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Average Length of Stay"
              value={kpis?.avg_los_days}
              suffix=" days"
              valueStyle={{ color: '#1890ff' }}
              prefix={<FieldTimeOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              <ArrowDownOutlined style={{ color: '#3f8600' }} /> {kpis?.avg_los_trend} target improvement
            </Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="ED Wait Time"
              value={kpis?.ed_wait_min}
              suffix=" min"
              valueStyle={{ color: '#d97706' }}
              prefix={<FieldTimeOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              <ArrowUpOutlined style={{ color: '#cf1322' }} /> {kpis?.ed_wait_trend} triage surge
            </Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Staffing Ratio"
              value={kpis?.nurse_patient_ratio}
              valueStyle={{ color: '#059669' }}
              prefix={<TeamOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Target ratio maintained across units
            </Text>
          </Card>
        </Col>
      </Row>

      {/* Main Analytics Content */}
      <Row gutter={[16, 16]}>
        <Col span={14}>
          <Card title="72-Hour Predictive Occupancy Trend">
            <ReactECharts option={getForecastChartOption()} style={{ height: 350 }} />
          </Card>
        </Col>

        <Col span={10}>
          <Card title="Department Health Status">
            <Table
              dataSource={departments}
              columns={columns}
              pagination={false}
              size="small"
              rowKey="department"
            />
          </Card>
        </Col>
      </Row>
    </Space>
  );
};
