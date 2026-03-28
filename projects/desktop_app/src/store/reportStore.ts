export interface ReportItem {
  report_id: string;
  report_type: string;
  title: string;
}

export interface ReportStoreState {
  reports: ReportItem[];
}

export const defaultReportStoreState: ReportStoreState = {
  reports: [],
};
