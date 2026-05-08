import React from 'react';
import { Card, Table, Tag, Empty } from 'antd';
import type { ColumnsType } from 'antd/es/table';
import { API_BASE_URL } from '../../api/index';

interface ThreadPoolData {
  node_name: string;
  pool_name: string;
  queue_size: number;
  rejected_count: number;
  active_threads: number;
  completed_tasks: number;
  is_overloaded: boolean;
}

export const ThreadPoolAlert: React.FC<{ reportId: string }> = ({ reportId }) => {
  const [data, setData] = React.useState<ThreadPoolData[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch(`${API_BASE_URL}/reports/${reportId}/thread-pools`)
      .then(res => res.json())
      .then(result => {
        setData(result.data?.critical_pools || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('获取线程池数据失败:', err);
        setLoading(false);
      });
  }, [reportId]);

  const columns: ColumnsType<ThreadPoolData> = [
    { 
      title: '节点名称', 
      dataIndex: 'node_name', 
      key: 'node_name',
      width: 150
    },
    { 
      title: '线程池', 
      dataIndex: 'pool_name', 
      key: 'pool_name',
      width: 120
    },
    { 
      title: '队列大小', 
      dataIndex: 'queue_size', 
      key: 'queue_size',
      width: 100,
      sorter: (a, b) => a.queue_size - b.queue_size
    },
    { 
      title: '拒绝数', 
      dataIndex: 'rejected_count', 
      key: 'rejected_count',
      width: 100,
      render: (count: number) => (
        <Tag color={count > 0 ? 'red' : 'green'}>{count}</Tag>
      ),
      sorter: (a, b) => a.rejected_count - b.rejected_count
    },
    {
      title: '活跃线程',
      dataIndex: 'active_threads',
      key: 'active_threads',
      width: 100
    },
    {
      title: '状态',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <Tag color={record.is_overloaded ? 'red' : 'green'}>
          {record.is_overloaded ? '过载' : '正常'}
        </Tag>
      )
    }
  ];

  if (!loading && data.length === 0) {
    return (
      <Card title="⚠️ 线程池队列堆积告警">
        <Empty description="所有线程池运行正常" />
      </Card>
    );
  }

  return (
    <Card title="⚠️ 线程池队列堆积告警">
      <Table 
        columns={columns} 
        dataSource={data} 
        loading={loading}
        rowKey={(record) => `${record.node_name}_${record.pool_name}`}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};
