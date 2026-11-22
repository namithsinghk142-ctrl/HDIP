import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Statistic, Tag, Table, Typography, Space, Spin, Select } from 'antd';
import { DollarOutlined, FundOutlined, BankOutlined, PieChartOutlined, FallOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import { fetchFinancialAnalytics, FinancialOverview } from '../../services/analytics';

const { Title, Text } = Typography;
const { Option } = Select;

export const FinancialAnalyticsPage: React.FC = () => {
  const [data, setData] = useState<FinancialOverview | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedDept, setSelectedDept] = useState<string>('All');

  useEffect(() => {
    setLoading(true);
    fetchFinancialAnalytics(selectedDept)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [selectedDept]);

  const getCostCategoryPieOption = () => {
    if (!data) return {};
    const pieData = data.categories.map((c) => ({
      name: c.category,
      value: c.amount
    }));

    return {
      title: { text: 'Operating Cost Allocation by Category', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'item', formatter: '{b}: ${c} ({d}%)' },
      legend: { bottom: 0 },
      series: [
        {
          name: 'Cost Category',
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 8 },
          data: pieData
        }
      ]
    };
  };

  const getPayerMixOption = () => {
    if (!data) return {};
    const payers = data.payer_mix.map((p) => p.payer);
    const costs = data.payer_mix.map((p) => p.total_cost);

    return {
      title: { text: 'Payer Mix Revenue Share ($)', left: 'center', textStyle: { fontSize: 14 } },
      tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
      xAxis: { type: 'category', data: payers },
      yAxis: { type: 'value', name: 'Total Revenue ($)' },
      series: [
        {
          name: 'Revenue',
          type: 'bar',
          data: costs,
          itemStyle: { color: '#059669' }
        }
      ]
    };
  };

  const deptColumns = [
    { title: 'Department', dataIndex: 'department', key: 'department', render: (val: string) => <Text strong>{val}</Text> },
    { title: 'Revenue ($)', dataIndex: 'revenue', key: 'revenue', render: (val: number) => `$${val.toLocaleString()}` },
    { title: 'Expense ($)', dataIndex: 'expense', key: 'expense', render: (val: number) => `$${val.toLocaleString()}` },
    {
      title: 'Net Margin ($)',
      dataIndex: 'net_margin',
      key: 'net_margin',
      render: (val: number) => (
        <Text style={{ color: val >= 0 ? '#16a34a' : '#dc2626', fontWeight: 600 }}>
          {val >= 0 ? `+$${val.toLocaleString()}` : `-$${Math.abs(val).toLocaleString()}`}
        </Text>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'profitable' ? 'green' : 'red';
        return <Tag color={color}>{status.toUpperCase()}</Tag>;
      }
    }
  ];

  if (loading && !data) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Financial & Cost-Per-Case Intelligence</Title>
          <Text type="secondary">Departmental Revenue, Cost Driver Waterfall & Payer Mix Analytics</Text>
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
              title="Total Gross Revenue"
              value={data?.total_revenue}
              prefix={<DollarOutlined />}
              formatter={(val) => `$${Number(val).toLocaleString()}`}
              valueStyle={{ color: '#16a34a' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Gross patient revenue</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Operating Expenses"
              value={data?.total_expense}
              prefix={<BankOutlined />}
              formatter={(val) => `$${Number(val).toLocaleString()}`}
              valueStyle={{ color: '#dc2626' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Staffing, supplies & overhead</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Net Operating Margin"
              value={data?.net_margin}
              suffix={` (${data?.margin_pct}%)`}
              prefix={<FundOutlined />}
              formatter={(val) => `$${Number(val).toLocaleString()}`}
              valueStyle={{ color: data && data.net_margin >= 0 ? '#16a34a' : '#dc2626' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Net margin percentage</Text>
          </Card>
        </Col>

        <Col span={6}>
          <Card bodyStyle={{ padding: 20 }}>
            <Statistic
              title="Average Cost Per Case"
              value={data?.avg_cost_per_case}
              prefix={<PieChartOutlined />}
              formatter={(val) => `$${Number(val).toLocaleString()}`}
              valueStyle={{ color: '#2563eb' }}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>Case-mix adjusted cost</Text>
          </Card>
        </Col>
      </Row>

      {/* Main Financial Visualizations */}
      <Row gutter={[16, 16]}>
        <Col span={12}>
          <Card title="Expense Distribution by Category">
            <ReactECharts option={getCostCategoryPieOption()} style={{ height: 320 }} />
          </Card>
        </Col>

        <Col span={12}>
          <Card title="Payer Mix Revenue Breakdown">
            <ReactECharts option={getPayerMixOption()} style={{ height: 320 }} />
          </Card>
        </Col>
      </Row>

      {/* Department Financial Scorecard Table */}
      <Card title="Departmental Financial Performance & Profitability">
        <Table
          dataSource={data?.departments || []}
          columns={deptColumns}
          pagination={false}
          size="small"
          rowKey="department"
        />
      </Card>
    </Space>
  );
};
