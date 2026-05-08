import React from 'react';
import { Card, Empty, Progress, Table } from 'antd';
import { API_BASE_URL } from '../../api/index';

interface JVMMemoryData {
  node_name: string;
  heap_used_bytes: number;
  heap_max_bytes: number;
  heap_used_percent: number;
  old_gen_bytes: number;
  young_gen_bytes: number;
  fielddata_bytes: number;
  segments_bytes: number;
  non_heap_bytes: number;
}

// 格式化字节数
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const JVMMemoryChart: React.FC<{ reportId: string }> = ({ reportId }) => {
  const [data, setData] = React.useState<JVMMemoryData[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch(`${API_BASE_URL}/reports/${reportId}/jvm-profile`)
      .then(res => res.json())
      .then(result => {
        setData(result.data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('获取JVM内存数据失败:', err);
        setLoading(false);
      });
  }, [reportId]);

  if (!loading && data.length === 0) {
    return (
      <Card title="💾 JVM 内存画像">
        <Empty description="暂无JVM内存数据" />
      </Card>
    );
  }

  // 所有节点的堆使用率表格
  const columns = [
    {
      title: '节点名称',
      dataIndex: 'node_name',
      key: 'node_name',
      width: 150
    },
    {
      title: '堆使用率',
      key: 'heap_used_percent',
      width: 200,
      render: (_: any, record: JVMMemoryData) => (
        <Progress
          percent={Math.round(record.heap_used_percent)}
          status={
            record.heap_used_percent > 85 ? 'exception' :
            record.heap_used_percent > 75 ? 'normal' : 'success'
          }
          strokeColor={
            record.heap_used_percent > 85 ? '#ff4d4f' :
            record.heap_used_percent > 75 ? '#faad14' : '#52c41a'
          }
        />
      )
    },
    {
      title: '已用堆内存',
      key: 'heap_used',
      width: 120,
      render: (_: any, record: JVMMemoryData) => formatBytes(record.heap_used_bytes)
    },
    {
      title: '最大堆内存',
      key: 'heap_max',
      width: 120,
      render: (_: any, record: JVMMemoryData) => formatBytes(record.heap_max_bytes)
    },
    {
      title: 'Old Gen',
      key: 'old_gen',
      width: 120,
      render: (_: any, record: JVMMemoryData) => formatBytes(record.old_gen_bytes)
    },
    {
      title: 'Young Gen',
      key: 'young_gen',
      width: 120,
      render: (_: any, record: JVMMemoryData) => formatBytes(record.young_gen_bytes)
    },
    {
      title: 'Fielddata',
      key: 'fielddata',
      width: 120,
      render: (_: any, record: JVMMemoryData) => formatBytes(record.fielddata_bytes)
    },
    {
      title: 'Segments',
      key: 'segments',
      width: 120,
      render: (_: any, record: JVMMemoryData) => formatBytes(record.segments_bytes)
    }
  ];

  return (
    <Card title="💾 JVM 内存画像">
      <Table
        dataSource={data}
        loading={loading}
        rowKey="node_name"
        columns={columns}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};
