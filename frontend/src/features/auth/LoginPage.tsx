import React, { useState } from 'react';
import { Card, Form, Input, Button, Typography, Alert, Space, Tag } from 'antd';
import { UserOutlined, LockOutlined, MedicineBoxOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../services/apiClient';
import { ENDPOINTS } from '../../config/api';

const { Title, Text } = Typography;

export const LoginPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const onFinish = async (values: any) => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.post(ENDPOINTS.AUTH.LOGIN, values);
      localStorage.setItem('access_token', res.data.access_token);
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      background: 'linear-[#0f172a], #1e293b',
      backgroundColor: '#0f172a',
      padding: 16
    }}>
      <Card style={{ width: 420, borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)' }}>
        <div style={{ textAlign: 'center', marginBottom: 24 }}>
          <MedicineBoxOutlined style={{ fontSize: 42, color: '#2563eb' }} />
          <Title level={3} style={{ margin: '12px 0 4px 0' }}>Hospital Intelligence Platform</Title>
          <Text type="secondary">AI-Powered Decision Intelligence Platform</Text>
        </div>

        {error && <Alert message={error} type="error" showIcon style={{ marginBottom: 16 }} />}

        <Form name="login" onFinish={onFinish} layout="vertical" initialValues={{ email: 'admin@hospital.org', password: 'admin123' }}>
          <Form.Item name="email" rules={[{ required: true, message: 'Please input email!' }]}>
            <Input prefix={<UserOutlined />} placeholder="Email Address" size="large" />
          </Form.Item>

          <Form.Item name="password" rules={[{ required: true, message: 'Please input password!' }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="Password" size="large" />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" size="large" block loading={loading} style={{ background: '#2563eb' }}>
              Sign In to HDIP Platform
            </Button>
          </Form.Item>
        </Form>

        <div style={{ textAlign: 'center', background: '#f8fafc', padding: 12, borderRadius: 8 }}>
          <Text type="secondary" style={{ fontSize: 12 }}>Demo Account Credentials:</Text><br/>
          <Tag color="blue">admin@hospital.org / admin123</Tag>
        </div>
      </Card>
    </div>
  );
};
