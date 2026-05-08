import React, { useState } from 'react';
import { Upload, message } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { useTranslation } from 'react-i18next';
import { uploadFile } from '../../api/upload';
import { useUploadStore } from '../../store/useUploadStore';
import { useTaskStore } from '../../store/useTaskStore';

const { Dragger } = Upload;

interface FileUploaderProps {
  onUploadSuccess?: (taskId: string) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUploadSuccess }) => {
  const { t } = useTranslation(['upload', 'common']);
  const { setUploading, setProgress, reset } = useUploadStore();
  const { addTask } = useTaskStore();
  const [fileList, setFileList] = useState<any[]>([]);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.zip',
    fileList,
    beforeUpload: (file) => {
      // 校验文件类型
      if (!file.name.endsWith('.zip')) {
        message.error(t('common:onlyZipFiles'));
        return false;
      }
      
      // 校验文件大小（最大 2GB）
      const maxSize = 2 * 1024 * 1024 * 1024;
      if (file.size > maxSize) {
        message.error(t('common:fileSizeExceeded'));
        return false;
      }
      
      return true;
    },
    customRequest: async ({ file, onSuccess, onError }) => {
      try {
        setUploading(true);
        
        const response = await uploadFile(file as File, (percent) => {
          setProgress(percent);
        });
        
        // 添加到任务列表
        addTask({
          id: response.data.taskId,
          filename: response.data.filename,
          fileSize: (file as File).size,
          status: response.data.status,
          progress: 0,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
        
        message.success(t('uploadSuccess'));
        onUploadSuccess?.(response.data.taskId);
        onSuccess?.(response);
        reset();
      } catch (error: any) {
        message.error(`${t('common:uploadFailed')}：${error.message}`);
        onError?.(error);
        reset();
      }
    },
    onRemove: () => {
      setFileList([]);
      return true;
    },
  };

  return (
    <Dragger {...uploadProps}>
      <p className="ant-upload-drag-icon">
        <InboxOutlined />
      </p>
      <p className="ant-upload-text">{t('dragText')}</p>
      <p className="ant-upload-hint">
        {t('hint')}
      </p>
    </Dragger>
  );
};
