import React, { useEffect, useState } from 'react';
import { Row, Col, Card, Typography, Tag, Table, Button, Space, Spin, Modal, message, Badge } from 'antd';
import { DatabaseOutlined, ReloadOutlined, CheckCircleOutlined, ThunderboltOutlined, ExperimentOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import { ENDPOINTS } from '../../config/api';

const { Title, Text, Paragraph } = Typography;

export const ModelRegistryPage: React.FC = () => {
  const [models, setModels] = useState<any[]>([]);
  const [benchmarks, setBenchmarks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [retrainingModel, setRetrainingModel] = useState<string | null>(null);

  const fetchRegistry = () => {
    setLoading(true);
    Promise.all([
      apiClient.get(ENDPOINTS.PREDICTIONS.REGISTRY),
      apiClient.get(ENDPOINTS.PREDICTIONS.BENCHMARK)
    ])
      .then(([regRes, benchRes]) => {
        setModels(regRes.data);
        setBenchmarks(benchRes.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchRegistry();
  }, []);

  const handleRetrain = (modelType: string) => {
    setRetrainingModel(modelType);
    apiClient.post(`/api/v1/predictions/models/${modelType}/retrain`)
      .then(res => {
        message.success(res.data.message || `Retraining completed for ${modelType}`);
        setRetrainingModel(null);
        fetchRegistry();
      })
      .catch(err => {
        console.error(err);
        message.error('Retraining failed');
        setRetrainingModel(null);
      });
  };

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />;

  const registryColumns = [
    {
      title: 'Model Type',
      dataIndex: 'model_type',
      key: 'model_type',
      render: (text: string) => <Text strong>{text.toUpperCase().replace('_', ' ')}</Text>
    },
    {
      title: 'Version',
      dataIndex: 'version',
      key: 'version',
      render: (v: string) => <Tag color="purple">{v}</Tag>
    },
    {
      title: 'Production Algorithm',
      dataIndex: 'algorithm',
      key: 'algorithm',
      render: (algo: string) => <Tag color="blue">{algo}</Tag>
    },
    {
      title: 'Evaluation Metrics',
      dataIndex: 'metrics',
      key: 'metrics',
      render: (metrics: any) => (
        <Space size="small">
          {Object.entries(metrics || {}).map(([k, v]: [string, any]) => (
            <Tag key={k} color="cyan">{k}: {typeof v === 'object' ? JSON.stringify(v) : String(v)}</Tag>
          ))}
        </Space>
      )
    },
    {
      title: 'Inference Latency',
      dataIndex: 'avg_latency_ms',
      key: 'avg_latency_ms',
      render: (ms: number) => <Text>{ms} ms</Text>
    },
    {
      title: 'Drift Status',
      dataIndex: 'drift_status',
      key: 'drift_status',
      render: (status: string) => (
        <Tag color={status === 'healthy' ? 'green' : 'red'}>{status.toUpperCase()}</Tag>
      )
    },
    {
      title: 'Last Trained',
      dataIndex: 'trained_at',
      key: 'trained_at',
      render: (dt: string) => new Date(dt).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'action',
      render: (_: any, record: any) => (
        <Button
          type="primary"
          ghost
          icon={<ReloadOutlined />}
          loading={retrainingModel === record.model_type}
          onClick={() => handleRetrain(record.model_type)}
        >
          Retrain Model
        </Button>
      )
    }
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Header */}
      <div>
        <Title level={3} style={{ margin: 0 }}>
          <DatabaseOutlined style={{ color: '#2563eb', marginRight: 8 }} />
          Enterprise Model Registry & MLOps Infrastructure
        </Title>
        <Text type="secondary">Centralized Production Machine Learning Model Catalog, Metrics & Lifecycle Management</Text>
      </div>

      {/* Registry Table */}
      <Card title={<Space><ThunderboltOutlined style={{ color: '#2563eb' }} /><Text strong>Active Production Models</Text></Space>}>
        <Table dataSource={models} columns={registryColumns} rowKey="id" pagination={false} />
      </Card>

      {/* Benchmarking Comparison Card */}
      <Card title={<Space><ExperimentOutlined style={{ color: '#8b5cf6' }} /><Text strong>Candidate Algorithm Benchmarking & Model Selection</Text></Space>}>
        <Row gutter={[16, 16]}>
          {benchmarks.map((b: any, idx: number) => (
            <Col span={12} key={idx}>
              <Card type="inner" title={`${b.model_type.toUpperCase().replace('_', ' ')} (${b.task})`}>
                {b.candidates?.map((cand: any, cIdx: number) => (
                  <div key={cIdx} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px solid #f0f0f0' }}>
                    <div>
                      <Text strong>{cand.algorithm}</Text>
                      {cand.status === 'Selected' && <Tag color="green" style={{ marginLeft: 8 }}>PRODUCTION</Tag>}
                    </div>
                    <Space>
                      <Text type="secondary">{cand.cv_score}</Text>
                      <Tag color="geekblue">{cand.latency_ms} ms</Tag>
                    </Space>
                  </div>
                ))}
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </Space>
  );
};
