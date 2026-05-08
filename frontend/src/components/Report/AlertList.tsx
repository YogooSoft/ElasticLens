import React from 'react';
import { Table, Tag, Typography } from 'antd';
import type { ColumnsType } from 'antd/es/table';

const { Text } = Typography;

interface Alert {
  level: string;
  message: string;
  timestamp?: string;
  node?: string;
}

interface AlertListProps {
  criticalAlerts: Alert[];
  warningAlerts: Alert[];
}

export const AlertList: React.FC<AlertListProps> = ({ criticalAlerts, warningAlerts }) => {
  const columns: ColumnsType<Alert> = [
    {
      title: '级别',
      dataIndex: 'level',
      key: 'level',
      render: (level: string) => (
        <Tag color={level === 'critical' ? 'red' : 'orange'}>
          {level === 'critical' ? '严重' : '警告'}
        </Tag>
      ),
    },
    {
      title: '告警信息',
      dataIndex: 'message',
      key: 'message',
      render: (text: string) => <Text>{text}</Text>,
    },
    {
      title: '节点',
      dataIndex: 'node',
      key: 'node',
    },
    {
      title: '时间',
      dataIndex: 'timestamp',
      key: 'timestamp',
    },
  ];

  const allAlerts = [...criticalAlerts, ...warningAlerts];

  return (
    <div>
      <h3>告警列表</h3>
      {allAlerts.length === 0 ? (
        <p>暂无告警</p>
      ) : (
        <Table
          columns={columns}
          dataSource={allAlerts}
          rowKey={(record, index) => `${record.level}-${index}`}
          pagination={false}
          size="small"
        />
      )}
    </div>
  );
};
