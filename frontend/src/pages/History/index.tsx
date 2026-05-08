import React, { useState, useEffect } from 'react';
import { Table, Button, Tag, Typography } from 'antd';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { fetchTasks } from '../../api/task';
import type { Task } from '../../types/task';
import dayjs from 'dayjs';

const { Title } = Typography;

export const History: React.FC = () => {
  const navigate = useNavigate();
  const { t } = useTranslation(['history', 'common']);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      setLoading(true);
      const response = await fetchTasks();
      setTasks(response.filter((t: Task) => t.status === 'completed'));
    } catch (error) {
      console.error(t('loadHistoryFailed'), error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    {
      title: t('filename'),
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: t('healthScore'),
      dataIndex: ['result', 'healthScore'],
      key: 'healthScore',
      render: (score: number) => (
        <Tag color={score >= 90 ? 'green' : score >= 70 ? 'orange' : 'red'}>
          {score}
        </Tag>
      ),
    },
    {
      title: t('alertCount'),
      dataIndex: ['result', 'alertCount'],
      key: 'alertCount',
    },
    {
      title: t('completedTime'),
      dataIndex: 'updated_at',
      key: 'updated_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: t('action'),
      key: 'action',
      render: (_: any, record: Task) => (
        <Button
          type="link"
          onClick={() => navigate(`/report/${record.result?.reportId}`)}
        >
          {t('viewDetail')}
        </Button>
      ),
    },
  ];

  return (
    <div>
      <Title level={2}>{t('title')}</Title>
      <Table
        columns={columns}
        dataSource={tasks}
        rowKey="id"
        loading={loading}
        pagination={{ pageSize: 10 }}
      />
    </div>
  );
};
