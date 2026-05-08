import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import { Home } from './pages/Home';
import { ReportDetail } from './pages/Report';
import { History } from './pages/History';
import { Settings } from './pages/Settings';

const { Content } = Layout;

const App: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ padding: '24px', background: '#fff' }}>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/report/:reportId" element={<ReportDetail />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Content>
    </Layout>
  );
};

export default App;
