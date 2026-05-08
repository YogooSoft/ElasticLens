import React from 'react';
import { Card, Empty, Progress, Table } from 'antd';
import { API_BASE_URL } from '../../api/index';

interface HeatmapData {
  node_name: string;
  load_index: number;
  cpu_percent: number;
  disk_percent: number;
  shard_count: number;
}

export const ShardHeatmap: React.FC<{ reportId: string }> = ({ reportId }) => {
  const [data, setData] = React.useState<HeatmapData[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch(`${API_BASE_URL}/reports/${reportId}/shard-heatmap`)
      .then(res => res.json())
      .then(result => {
        setData(result.data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('获取热力图数据失败:', err);
        setLoading(false);
      });
  }, [reportId]);

  if (!loading && data.length === 0) {
    return (
      <Card title="🔥 分片分布热点">
        <Empty description="暂无分片数据" />
      </Card>
    );
  }

  // 按负载指数排序
  const sortedData = [...data].sort((a, b) => b.load_index - a.load_index);

  return (
    <Card title="🔥 分片分布热点">
      <Table
        dataSource={sortedData}
        loading={loading}
        rowKey="node_name"
        pagination={{ pageSize: 10 }}
        columns={[
          {
            title: '节点名称',
            dataIndex: 'node_name',
            key: 'node_name',
            width: 150
          },
          {
            title: '负载指数',
            key: 'load_index',
            width: 200,
            render: (_, record) => (
              <Progress
                percent={Math.round(record.load_index)}
                status={
                  record.load_index > 90 ? 'exception' :
                  record.load_index > 70 ? 'normal' : 'success'
                }
                strokeColor={
                  record.load_index > 90 ? '#ff4d4f' :
                  record.load_index > 70 ? '#faad14' : '#52c41a'
                }
              />
            )
          },
          {
            title: 'CPU使用率',
            key: 'cpu_percent',
            width: 150,
            render: (_, record) => (
              <Progress
                percent={Math.round(record.cpu_percent)}
                size="small"
                status={record.cpu_percent > 80 ? 'exception' : 'normal'}
              />
            )
          },
          {
            title: '磁盘使用率',
            key: 'disk_percent',
            width: 150,
            render: (_, record) => (
              <Progress
                percent={Math.round(record.disk_percent)}
                size="small"
                status={record.disk_percent > 85 ? 'exception' : 'normal'}
              />
            )
          },
          {
            title: '分片数',
            dataIndex: 'shard_count',
            key: 'shard_count',
            width: 100,
            sorter: (a, b) => a.shard_count - b.shard_count
          }
        ]}
      />
    </Card>
  );
};
