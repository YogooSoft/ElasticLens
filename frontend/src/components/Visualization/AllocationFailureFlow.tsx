import React from 'react';
import { Card, Steps, Alert } from 'antd';
import { API_BASE_URL } from '../../api/index';

const { Step } = Steps;

interface FailureData {
  index_name: string;
  shard_id: number;
  failure_reasons: string[];
  decision_path: Array<{ node: string; decider: string; reason: string }>;
}

export const AllocationFailureFlow: React.FC<{ reportId: string }> = ({ reportId }) => {
  const [failures, setFailures] = React.useState<FailureData[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch(`${API_BASE_URL}/reports/${reportId}/allocation-failures`)
      .then(res => res.json())
      .then(result => {
        setFailures(result.data || []);
        setLoading(false);
      })
      .catch(err => {
        console.error('获取分片分配失败数据失败:', err);
        setLoading(false);
      });
  }, [reportId]);

  if (!loading && failures.length === 0) {
    return (
      <Card title="✅ 分片分配状态">
        <Alert message="所有分片分配正常" type="success" showIcon />
      </Card>
    );
  }

  return (
    <Card title="❌ 分片分配失败分析" loading={loading}>
      {failures.map((failure, idx) => (
        <div key={idx} style={{ marginBottom: 24 }}>
          <h4 style={{ marginBottom: 12 }}>
            索引: {failure.index_name}, 分片: {failure.shard_id}
          </h4>
          
          <Alert
            message="失败原因"
            description={
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                {failure.failure_reasons.map((reason, i) => (
                  <li key={i}>{reason}</li>
                ))}
              </ul>
            }
            type="error"
            style={{ marginBottom: 16 }}
          />
          
          {failure.decision_path.length > 0 && (
            <>
              <h5 style={{ marginBottom: 8 }}>分配决策路径:</h5>
              <Steps direction="vertical" size="small">
                {failure.decision_path.map((step, i) => (
                  <Step
                    key={i}
                    status="error"
                    title={`节点: ${step.node}`}
                    description={
                      <div>
                        <p style={{ margin: '4px 0' }}>
                          <strong>决策器:</strong> {step.decider}
                        </p>
                        <p style={{ margin: '4px 0' }}>
                          <strong>原因:</strong> {step.reason}
                        </p>
                      </div>
                    }
                  />
                ))}
              </Steps>
            </>
          )}
          
          {idx < failures.length - 1 && (
            <div style={{ 
              borderTop: '1px solid #f0f0f0', 
              marginTop: 24, 
              paddingTop: 24 
            }} />
          )}
        </div>
      ))}
    </Card>
  );
};
