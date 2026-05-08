import { create } from 'zustand';
import { Task } from '../types/task';

interface TaskState {
  tasks: Task[];
  activeTaskId: string | null;
  
  setTasks: (tasks: Task[]) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  addTask: (task: Task) => void;
  removeTask: (taskId: string) => void;
  setActiveTask: (taskId: string | null) => void;
}

export const useTaskStore = create<TaskState>((set) => ({
  tasks: [],
  activeTaskId: null,
  
  setTasks: (tasks) => set({ tasks }),
  updateTask: (taskId, updates) =>
    set((state) => ({
      tasks: state.tasks.map((task) =>
        task.id === taskId ? { ...task, ...updates } : task
      ),
    })),
  addTask: (task) =>
    set((state) => ({ tasks: [...state.tasks, task] })),
  removeTask: (taskId) =>
    set((state) => ({
      tasks: state.tasks.filter((t) => t.id !== taskId),
    })),
  setActiveTask: (taskId) => set({ activeTaskId: taskId }),
}));
