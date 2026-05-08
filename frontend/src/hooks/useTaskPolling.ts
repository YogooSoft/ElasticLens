import { useState, useEffect } from 'react';
import { fetchTasks } from '../api/task';
import type { Task } from '../types/task';

export const useTaskPolling = (interval: number = 3000) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const pollTasks = async () => {
      try {
        setLoading(true);
        const response = await fetchTasks();
        setTasks(response);
      } catch (error) {
        console.error('轮询任务失败:', error);
      } finally {
        setLoading(false);
      }
    };

    pollTasks();

    const taskId = setInterval(pollTasks, interval);

    return () => clearInterval(taskId);
  }, [interval]);

  return { tasks, loading };
};
