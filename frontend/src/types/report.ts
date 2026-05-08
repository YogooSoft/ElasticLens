export interface ReportData {
  id: string;
  clusterName: string;
  healthScore: number;
  basicInfo: {
    clusterInfo: any;
    healthSummary: any;
    nodeSummary: any;
    indexSummary: any;
  };
  alerts: {
    summary: any;
    criticalAlerts: any[];
    warningAlerts: any[];
  };
  checkResults: {
    clusterHealth: any;
    nodeResources: any;
    indexHealth: any;
    threadPools: any;
    shards: any;
    ilm: any;
    snapshot: any;
    security: any;
  };
}

export interface ReportResponse {
  code: number;
  data: ReportData;
}
