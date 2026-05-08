import { create } from 'zustand';

interface UploadState {
  isUploading: boolean;
  uploadProgress: number;
  currentFile: File | null;
  
  setUploading: (isUploading: boolean) => void;
  setProgress: (progress: number) => void;
  setCurrentFile: (file: File | null) => void;
  reset: () => void;
}

export const useUploadStore = create<UploadState>((set) => ({
  isUploading: false,
  uploadProgress: 0,
  currentFile: null,
  
  setUploading: (isUploading) => set({ isUploading }),
  setProgress: (progress) => set({ uploadProgress: progress }),
  setCurrentFile: (file) => set({ currentFile: file }),
  reset: () => set({ isUploading: false, uploadProgress: 0, currentFile: null }),
}));
