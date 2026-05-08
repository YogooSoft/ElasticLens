import axios from 'axios';
import type { AxiosInstance, AxiosResponse } from 'axios';
import { message } from 'antd';

// API 基础 URL（导出供前端组件使用）
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000/api/v1';

// 响应数据接口
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data?: T;
}

// 创建 Axios 实例
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 分钟超时（考虑到大文件上传）
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以添加认证 token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('请求错误:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    // 如果是 blob 类型，直接返回（如下载文件）
    if (response.config.responseType === 'blob') {
      return response;
    }
    
    const { code, message: msg } = response.data as ApiResponse;
    
    // 根据 code 判断是否成功
    if (code !== 200) {
      message.error(msg || '请求失败');
      return Promise.reject(new Error(msg));
    }
    
    return response.data;
  },
  (error) => {
    console.error('HTTP 错误:', error);
    
    // 处理常见 HTTP 错误
    if (error.response) {
      switch (error.response.status) {
        case 401:
          message.error('未授权，请登录');
          break;
        case 403:
          message.error('拒绝访问');
          break;
        case 404:
          message.error('请求的资源不存在');
          break;
        case 500:
          message.error('服务器内部错误');
          break;
        default:
          message.error(error.response.data?.message || '网络错误');
      }
    } else if (error.request) {
      message.error('网络异常，请检查网络连接');
    } else {
      message.error(error.message || '请求失败');
    }
    
    return Promise.reject(error);
  }
);

export default apiClient;
