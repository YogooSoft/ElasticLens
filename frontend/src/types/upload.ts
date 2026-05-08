export interface UploadResponse {
  code: number;
  message: string;
  data: {
    taskId: string;
    filename: string;
    status: 'pending' | 'processing' | 'completed' | 'failed';
  };
}
