import { create } from 'zustand';
import { ReportData } from '../types/report';

interface ReportState {
  currentReport: ReportData | null;
  isLoading: boolean;
  
  setCurrentReport: (report: ReportData | null) => void;
  setLoading: (isLoading: boolean) => void;
  reset: () => void;
}

export const useReportStore = create<ReportState>((set) => ({
  currentReport: null,
  isLoading: false,
  
  setCurrentReport: (report) => set({ currentReport: report }),
  setLoading: (isLoading) => set({ isLoading }),
  reset: () => set({ currentReport: null, isLoading: false }),
}));
