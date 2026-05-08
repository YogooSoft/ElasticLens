import { useState, useEffect } from 'react';
import { fetchReport } from '../api/report';
import type { ReportData } from '../types/report';

export const useReport = (reportId: string) => {
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadReport = async () => {
      try {
        setLoading(true);
        const result = await fetchReport(reportId);
        setData(result);
        setError(null);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (reportId) {
      loadReport();
    }
  }, [reportId]);

  return { data, loading, error };
};
