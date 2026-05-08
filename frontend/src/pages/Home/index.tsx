import React from 'react';
import { Row, Col, Card, Typography, Divider, Button } from 'antd';
import { useTranslation } from 'react-i18next';
import { FileUploader } from '../../components/Upload/FileUploader';
import { TaskList } from '../../components/Task/TaskList';
import { LanguageSwitcher } from '../../components/LanguageSwitcher';

const { Title, Text } = Typography;

export const Home: React.FC = () => {
  const { t } = useTranslation(['home', 'common']);

  const handleUploadSuccess = (taskId: string) => {
    console.log('上传成功，任务 ID:', taskId);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Title level={2} style={{ margin: 0 }}>{t('title')}</Title>
          <Text type="secondary">
            {t('subtitle')}
          </Text>
        </div>
        <LanguageSwitcher />
      </div>

      <Divider />

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title={t('uploadSection.title')}>
            <FileUploader onUploadSuccess={handleUploadSuccess} />
          </Card>

          <Card title={t('downloadToolSection.title')} style={{ marginTop: 16 }}>
            <p>{t('downloadToolSection.description')}</p>
            <Button type="primary" href="/tools/diagnostics-9.1.0-dist.zip" download>
              {t('downloadToolSection.downloadButton')}
            </Button>
          </Card>

          <Card title={t('usageGuideSection.title')} style={{ marginTop: 16 }}>
            <div style={{ lineHeight: '1.8' }}>
              <p><strong>{t('usageGuideSection.step1.title')}：</strong>{t('usageGuideSection.step1.content')}</p>
              <p><strong>{t('usageGuideSection.step2.title')}：</strong>{t('usageGuideSection.step2.content')}</p>
              <p><strong>{t('usageGuideSection.step3.title')}：</strong>{t('usageGuideSection.step3.content')}</p>
              <pre style={{ background: '#f5f5f5', padding: '10px', borderRadius: '4px', fontSize: '12px', overflowX: 'auto' }}>
{t('usageGuideSection.command')}
              </pre>
              <p><strong>{t('usageGuideSection.step4.title')}：</strong>{t('usageGuideSection.step4.content')}</p>
            </div>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card title={t('taskListSection.title')}>
            <TaskList />
          </Card>
        </Col>
      </Row>

      <div style={{ marginTop: 40, textAlign: 'center', color: '#999', fontSize: 12 }}>
        <p>{t('common:app.copyright')}</p>
        <p>{t('common:app.version')}：v{import.meta.env.VITE_APP_VERSION || '1.0.0'}</p>
      </div>
    </div>
  );
};
