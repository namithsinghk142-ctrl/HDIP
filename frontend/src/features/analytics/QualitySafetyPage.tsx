import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Tag, Table, Typography, Space, Spin, Select, Progress } from 'antd';
import { SafetyCertificateOutlined, WarningOutlined, BugOutlined, RedoOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { fetchQualityAnalytics, QualityOverview } from '../../services/analytics';

const { Title, Text } = Typography;
const { Option } = Select;

export const QualitySafetyPage: React.FC = () => {
  const [data, setData] = useState<QualityOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDept, setSelectedDept] = useState<string>('All');

  useEffect(() => {
    setLoading(true);
    fetchQualityAnalytics(selectedDept)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedDept]);

  const getEventTypeBarOption = () => {
    if (!data) return {};
    const types = data.events_by_type.map((e) => e.event_type);
    const counts = data.events_by_type.map((e) => e.count);

    return {
      title: { text: 'Quality & Safety Incidents by Type', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'category', data: types },
      yAxis: { type: 'value', name: 'Incident Count' },
      series: [
        {
          name: 'Incidents',
          type: 'bar',
          data: counts,
          itemStyle: { color: '#dc2626' }
        }
      ]
    };
  };

  const getSeverityPieOption = () => {
    if (!data) return {};
    const pieData = Object.entries(data.severity_counts).map(([sev, cnt]) => ({
      name: sev,
      value: cnt
    }));

    return {
      title: { text: 'Incident Breakdown by Severity Level', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      series: [
        {
          name: 'Severity',
          type: 'pie',
          radius: ['40%', '70%'],
          data: pieData
        }
      ]
    };
  };

  const deptSafetyColumns = [
    { title: 'Department', dataIndex: 'department', key: 'department', render: (val: string) => <Text strong>{val}</Text> },
    { title: 'Incident Count', dataIndex: 'events_count', key: 'events_count' },
    {
      title: 'Safety Score (0-100)',
      dataIndex: 'safety_score',
      key: 'safety_score',
      render: (score: number) => (
        <Progress percent={score} size="small" status={score >= 90 ? 'success' : (score >= 80 ? 'active' : 'exception')} />
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'excellent' ? 'green' : (status === 'good' ? 'blue' : 'red');
        return <Tag color={color}>{status.toUpperCase().replace('_', ' ')}</Tag>;
      }
    }
  ];

  const recentEventColumns = [
    { title: 'Date', dataIndex: 'event_date', key: 'event_date' },
    { title: 'Department', dataIndex: 'department', key: 'department' },
    { title: 'Event Type', dataIndex: 'event_type', key: 'event_type', render: (val: string) => <Text strong>{val}</Text> },
    {
      title: 'Severity',
      dataIndex: 'severity',
      key: 'severity',
      render: (sev: string) => {
        const color = sev === 'Critical' ? 'red' : (sev === 'High' ? 'orange' : (sev === 'Medium' ? 'gold' : 'green'));
        return <Tag color={color}>{sev}</Tag>;
      }
    },
    { title: 'Details / Notes', dataIndex: 'details', key: 'details' }
  ];

  if (loading && !data) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Quality, Readmissions & Clinical Safety Analytics</Title>
          <Text type="secondary">30-Day Readmission Tracking, Hospital Infection Density & Event Audits</Text>
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
              title="30-Day Readmission Rate"
              value={data?.readmission_rate_pct}
              suffix="%"
              prefix={<RedoOutlined />}
              valueStyle={{ color: data && data.readmission_rate_pct > 12.0 ? '#dc2626' : '#16a34a' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Total readmitted: <Text strong>{data?.readmissions_30d_count}</Text>
            </Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Total Quality Events"
              value={data?.total_quality_events}
              prefix={<WarningOutlined />}
              valueStyle={{ color: '#d97706' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Reported clinical incidents</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Critical Incidents"
              value={data?.severity_counts?.Critical || 0}
              prefix={<BugOutlined />}
              valueStyle={{ color: '#dc2626' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Requires immediate root-cause audit</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Overall Safety Score"
              value={92.4}
              suffix="/ 100"
              prefix={<SafetyCertificateOutlined />}
              valueStyle={{ color: '#059669' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Hospital compliance index</Text>
          </Card>
        </Col>
      </Row>

      {/* Charts & Department Safety Scorecards */}
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="Quality Incident Distribution by Category">
            <ReactECharts option={getEventTypeBarOption()} style={{ height: 320 }} />
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Incident Severity Breakdown">
            <ReactECharts option={getSeverityPieOption()} style={{ height: 320 }} />
          </Card>
        </Col>
      </Row>

      {/* Department Safety Table */}
      <Card title="Departmental Clinical Safety Scorecards">
        <Table
          dataSource={data?.department_safety || []}
          columns={deptSafetyColumns}
          pagination={false}
          size="small"
          rowKey="department"
        />
      </Card>

      {/* Recent Quality Incident Audit Log */}
      <Card title="Recent Clinical Safety Incident Audit Logs">
        <Table
          dataSource={data?.recent_events || []}
          columns={recentEventColumns}
          pagination={{ pageSize: 5 }}
          size="small"
          rowKey="id"
        />
      </Card>
    </Space>
  );
};
