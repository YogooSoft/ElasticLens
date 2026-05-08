import apiClient from './index';
import type { UploadResponse } from '../types/upload';

/**
 * 上传文件
 * @param file 要上传的文件
 * @param onProgress 进度回调函数
 */
export const uploadFile = async (
  file: File,
  onProgress?: (percent: number) => void
): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percent);
      }
    },
  });

  return response as unknown as UploadResponse;
};
