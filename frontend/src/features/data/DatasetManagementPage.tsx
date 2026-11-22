import React, { useEffect, useState } from 'react';
import { Table, Card, Button, Typography, Tag, Upload, message, Space, Progress, Modal } from 'antd';
import { UploadOutlined, DatabaseOutlined, CheckCircleOutlined, FileTextOutlined } from '@ant-design/icons';
import apiClient from '../../services/apiClient';
import { ENDPOINTS } from '../../config/api';

const { Title, Text } = Typography;

export const DatasetManagementPage: React.FC = () => {
  const [datasets, setDatasets] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);

  const fetchDatasets = () => {
    setLoading(true);
    apiClient.get(ENDPOINTS.DATA.DATASETS)
      .then(res => {
        setDatasets(res.data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleUpload = (info: any) => {
    const { status, response } = info.file;
    if (status === 'uploading') {
      setUploading(true);
    }
    if (status === 'done') {
      message.success(`${info.file.name} dataset uploaded and profiled successfully.`);
      setUploading(false);
      fetchDatasets();
    } else if (status === 'error') {
      message.error(`${info.file.name} upload failed.`);
      setUploading(false);
    }
  };

  const columns = [
    { title: 'Dataset Name', dataIndex: 'name', key: 'name', render: (text: string) => <Text strong><FileTextOutlined style={{ marginRight: 6 }} />{text}</Text> },
    { title: 'Rows', dataIndex: 'row_count', key: 'row_count', render: (val: number) => val ? val.toLocaleString() : '-' },
    { title: 'Columns', dataIndex: 'column_count', key: 'column_count' },
    {
      title: 'Quality Score',
      dataIndex: 'quality_score',
      key: 'quality_score',
      render: (score: number) => (
        <Space>
          <Progress type="circle" percent={score} width={32} format={percent => `${percent}%`} />
          <Text>{score >= 80 ? 'High Quality' : 'Needs Clean'}</Text>
        </Space>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => <Tag color="green"><CheckCircleOutlined /> {status.toUpperCase()}</Tag>
    },
    { title: 'Uploaded At', dataIndex: 'created_at', key: 'created_at', render: (val: string) => new Date(val).toLocaleDateString() }
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div>
        <Title level={3} style={{ margin: 0 }}>
          <DatabaseOutlined style={{ color: '#2563eb', marginRight: 8 }} />
          Hospital Data Management
        </Title>
        <Text type="secondary">Ingest, Profile, and Catalog Operational Hospital Datasets</Text>
      </div>

      <Card title="Upload New Dataset File (CSV / Excel)">
        <Upload.Dragger
          name="file"
          multiple={false}
          action={ENDPOINTS.DATA.UPLOAD}
          headers={{ Authorization: `Bearer ${localStorage.getItem('access_token')}` }}
          onChange={handleUpload}
          showUploadList={false}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined style={{ fontSize: 36, color: '#2563eb' }} />
          </p>
          <p className="ant-upload-text">Click or drag hospital dataset file (CSV/Excel) to this area to upload</p>
          <p className="ant-upload-hint">Automatic schema inference, null profiling, and dataset quality scoring applied instantly.</p>
        </Upload.Dragger>
      </Card>

      <Card title="Cataloged Datasets">
        <Table
          dataSource={datasets}
          columns={columns}
          loading={loading}
          rowKey="id"
        />
      </Card>
    </Space>
  );
};
