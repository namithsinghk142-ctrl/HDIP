import React, { useEffect, useState } from 'react';
import {
  Table, Card, Typography, Tag, Button, Space, Spin, Modal, Form, InputNumber, Input, message, Tabs, Badge, Progress, Row, Col
} from 'antd';
import {
  HistoryOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  FormOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import {
  fetchDecisionAuditLog,
  markDecisionImplemented,
  submitDecisionOutcome,
  AuditLogEntry,
  DecisionOutcomeSubmission
} from '../../services/decisions';

const { Title, Text, Paragraph } = Typography;

export const DecisionHistoryPage: React.FC = () => {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedEntry, setSelectedEntry] = useState<AuditLogEntry | null>(null);
  const [outcomeModalVisible, setOutcomeModalVisible] = useState<boolean>(false);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const [form] = Form.useForm();

  const loadLogs = () => {
    setLoading(true);
    fetchDecisionAuditLog()
      .then((data) => {
        setLogs(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        message.error('Failed to load Decision Audit Trail.');
        setLoading(false);
      });
  };

  useEffect(() => {
    loadLogs();
  }, []);

  const handleMarkImplemented = async (id: string) => {
    try {
      await markDecisionImplemented(id);
      message.success('Decision marked as implemented.');
      loadLogs();
    } catch (err) {
      message.error('Failed to update status.');
    }
  };

  const handleOutcomeSubmit = async (values: any) => {
    if (!selectedEntry) return;
    setSubmitting(true);
    try {
      await submitDecisionOutcome(selectedEntry.id, values);
      message.success('Actual outcome recorded and effectiveness scores calculated!');
      setOutcomeModalVisible(false);
      form.resetFields();
      loadLogs();
    } catch (err) {
      message.error('Failed to record outcome.');
    } finally {
      setSubmitting(false);
    }
  };

  const columns = [
    {
      title: 'Date & Time',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text: string) => new Date(text).toLocaleString(),
    },
    {
      title: 'Model',
      dataIndex: 'model_type',
      key: 'model_type',
      render: (text: string) => <Tag color="blue">{text.replace('_', ' ').toUpperCase()}</Tag>,
    },
    {
      title: 'Priority',
      dataIndex: 'priority_tier',
      key: 'priority_tier',
      render: (text: string) => <Tag color={text === 'P1' ? 'red' : 'orange'}>{text}</Tag>,
    },
    {
      title: 'Recommendation Action',
      dataIndex: 'recommendation_text',
      key: 'recommendation_text',
      render: (text: any, record: AuditLogEntry) => (
        <div>
          <Text strong>
            {typeof text === 'object'
              ? (text.action || text.recommendation_text || JSON.stringify(text))
              : String(text || '')}
          </Text>
          {record.action_detail && (
            <Paragraph type="secondary" style={{ fontSize: 12, margin: 0 }}>
              {record.action_detail}
            </Paragraph>
          )}
        </div>
      ),
    },
    {
      title: 'Action Taken',
      dataIndex: 'action',
      key: 'action',
      render: (action: string, record: AuditLogEntry) => (
        <div>
          <Tag color={action === 'accepted' ? 'green' : 'volcano'}>
            {action.toUpperCase()}
          </Tag>
          <Text type="secondary" style={{ fontSize: 11, display: 'block' }}>
            by {record.acted_by_name || 'System Admin'}
          </Text>
        </div>
      ),
    },
    {
      title: 'Confidence',
      dataIndex: 'confidence_profile',
      key: 'confidence',
      render: (conf: any) => {
        const val = conf?.overall_decision_confidence || 0.85;
        return <Progress percent={Math.round(val * 100)} size="small" width={60} />;
      },
    },
    {
      title: 'Lifecycle Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'outcome_recorded' ? 'purple' : status === 'implemented' ? 'green' : 'orange';
        return <Tag color={color}>{status.replace('_', ' ').toUpperCase()}</Tag>;
      },
    },
    {
      title: 'Feedback Loop Action',
      key: 'actions',
      render: (_: any, record: AuditLogEntry) => (
        <Space>
          {record.status === 'pending' && record.action === 'accepted' && (
            <Button size="small" type="primary" ghost onClick={() => handleMarkImplemented(record.id)}>
              Mark Implemented
            </Button>
          )}
          {record.status === 'implemented' && (
            <Button
              size="small"
              type="primary"
              icon={<FormOutlined />}
              onClick={() => {
                setSelectedEntry(record);
                setOutcomeModalVisible(true);
              }}
            >
              Record Outcome
            </Button>
          )}
          {record.status === 'outcome_recorded' && (
            <Tag color="purple" icon={<CheckCircleOutlined />}>Verified</Tag>
          )}
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header */}
      <div>
        <Title level={3} style={{ margin: 0 }}>
          <HistoryOutlined style={{ color: '#7c3aed', marginRight: 8 }} />
          Decision Audit Trail & Feedback Loop
        </Title>
        <Text type="secondary">Complete Historical Governance Record of Accepted/Rejected Decisions & Actual Operational Outcomes</Text>
      </div>

      <Card>
        <Table
          dataSource={logs}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      {/* OUTCOME RECORD MODAL */}
      <Modal
        title={<Space><FormOutlined style={{ color: '#059669' }} /><Text strong>Record Actual Operational Outcome</Text></Space>}
        visible={outcomeModalVisible}
        onCancel={() => setOutcomeModalVisible(false)}
        onOk={() => form.submit()}
        confirmLoading={submitting}
      >
        {selectedEntry && (
          <Form form={form} layout="vertical" onFinish={handleOutcomeSubmit}>
            <Paragraph type="secondary">
              Recommendation:{' '}
              <Text strong>
                {selectedEntry.recommendation_text && typeof selectedEntry.recommendation_text === 'object'
                  ? ((selectedEntry.recommendation_text as any).action || (selectedEntry.recommendation_text as any).recommendation_text || JSON.stringify(selectedEntry.recommendation_text))
                  : String(selectedEntry.recommendation_text || '')}
              </Text>
            </Paragraph>

            <Row gutter={16}>
              <Col span={12}>
                <Form.Item name="actual_improvement" label="Actual Improvement (%)">
                  <InputNumber style={{ width: '100%' }} placeholder="e.g. 24.5" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="actual_cost_inr" label="Actual Financial Cost (₹)">
                  <InputNumber style={{ width: '100%' }} placeholder="e.g. 18000" />
                </Form.Item>
              </Col>

              <Col span={12}>
                <Form.Item name="actual_wait_reduction_min" label="Actual Wait Reduction (min)">
                  <InputNumber style={{ width: '100%' }} placeholder="e.g. 16.0" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="actual_occupancy_change_pct" label="Actual Occupancy Δ (%)">
                  <InputNumber style={{ width: '100%' }} placeholder="e.g. -5.2" />
                </Form.Item>
              </Col>

              <Col span={12}>
                <Form.Item name="actual_staffing_change" label="Actual Staffing Added (FTE)">
                  <InputNumber style={{ width: '100%' }} placeholder="e.g. 2" />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item name="actual_resource_utilization_pct" label="Actual Resource Util Δ (%)">
                  <InputNumber style={{ width: '100%' }} placeholder="e.g. 12.0" />
                </Form.Item>
              </Col>
            </Row>

            <Form.Item name="notes" label="Outcome Evaluation Notes">
              <Input.TextArea rows={3} placeholder="Observations on implementation effectiveness..." />
            </Form.Item>
          </Form>
        )}
      </Modal>
    </Space>
  );
};
