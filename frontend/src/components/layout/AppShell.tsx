import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Space, Typography, Tag } from 'antd';
import {
  DashboardOutlined,
  LineChartOutlined,
  DatabaseOutlined,
  UserOutlined,
  LogoutOutlined,
  MedicineBoxOutlined,
  AlertOutlined,
  TeamOutlined,
  DollarOutlined,
  FieldTimeOutlined,
  SafetyCertificateOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import apiClient from '../../services/apiClient';
import { ENDPOINTS } from '../../config/api';

const { Header, Sider, Content } = Layout;
const { Text, Title } = Typography;

interface UserProfile {
  full_name: string;
  role: string;
  email: string;
  department?: string;
}

export const AppShell: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    apiClient.get(ENDPOINTS.AUTH.ME)
      .then(res => setUser(res.data))
      .catch(() => navigate('/login'));
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    navigate('/login');
  };

  const userMenuItems = [
    {
      key: 'profile',
      label: (
        <div style={{ padding: '4px 8px' }}>
          <Text strong>{user?.full_name}</Text><br/>
          <Text type="secondary" style={{ fontSize: 12 }}>{user?.email}</Text><br/>
          <Tag color="blue" style={{ marginTop: 4 }}>{user?.role?.toUpperCase()}</Tag>
        </div>
      ),
    },
    { type: 'divider' as const },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Sign Out',
      onClick: handleLogout,
    },
  ];

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Command Center',
      onClick: () => navigate('/dashboard'),
    },
    {
      key: 'operational-analytics',
      icon: <TeamOutlined />,
      label: 'Operational Analytics',
      children: [
        {
          key: '/analytics/staffing',
          icon: <TeamOutlined />,
          label: 'Staffing Intelligence',
          onClick: () => navigate('/analytics/staffing'),
        },
        {
          key: '/analytics/financial',
          icon: <DollarOutlined />,
          label: 'Financial Analytics',
          onClick: () => navigate('/analytics/financial'),
        },
        {
          key: '/analytics/ed-flow',
          icon: <FieldTimeOutlined />,
          label: 'ED Flow Analytics',
          onClick: () => navigate('/analytics/ed-flow'),
        },
        {
          key: '/analytics/quality',
          icon: <SafetyCertificateOutlined />,
          label: 'Quality & Clinical Safety',
          onClick: () => navigate('/analytics/quality'),
        },
      ],
    },
    {
      key: 'predictions',
      icon: <LineChartOutlined />,
      label: 'Predictive Intelligence & MLOps',
      children: [
        {
          key: '/predictions/demand',
          label: 'Patient Demand Forecast',
          onClick: () => navigate('/predictions/demand'),
        },
        {
          key: '/predictions/bed-occupancy',
          label: 'Bed Occupancy Forecast',
          onClick: () => navigate('/predictions/bed-occupancy'),
        },
        {
          key: '/predictions/ed-wait-time',
          label: 'ED Wait Time Prediction',
          onClick: () => navigate('/predictions/ed-wait-time'),
        },
        {
          key: '/predictions/readmission-risk',
          label: 'Readmission Risk Calculator',
          onClick: () => navigate('/predictions/readmission-risk'),
        },
        {
          key: '/predictions/registry',
          label: 'Enterprise Model Registry',
          onClick: () => navigate('/predictions/registry'),
        },
        {
          key: '/predictions/monitoring',
          label: 'Model Monitoring & Data Drift',
          onClick: () => navigate('/predictions/monitoring'),
        },
      ],
    },
    {
      key: 'decisions-intelligence',
      icon: <SafetyCertificateOutlined />,
      label: 'Decision Intelligence',
      children: [
        {
          key: '/decisions/executive',
          label: 'Executive Decision Center',
          onClick: () => navigate('/decisions/executive'),
        },
        {
          key: '/decisions/simulator',
          label: 'Scenario Simulator',
          onClick: () => navigate('/decisions/simulator'),
        },
        {
          key: '/decisions/history',
          label: 'Decision History & Audit',
          onClick: () => navigate('/decisions/history'),
        },
      ],
    },
    {
      key: '/alerts',
      icon: <AlertOutlined />,
      label: 'Proactive Alert Center',
      onClick: () => navigate('/alerts'),
    },
    {
      key: '/data',
      icon: <DatabaseOutlined />,
      label: 'Dataset & Data Health',
      onClick: () => navigate('/data'),
    },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={value => setCollapsed(value)} theme="dark" width={250}>
        <div style={{ padding: 16, display: 'flex', alignItems: 'center', gap: 12, background: '#001529' }}>
          <MedicineBoxOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          {!collapsed && (
            <Title level={4} style={{ color: '#fff', margin: 0, fontSize: 16, fontWeight: 700 }}>
              HDIP Enterprise
            </Title>
          )}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #f0f0f0' }}>
          <div>
            <Text strong style={{ fontSize: 16 }}>Hospital Decision Intelligence Platform</Text>
            <Tag color="purple" style={{ marginLeft: 12 }}>Phase 4 Decision Intelligence Engine</Tag>
          </div>
          <Space size="large">
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#1890ff' }} />
                <Text strong>{user?.full_name || 'Admin User'}</Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: '24px 24px', minHeight: 280 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};
