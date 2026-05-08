export interface Task {
  id: string;
  filename: string;
  fileSize: number;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  created_at: string;
  updated_at: string;
  result?: {
    reportId: string;
    healthScore: number;
    alertCount: number;
    criticalCount?: number;
    warningCount?: number;
    level_1_count?: number;
    level_2_count?: number;
    level_3_count?: number;
  };
  error?: string;
}

export interface TaskListResponse {
  code: number;
  data: Task[];
}
