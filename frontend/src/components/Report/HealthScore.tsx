import React from 'react';
import { Card, Statistic } from 'antd';

interface HealthScoreProps {
  score: number;
}

export const HealthScore: React.FC<HealthScoreProps> = ({ score }) => {
  const getScoreColor = (score: number) => {
    if (score >= 90) return '#28a745';
    if (score >= 70) return '#ffc107';
    return '#dc3545';
  };

  const getHealthLevel = (score: number) => {
    if (score >= 90) return '健康';
    if (score >= 70) return '亚健康';
    return '不健康';
  };

  return (
    <Card bordered={false} style={{ textAlign: 'center' }}>
      <div style={{ position: 'relative', display: 'inline-block' }}>
        <svg width="200" height="200">
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke="#e0e0e0"
            strokeWidth="20"
          />
          <circle
            cx="100"
            cy="100"
            r="90"
            fill="none"
            stroke={getScoreColor(score)}
            strokeWidth="20"
            strokeDasharray={`${score * 5.65}, 565`}
            transform="rotate(-90 100 100)"
            style={{ transition: 'stroke-dasharray 1s ease' }}
          />
        </svg>
        <div
          style={{
            position: 'absolute',
            top: '50%',
            left: '50%',
            transform: 'translate(-50%, -50%)',
          }}
        >
          <div style={{ fontSize: 48, fontWeight: 'bold', color: getScoreColor(score) }}>
            {score}
          </div>
          <div style={{ fontSize: 16, color: '#666' }}>健康评分</div>
        </div>
      </div>
      
      <div style={{ marginTop: 24 }}>
        <Statistic
          title="健康等级"
          value={getHealthLevel(score)}
          valueStyle={{ color: getScoreColor(score) }}
        />
      </div>
    </Card>
  );
};
