import React from 'react';
import { Card, Progress, Tag, Button, Space, Empty, message } from 'antd';
import { 
  CheckCircleOutlined,
  CloseCircleOutlined,
  LoadingOutlined,
  DeleteOutlined,
  EyeOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { useTranslation } from 'react-i18next';
import { useTaskStore } from '../../store/useTaskStore';
import { fetchTasks, deleteTask } from '../../api/task';
import { downloadReport } from '../../api/report';
import type { Task } from '../../types/task';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/zh-cn';
import 'dayjs/locale/en';
import { useNavigate } from 'react-router-dom';

dayjs.extend(relativeTime);
dayjs.locale('zh-cn');

export const TaskList: React.FC = () => {
  const { t, i18n } = useTranslation(['task', 'common']);
  const { tasks, setTasks, removeTask, updateTask } = useTaskStore();
  const navigate = useNavigate();
  const tasksRef = React.useRef(tasks);

  // 更新 ref
  React.useEffect(() => {
    tasksRef.current = tasks;
  }, [tasks]);

  // 根据i18n语言切换dayjs locale
  React.useEffect(() => {
    if (i18n.language === 'en-US') {
      dayjs.locale('en');
    } else {
      dayjs.locale('zh-cn');
    }
  }, [i18n.language]);

  // 轮询任务状态（每 3 秒）
  React.useEffect(() => {
    const pollTasks = async () => {
      try {
        const newTasks = await fetchTasks();
        
        // 更新现有任务状态
        newTasks.forEach((newTask: Task) => {
          const existingTask = tasksRef.current.find(t => t.id === newTask.id);
          if (!existingTask || existingTask.status !== newTask.status) {
            updateTask(newTask.id, newTask);
          }
        });
        
        setTasks(newTasks);
      } catch (error) {
        console.error(t('fetchTasksFailed'), error);
      }
    };

    pollTasks();
    
    const interval = setInterval(pollTasks, 3000);
    
    return () => clearInterval(interval);
  }, [setTasks, updateTask]);

  const handleDelete = async (taskId: string) => {
    try {
      await deleteTask(taskId);
      removeTask(taskId);
    } catch (error) {
      console.error(t('deleteTaskFailed'), error);
    }
  };

  const handleViewReport = (reportId: string) => {
    navigate(`/report/${reportId}`);
  };

  const handleDownloadWord = async (reportId: string, filename: string) => {
    try {
      message.loading({ content: t('generatingWord'), key: 'download', duration: 0 });
      
      const blob = await downloadReport(reportId, 'word');
      
      // 创建下载链接
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${filename.replace('.zip', '')}.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      message.success({ content: t('wordDownloadSuccess'), key: 'download' });
    } catch (error: any) {
      console.error(t('downloadFailed'), error);
      
      // 处理 Word 功能不可用的情况
      if (error.response?.status === 503) {
        message.error({
          content: t('wordFeatureUnavailable'),
          key: 'download',
          duration: 5,
        });
      } else {
        message.error({ 
          content: error.response?.data?.message || t('downloadFailed'), 
          key: 'download',
          duration: 3,
        });
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'processing': return 'processing';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleOutlined />;
      case 'failed': return <CloseCircleOutlined />;
      case 'processing': return <LoadingOutlined spin />;
      default: return null;
    }
  };

  if (tasks.length === 0) {
    return <Empty description={t('common:noTasks')} />;
  }

  return (
    <Space direction="vertical" style={{ width: '100%' }} size="middle">
      {tasks.map((task) => (
        <Card
          key={task.id}
          size="small"
          title={
            <Space>
              {getStatusIcon(task.status)}
              <span>{task.filename}</span>
            </Space>
          }
          extra={
            task.status === 'completed' || task.status === 'failed' ? (
              <Space>
                {task.status === 'completed' && task.result && (
                  <>
                    <Button
                      type="primary"
                      size="small"
                      icon={<EyeOutlined />}
                      onClick={() => handleViewReport(task.result!.reportId)}
                      style={{ fontSize: '12px' }}
                    >
                      {t('view')}
                    </Button>
                    <Button
                      type="default"
                      size="small"
                      icon={<DownloadOutlined />}
                      onClick={() => handleDownloadWord(task.result!.reportId, task.filename)}
                      style={{ fontSize: '12px' }}
                    >
                      {t('downloadWord')}
                    </Button>
                  </>
                )}
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => handleDelete(task.id)}
                />
              </Space>
            ) : null
          }
        >
          <div style={{ marginBottom: 8 }}>
            <Space>
              <Tag color={getStatusColor(task.status)}>
                {task.status === 'completed' && t('completed')}
                {task.status === 'failed' && t('failed')}
                {task.status === 'processing' && t('processing')}
                {task.status === 'pending' && t('pending')}
              </Tag>
              <span>{dayjs(task.updated_at).fromNow()}</span>
            </Space>
          </div>

          {(task.status === 'processing' || task.progress > 0) && (
            <Progress
              percent={task.progress}
              strokeColor={{
                '0%': '#667eea',
                '100%': '#764ba2',
              }}
            />
          )}

          {task.status === 'completed' && task.result && (
            <div style={{ marginTop: 8 }}>
              <Space size={[4, 4]} wrap>
                <Tag color="blue" style={{ margin: 0 }}>{t('healthScore')}: {task.result.healthScore}</Tag>
                <Tag color={task.result.alertCount > 0 ? "red" : "green"} style={{ margin: 0 }}>
                  {t('alertCount')}: {task.result.alertCount}
                </Tag>
                {task.result.level_1_count !== undefined && (
                  <Tag color="default" style={{ margin: 0 }}>
                    {t('level1Alerts')}: {task.result.level_1_count}
                  </Tag>
                )}
                {task.result.level_2_count !== undefined && (
                  <Tag color="warning" style={{ margin: 0 }}>
                    {t('level2Alerts')}: {task.result.level_2_count}
                  </Tag>
                )}
                {task.result.level_3_count !== undefined && (
                  <Tag color="error" style={{ margin: 0 }}>
                    {t('level3Alerts')}: {task.result.level_3_count}
                  </Tag>
                )}
              </Space>
            </div>
          )}

          {task.status === 'failed' && task.error && (
            <div style={{ marginTop: 8, color: '#dc3545', fontSize: 12 }}>
              {t('error')}：{task.error}
            </div>
          )}
        </Card>
      ))}
    </Space>
  );
};
