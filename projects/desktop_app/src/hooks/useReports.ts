import { useEffect, useState } from "react";

import { apiCall } from "../api/client";
import { defaultReportStoreState, type ReportStoreState } from "../store/reportStore";

export function useReports(): ReportStoreState {
  const [state, setState] = useState<ReportStoreState>(defaultReportStoreState);

  useEffect(() => {
    void apiCall<{ reports: { report_id: string; report_type: string; title: string }[] }>("/reports", "GET")
      .then((payload) => setState({ reports: payload.reports }))
      .catch(() => setState(defaultReportStoreState));
  }, []);

  return state;
}
