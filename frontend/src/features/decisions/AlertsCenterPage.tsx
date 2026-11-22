import React, { useEffect, useState } from 'react';
import { Card, Tag, Button, Typography, Space, Spin, Tabs, Alert, Segmented, Row, Col, message } from 'antd';
import { AlertOutlined, CheckCircleOutlined, ThunderboltOutlined, InfoCircleOutlined, FilterOutlined } from '@ant-design/icons';
import { fetchOperationalAlerts, acknowledgeOperationalAlert, OperationalAlertItem } from '../../services/analytics';

const { Title, Text } = Typography;

export const AlertsCenterPage: React.FC = () => {
  const [alerts, setAlerts] = useState<OperationalAlertItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('active'); // active vs acknowledged

  const loadAlerts = () => {
    setLoading(true);
    const isAck = statusFilter === 'acknowledged';
    fetchOperationalAlerts(severityFilter, isAck)
      .then((res) => {
        setAlerts(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    loadAlerts();
  }, [severityFilter, statusFilter]);

  const handleAcknowledge = async (alertId: string, title: string) => {
    try {
      await acknowledgeOperationalAlert(alertId);
      message.success(`Alert "${title}" has been acknowledged.`);
      loadAlerts();
    } catch (err) {
      message.error('Failed to acknowledge alert.');
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toLowerCase()) {
      case 'critical':
        return <Tag color="red" icon={<AlertOutlined />}>CRITICAL</Tag>;
      case 'high':
        return <Tag color="volcano" icon={<ThunderboltOutlined />}>HIGH</Tag>;
      case 'medium':
        return <Tag color="gold" icon={<InfoCircleOutlined />}>MEDIUM</Tag>;
      default:
        return <Tag color="blue">LOW</Tag>;
    }
  };

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header Bar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={3} style={{ margin: 0 }}>Proactive Operational Alert & Governance Center</Title>
          <Text type="secondary">Real-Time Risk Alerts, Prescriptive Actions & Management Acknowledgement Workflow</Text>
        </div>
      </div>

      {/* Filter Toolbar */}
      <Card bodyStyle={{ padding: '16px 24px' }}>
        <Row justify="space-between" align="middle">
          <Col>
            <Space size="large">
              <Space>
                <FilterOutlined />
                <Text strong>Status:</Text>
                <Segmented
                  options={[
                    { label: 'Active Alerts', value: 'active' },
                    { label: 'Acknowledged', value: 'acknowledged' }
                  ]}
                  value={statusFilter}
                  onChange={(val) => setStatusFilter(val as string)}
                />
              </Space>

              <Space>
                <Text strong>Severity:</Text>
                <Segmented
                  options={[
                    { label: 'All', value: 'all' },
                    { label: 'Critical', value: 'critical' },
                    { label: 'High', value: 'high' },
                    { label: 'Medium', value: 'medium' }
                  ]}
                  value={severityFilter}
                  onChange={(val) => setSeverityFilter(val as string)}
                />
              </Space>
            </Space>
          </Col>

          <Col>
            <Text type="secondary">Found <Text strong>{alerts.length}</Text> alerts matching filter</Text>
          </Col>
        </Row>
      </Card>

      {/* Alert Feed List */}
      {loading ? (
        <Spin size="large" style={{ display: 'block', margin: '60px auto' }} />
      ) : alerts.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: '40px 0' }}>
          <CheckCircleOutlined style={{ fontSize: 48, color: '#16a34a', marginBottom: 16 }} />
          <Title level={4}>No Operational Alerts Found</Title>
          <Text type="secondary">All hospital units are operating within nominal safety thresholds.</Text>
        </Card>
      ) : (
        alerts.map((item) => (
          <Card
            key={item.id}
            style={{
              borderLeft: `6px solid ${item.severity === 'critical' ? '#dc2626' : (item.severity === 'high' ? '#ea580c' : '#d97706')}`,
              borderRadius: 8
            }}
          >
            <Row justify="space-between" align="top">
              <Col span={18}>
                <Space style={{ marginBottom: 8 }}>
                  {getSeverityBadge(item.severity)}
                  <Title level={4} style={{ margin: 0 }}>{item.title}</Title>
                </Space>

                <p style={{ fontSize: 14, color: '#334155', margin: '8px 0 16px 0' }}>{item.description}</p>

                {/* Context Payload Tags */}
                {item.context && (
                  <Card size="small" style={{ background: '#f8fafc', marginBottom: 16 }}>
                    <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>
                      OPERATIONAL CONTEXT PARAMETERS:
                    </Text>
                    <Space wrap>
                      {Object.entries(item.context).map(([k, v]) => (
                        <Tag key={k} color="cyan">{k}: {String(v)}</Tag>
                      ))}
                    </Space>
                  </Card>
                )}

                {/* Recommendations */}
                <Text strong style={{ display: 'block', marginBottom: 8 }}>Prescriptive Recommended Actions:</Text>
                <ul style={{ paddingLeft: 20, margin: 0 }}>
                  {item.recommendations?.map((rec: any, idx: number) => {
                    const actionText = typeof rec === 'string' ? rec : (rec?.action || rec?.recommendation_text || rec?.title || JSON.stringify(rec));
                    const urgency = typeof rec === 'object' ? (rec?.urgency || 'immediate') : 'immediate';
                    const category = typeof rec === 'object' ? (rec?.category || 'capacity') : 'capacity';
                    return (
                      <li key={idx} style={{ marginBottom: 6 }}>
                        <Space>
                          <Text style={{ fontWeight: 500 }}>{actionText}</Text>
                          <Tag color="purple">{String(urgency)}</Tag>
                          <Tag color="blue">{String(category)}</Tag>
                        </Space>
                      </li>
                    );
                  })}
                </ul>
              </Col>

              <Col span={5} style={{ textAlign: 'right' }}>
                <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 16 }}>
                  Triggered: {new Date(item.created_at).toLocaleString()}
                </Text>

                {!item.is_acknowledged ? (
                  <Button
                    type="primary"
                    icon={<CheckCircleOutlined />}
                    onClick={() => handleAcknowledge(item.id, item.title)}
                  >
                    Acknowledge Action
                  </Button>
                ) : (
                  <Tag color="green" icon={<CheckCircleOutlined />} style={{ padding: '6px 12px', fontSize: 13 }}>
                    ACKNOWLEDGED
                  </Tag>
                )}
              </Col>
            </Row>
          </Card>
        ))
      )}
    </Space>
  );
};
