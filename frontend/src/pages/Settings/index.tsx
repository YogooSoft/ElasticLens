import React from 'react';
import { Card, Form, Input, Button, message } from 'antd';
import { SaveOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

export const Settings: React.FC = () => {
  const { t } = useTranslation(['settings', 'common']);
  const [form] = Form.useForm();

  const handleSave = async (values: any) => {
    try {
      // TODO: 保存到后端
      console.log('保存配置:', values);
      message.success(t('saveSuccess'));
    } catch (error) {
      message.error(t('saveFailed'));
    }
  };

  return (
    <div>
      <h2>{t('title')}</h2>
      <Card title={t('apiConfig')} style={{ maxWidth: 600 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            apiUrl: import.meta.env.VITE_API_BASE_URL,
          }}
        >
          <Form.Item
            label={t('apiUrl')}
            name="apiUrl"
            rules={[{ required: true, message: t('apiUrlRequired') }]}
          >
            <Input disabled />
          </Form.Item>

          <Form.Item>
            <Button type="primary" htmlType="submit" icon={<SaveOutlined />}>
              {t('saveConfig')}
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
};
