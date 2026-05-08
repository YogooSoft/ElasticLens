import apiClient from './index';
import type { ReportData, ReportResponse } from '../types/report';

/**
 * 获取报告详情
 * @param reportId 报告 ID
 */
export const fetchReport = async (reportId: string): Promise<ReportData> => {
  const response = await apiClient.get<ReportResponse>(`/reports/${reportId}`);
  return (response as unknown as ReportResponse).data;
};

/**
 * 获取报告 HTML 内容
 * @param reportId 报告 ID
 */
export const fetchReportHtml = async (reportId: string): Promise<any> => {
  const response = await apiClient.get(`/reports/${reportId}/html`);
  return response.data;
};

/**
 * 下载报告（支持 HTML、JSON、Word）
 * @param reportId 报告 ID
 * @param format 格式类型：'html' | 'json' | 'word'，默认为 'html'
 */
export const downloadReport = async (
  reportId: string,
  format: 'html' | 'json' | 'word' = 'html'
): Promise<Blob> => {
  // 从localStorage获取当前语言
  const currentLang = localStorage.getItem('i18nextLng') || 'zh-CN';
  
  const response = await apiClient.get(`/reports/${reportId}/download`, {
    params: { 
      format,
      lang: currentLang  // 新增：传递语言参数
    },
    responseType: 'blob',
  });
  
  // 检查返回的 blob 是否为错误 JSON 响应
  const blob = response.data as Blob;
  if (blob.type === 'application/json') {
    const text = await blob.text();
    const errorData = JSON.parse(text);
    throw new Error(errorData.message || '下载报告失败');
  }
  
  return blob;
};
