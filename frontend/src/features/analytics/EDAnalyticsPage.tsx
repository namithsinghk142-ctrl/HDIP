import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Tag, Table, Typography, Space, Spin } from 'antd';
import { FieldTimeOutlined, MedicineBoxOutlined, AlertOutlined, UsergroupAddOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { fetchEDFlowAnalytics, EDFlowOverview } from '../../services/analytics';

const { Title, Text } = Typography;

export const EDAnalyticsPage: React.FC = () => {
  const [data, setData] = useState<EDFlowOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchEDFlowAnalytics()
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  const getHourlyTrendOption = () => {
    if (!data) return {};
    const hours = data.hourly_trend.map((h) => h.hour);
    const waits = data.hourly_trend.map((h) => h.avg_wait_min);
    const volumes = data.hourly_trend.map((h) => h.volume);

    return {
      title: { text: 'Hourly ED Arrival Volume & Wait Time Timeline (24-Hour Cycle)', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis' },
      legend: { bottom: 0 },
      xAxis: { type: 'category', data: hours },
      yAxis: [
        { type: 'value', name: 'Wait Time (min)' },
        { type: 'value', name: 'Arrival Volume', position: 'right' }
      ],
      series: [
        {
          name: 'Avg Wait Time (min)',
          type: 'line',
          smooth: true,
          data: waits,
          itemStyle: { color: '#d97706' },
          lineStyle: { width: 3 }
        },
        {
          name: 'Patient Arrivals',
          type: 'bar',
          yAxisIndex: 1,
          data: volumes,
          itemStyle: { color: 'rgba(59, 130, 246, 0.4)' }
        }
      ]
    };
  };

  const getDispositionPieOption = () => {
    if (!data) return {};
    const pieData = data.dispositions.map((d) => ({
      name: d.disposition,
      value: d.count
    }));

    return {
      title: { text: 'ED Patient Disposition Distribution', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: { bottom: 0 },
      series: [
        {
          name: 'Disposition',
          type: 'pie',
          radius: '65%',
          data: pieData,
          itemStyle: { borderRadius: 6 }
        }
      ]
    };
  };

  const triageColumns = [
    { title: 'Triage Category', dataIndex: 'triage_name', key: 'triage_name', render: (val: string) => <Text strong>{val}</Text> },
    { title: 'Patient Count', dataIndex: 'patient_count', key: 'patient_count' },
    { title: 'Share (%)', dataIndex: 'share_pct', key: 'share_pct', render: (val: number) => `${val}%` },
    {
      title: 'Avg Wait Time',
      dataIndex: 'avg_wait_min',
      key: 'avg_wait_min',
      render: (val: number) => (
        <Text style={{ color: val > 40 ? '#dc2626' : (val > 20 ? '#d97706' : '#16a34a'), fontWeight: 600 }}>
          {val} mins
        </Text>
      )
    }
  ];

  if (loading && !data) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header Bar */}
      <div>
        <Title level={3} style={{ margin: 0 }}>Emergency Department Flow & Bottleneck Analytics</Title>
        <Text type="secondary">Triage Level (ESI 1-5) Breakdown, Wait-Time Timelines & Disposition Analysis</Text>
      </div>

      {/* KPI Cards */}
      <Row gutter={[16, 16]}>
        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Total ED Patient Visits"
              value={data?.total_ed_visits}
              prefix={<UsergroupAddOutlined />}
              valueStyle={{ color: '#2563eb' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>30-day ED arrivals</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Average Triage Wait Time"
              value={data?.avg_wait_time_min}
              suffix=" min"
              prefix={<FieldTimeOutlined />}
              valueStyle={{ color: data && data.avg_wait_time_min > 30 ? '#dc2626' : '#d97706' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Door-to-provider wait time</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Average Treatment Time"
              value={data?.avg_treatment_time_min}
              suffix=" min"
              prefix={<MedicineBoxOutlined />}
              valueStyle={{ color: '#059669' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Provider-to-disposition time</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Estimated LWBS Rate"
              value={data?.estimated_lwbs_pct}
              suffix="%"
              prefix={<AlertOutlined />}
              valueStyle={{ color: data && data.estimated_lwbs_pct > 3.0 ? '#dc2626' : '#16a34a' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Left Without Being Seen risk</Text>
          </Card>
        </Col>
      </Row>

      {/* Hourly Wait Timeline & Disposition Charts */}
      <Row gutter={[16, 16]}>
        <Col span={15}>
          <Card title="24-Hour Wait Time & Volume Timeline">
            <ReactECharts option={getHourlyTrendOption()} style={{ height: 340 }} />
          </Card>
        </Col>

        <Col span={9}>
          <Card title="Patient Disposition Breakdown">
            <ReactECharts option={getDispositionPieOption()} style={{ height: 340 }} />
          </Card>
        </Col>
      </Row>

      {/* Triage Level Table */}
      <Card title="ESI Triage Level Performance Breakdown">
        <Table
          dataSource={data?.triage_levels || []}
          columns={triageColumns}
          pagination={false}
          size="small"
          rowKey="triage_level"
        />
      </Card>
    </Space>
  );
};
