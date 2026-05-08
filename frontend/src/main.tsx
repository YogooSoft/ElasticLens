import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import enUS from 'antd/locale/en_US';
import App from './App';
import './index.css';
import './i18n'; // 引入i18n配置
import { useTranslation } from 'react-i18next';

// 创建带国际化的根组件
const RootWithI18n: React.FC = () => {
  const { i18n } = useTranslation();
  
  // 根据当前语言选择Ant Design的语言包
  const antdLocale = i18n.language === 'en-US' ? enUS : zhCN;

  return (
    <ConfigProvider locale={antdLocale}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </ConfigProvider>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <RootWithI18n />
  </React.StrictMode>,
);
