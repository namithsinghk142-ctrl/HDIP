import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Tag, Table, Typography, Space, Spin, Select, Slider, Button, Alert } from 'antd';
import { TeamOutlined, UserAddOutlined, AlertOutlined, CheckCircleOutlined, CalculatorOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { fetchStaffingAnalytics, simulateStaffing, StaffingOverview } from '../../services/analytics';

const { Title, Text } = Typography;
const { Option } = Select;

export const StaffingAnalyticsPage: React.FC = () => {
  const [data, setData] = useState<StaffingOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDept, setSelectedDept] = useState<string>('All');

  // Simulation State
  const [simPatients, setSimPatients] = useState<number>(40);
  const [simTargetRatio, setSimTargetRatio] = useState<number>(3.0);
  const [simResult, setSimResult] = useState<any>(null);

  const loadData = (dept?: string) => {
    setLoading(true);
    fetchStaffingAnalytics(dept)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadData(selectedDept);
  }, [selectedDept]);

  const handleSimulate = async () => {
    try {
      const res = await simulateStaffing(simPatients, simTargetRatio);
      setSimResult(res);
    } catch (err) {
      console.error(err);
    }
  };

  const getDeptRatioChartOption = () => {
    if (!data) return {};
    const depts = data.department_ratios.map((d) => d.department);
    const current = data.department_ratios.map((d) => d.current_ratio);
    const target = data.department_ratios.map((d) => d.target_ratio);

    return {
      title: { text: 'Nurse-to-Patient Ratio by Department (Actual vs Target)', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      legend: { bottom: 0 },
      xAxis: { type: 'category', data: depts },
      yAxis: { type: 'value', name: 'Patients per Nurse' },
      series: [
        {
          name: 'Current Ratio',
          type: 'bar',
          data: current,
          itemStyle: { color: '#3b82f6' }
        },
        {
          name: 'Safety Target Ratio',
          type: 'line',
          data: target,
          itemStyle: { color: '#ef4444' },
          lineStyle: { width: 3, type: 'dashed' }
        }
      ]
    };
  };

  const shiftColumns = [
    { title: 'Shift Type', dataIndex: 'shift_type', key: 'shift_type', render: (val: string) => <Text strong>{val}</Text> },
    { title: 'Nurses Scheduled', dataIndex: 'nurses_scheduled', key: 'nurses_scheduled' },
    { title: 'Nurses Actual', dataIndex: 'nurses_actual', key: 'nurses_actual' },
    { title: 'Average Ratio', dataIndex: 'avg_ratio', key: 'avg_ratio', render: (val: number) => `1:${val}` },
    {
      title: 'Fill Rate',
      dataIndex: 'fill_rate_pct',
      key: 'fill_rate_pct',
      render: (pct: number) => {
        const color = pct >= 95 ? 'green' : (pct >= 85 ? 'gold' : 'red');
        return <Tag color={color}>{pct}%</Tag>;
      }
    }
  ];

  if (loading && !data) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Staffing Intelligence & Ratio Optimization</Title>
          <Text type="secondary">Nurse-to-Patient Ratio Strain, Shift Fill Rates & Capacity Planning</Text>
        </div>
        <Space>
          <Text strong>Filter Department:</Text>
          <Select value={selectedDept} onChange={setSelectedDept} style={{ width: 180 }}>
            <Option value="All">All Departments</Option>
            <Option value="Emergency">Emergency</Option>
            <Option value="ICU">ICU</Option>
            <Option value="MedSurg">MedSurg</Option>
            <Option value="Pediatrics">Pediatrics</Option>
            <Option value="Cardiology">Cardiology</Option>
            <Option value="Oncology">Oncology</Option>
          </Select>
        </Space>
      </div>

      {/* KPI Cards */}
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Scheduled Nursing Staff"
              value={data?.total_scheduled}
              prefix={<TeamOutlined />}
              valueStyle={{ color: '#2563eb' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Total nursing roster required</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Actual On-Duty Staff"
              value={data?.total_actual}
              prefix={<UserAddOutlined />}
              valueStyle={{ color: data && data.staffing_deficit > 10 ? '#dc2626' : '#16a34a' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Deficit: <Text type="danger" strong>{data?.staffing_deficit} nurses</Text>
            </Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Shift Fill Rate"
              value={data?.fill_rate_pct}
              suffix="%"
              valueStyle={{ color: '#0d9488' }}
              prefix={<CheckCircleOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Shift coverage performance</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Overall Nurse Ratio"
              value={`1:${data?.overall_avg_ratio}`}
              valueStyle={{ color: data?.strain_level === 'Critical' ? '#dc2626' : '#d97706' }}
              prefix={<AlertOutlined />}
            />
            <Tag color={data?.strain_level === 'Critical' ? 'red' : 'gold'} style={{ marginTop: 4 }}>
              {data?.strain_level.toUpperCase()} STRAIN
            </Tag>
          </Card>
        </Col>
      </Row>

      {/* Main Charts & Shift Table */}
      <Row gutter={[16, 16]}>
        <Col span={14}>
          <Card title="Departmental Nurse-to-Patient Ratios">
            <ReactECharts option={getDeptRatioChartOption()} style={{ height: 340 }} />
          </Card>
        </Col>

        <Col span={10}>
          <Card title="Shift Coverage Breakdown">
            <Table
              dataSource={data?.shifts || []}
              columns={shiftColumns}
              pagination={false}
              size="small"
              rowKey="shift_type"
            />
          </Card>
        </Col>
      </Row>

      {/* Interactive Shift Ratio Simulator Widget */}
      <Card title={<Space><CalculatorOutlined style={{ color: '#2563eb' }} /><Text strong>Nurse Safety Ratio Optimizer & Cost Estimator</Text></Space>}>
        <Row gutter={[24, 16]} align="middle">
          <Col span={8}>
            <Text strong>Current Unit Patient Volume: {simPatients} patients</Text>
            <Slider min={10} max={120} value={simPatients} onChange={setSimPatients} />
          </Col>
          <Col span={8}>
            <Text strong>Target Safety Ratio (1:N): 1:{simTargetRatio}</Text>
            <Slider min={1.0} max={6.0} step={0.5} value={simTargetRatio} onChange={setSimTargetRatio} />
          </Col>
          <Col span={8}>
            <Button type="primary" size="large" onClick={handleSimulate} block icon={<CalculatorOutlined />}>
              Calculate Nursing Requirement
            </Button>
          </Col>
        </Row>

        {simResult && (
          <Alert
            style={{ marginTop: 16 }}
            type="info"
            message={<Text strong>Optimization Recommendation</Text>}
            description={
              <div>
                <p style={{ margin: '4px 0' }}>
                  {typeof simResult.recommendation === 'object'
                    ? (simResult.recommendation.action || simResult.recommendation.recommendation_text || JSON.stringify(simResult.recommendation))
                    : simResult.recommendation}
                </p>
                <Text type="secondary">
                  Estimated Shift Cost: <Text strong>${simResult.estimated_shift_cost_usd?.toLocaleString()}</Text>
                </Text>
              </div>
            }
          />
        )}
      </Card>
    </Space>
  );
};
