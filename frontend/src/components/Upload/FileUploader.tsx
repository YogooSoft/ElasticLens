import React, { useState } from 'react';
import { Upload, message, Progress, Typography } from 'antd';
import { InboxOutlined } from '@ant-design/icons';
import type { UploadProps } from 'antd';
import { useTranslation } from 'react-i18next';
import { uploadFile } from '../../api/upload';
import { useUploadStore } from '../../store/useUploadStore';
import { useTaskStore } from '../../store/useTaskStore';

const { Dragger } = Upload;
const { Text } = Typography;

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

interface FileUploaderProps {
  onUploadSuccess?: (taskId: string) => void;
}

export const FileUploader: React.FC<FileUploaderProps> = ({ onUploadSuccess }) => {
  const { t } = useTranslation(['upload', 'common']);
  const {
    isUploading,
    uploadProgress,
    currentFile,
    setUploading,
    setProgress,
    setCurrentFile,
    reset,
  } = useUploadStore();
  const { addTask } = useTaskStore();
  const [fileList, setFileList] = useState<any[]>([]);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: false,
    accept: '.zip',
    fileList,
    disabled: isUploading,
    beforeUpload: (file) => {
      if (!file.name.endsWith('.zip')) {
        message.error(t('common:onlyZipFiles'));
        return false;
      }

      const maxSize = 2 * 1024 * 1024 * 1024;
      if (file.size > maxSize) {
        message.error(t('common:fileSizeExceeded'));
        return false;
      }

      return true;
    },
    customRequest: async ({ file, onSuccess, onError }) => {
      const uploadFileObj = file as File;
      try {
        setCurrentFile(uploadFileObj);
        setUploading(true);
        setProgress(0);

        const response = await uploadFile(uploadFileObj, (percent) => {
          setProgress(percent);
        });

        setProgress(100);

        addTask({
          id: response.data.taskId,
          filename: response.data.filename,
          fileSize: uploadFileObj.size,
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

  const loadedBytes = currentFile
    ? Math.min(currentFile.size, Math.round((currentFile.size * uploadProgress) / 100))
    : 0;

  return (
    <div>
      <Dragger {...uploadProps}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">{t('dragText')}</p>
        <p className="ant-upload-hint">{t('hint')}</p>
      </Dragger>

      {isUploading && currentFile && (
        <div style={{ marginTop: 16 }}>
          <Text strong style={{ display: 'block', marginBottom: 8 }} ellipsis>
            {currentFile.name}
          </Text>
          <Text type="secondary" style={{ display: 'block', marginBottom: 8 }}>
            {t('uploading')} {t('uploadProgress', { percent: uploadProgress })}
          </Text>
          <Progress
            percent={uploadProgress}
            status="active"
            strokeColor={{
              '0%': '#667eea',
              '100%': '#764ba2',
            }}
          />
          <Text type="secondary" style={{ display: 'block', marginTop: 8, fontSize: 12 }}>
            {t('uploadSize', {
              loaded: formatFileSize(loadedBytes),
              total: formatFileSize(currentFile.size),
            })}
          </Text>
        </div>
      )}
    </div>
  );
};
