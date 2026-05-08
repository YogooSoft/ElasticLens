import apiClient from './index';
import type { Task } from '../types/task';

export type { Task };

/**
 * 获取所有任务列表
 * 后端返回: { code: 200, data: Task[] }
 * 拦截器返回 response.data → { code: 200, data: Task[] }
 * 所以 response.data 就是任务数组
 */
export const fetchTasks = async (): Promise<Task[]> => {
  const response: any = await apiClient.get('/tasks');
  return response.data || [];
};

/**
 * 获取单个任务详情
 * @param taskId 任务 ID
 */
export const fetchTaskDetail = async (taskId: string): Promise<any> => {
  return apiClient.get(`/tasks/${taskId}`);
};

/**
 * 删除任务
 * @param taskId 任务 ID
 */
export const deleteTask = async (taskId: string): Promise<any> => {
  return apiClient.delete(`/tasks/${taskId}`);
};
