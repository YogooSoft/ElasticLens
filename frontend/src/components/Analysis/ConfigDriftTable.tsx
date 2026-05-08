import React from 'react';
import { Card, Table, Tag, Empty } from 'antd';
import { API_BASE_URL } from '../../api/index';

interface DriftData {
  parameter_name: string;
  expected_value: any;
  drifted_nodes: Array<{ node_name: string; actual_value: any }>;
  severity: string;
}

export const ConfigDriftTable: React.FC<{ reportId: string }> = ({ reportId }) => {
  const [drifts, setDrifts] = React.useState<DriftData[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch(`${API_BASE_URL}/reports/${reportId}/config-drift`)
      .then(res => res.json())
      .then(result => {
        setDrifts(result.data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('获取配置漂移数据失败:', err);
        setLoading(false);
      });
  }, [reportId]);

  if (!loading && drifts.length === 0) {
    return (
      <Card title="⚙️ 配置漂移检测">
        <Empty description="所有节点配置一致" />
      </Card>
    );
  }

  const columns = [
    {
      title: '配置参数',
      dataIndex: 'parameter_name',
      key: 'parameter_name',
      width: 300
    },
    {
      title: '期望值',
      dataIndex: 'expected_value',
      key: 'expected_value',
      width: 200,
      render: (value: any) => <code>{String(value)}</code>
    },
    {
      title: '严重程度',
      key: 'severity',
      width: 120,
      render: (_: any, record: DriftData) => (
        <Tag color={
          record.severity === 'critical' ? 'red' :
          record.severity === 'warning' ? 'orange' : 'blue'
        }>
          {record.severity.toUpperCase()}
        </Tag>
      )
    },
    {
      title: '不一致节点数',
      key: 'drifted_count',
      width: 120,
      render: (_: any, record: DriftData) => record.drifted_nodes.length
    }
  ];

  const expandedRowRender = (record: DriftData) => (
    <div style={{ padding: '0 48px' }}>
      <h4 style={{ marginBottom: 12 }}>不一致节点详情:</h4>
      <Table
        dataSource={record.drifted_nodes}
        rowKey="node_name"
        pagination={false}
        size="small"
        columns={[
          {
            title: '节点名称',
            dataIndex: 'node_name',
            key: 'node_name',
            width: 200
          },
          {
            title: '实际值',
            dataIndex: 'actual_value',
            key: 'actual_value',
            render: (value: any) => <code>{String(value)}</code>
          }
        ]}
      />
    </div>
  );

  return (
    <Card title="⚙️ 配置漂移检测">
      <Table
        columns={columns}
        dataSource={drifts}
        loading={loading}
        rowKey="parameter_name"
        expandable={{ expandedRowRender }}
        pagination={{ pageSize: 10 }}
      />
    </Card>
  );
};
