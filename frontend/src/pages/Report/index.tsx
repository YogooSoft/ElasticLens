import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Spin, Alert } from 'antd';
import { ArrowLeftOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { API_BASE_URL } from '../../api/index';

export const ReportDetail: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const { t, i18n } = useTranslation(['report', 'common']);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // 获取当前语言并构建 iframe URL（支持多语言）
  const currentLang = i18n.language || 'zh-CN';
  const iframeUrl = `${API_BASE_URL}/reports/${reportId}/view?lang=${currentLang}`;

  const handleLoad = () => {
    setLoading(false);
  };

  const handleError = () => {
    setLoading(false);
    setError(t('loadError'));
  };

  if (error) {
    return (
      <div>
        <Button
          icon={<ArrowLeftOutlined />}
          onClick={() => navigate('/')}
          style={{ marginBottom: 16 }}
        >
          {t('backToHome')}
        </Button>
        <Alert
          message={t('loadFailed')}
          description={error}
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/')}
        style={{ marginBottom: 16 }}
      >
        {t('backToHome')}
      </Button>

      {loading && (
        <div style={{ textAlign: 'center', padding: 100 }}>
          <Spin size="large" tip={t('loadingReport')} />
        </div>
      )}

      {/* 使用 iframe 渲染完整的 HTML 报告 */}
      <iframe
        src={iframeUrl}
        title={t('reportTitle')}
        onLoad={handleLoad}
        onError={handleError}
        style={{
          width: '100%',
          height: 'calc(100vh - 80px)',
          border: 'none',
          display: loading ? 'none' : 'block',
        }}
      />

      <div style={{ marginTop: 20, textAlign: 'center', color: '#999', fontSize: 12 }}>
        <p>{t('common:app.copyright')}</p>
        <p>{t('common:app.version')}：v{import.meta.env.VITE_APP_VERSION || '1.0.0'}</p>
      </div>
    </div>
  );
};
