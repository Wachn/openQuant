import { useEffect, useState } from "react";

import { apiCall } from "../api/client";
import { defaultPortfolioSummaryState, type PortfolioSummaryState } from "../store/portfolioStore";

export function usePortfolioSummary(): PortfolioSummaryState {
  const [state, setState] = useState<PortfolioSummaryState>(defaultPortfolioSummaryState);

  useEffect(() => {
    void apiCall<Record<string, unknown>>("/dashboard", "GET")
      .then((payload) => {
        const summary = payload.portfolio_summary as Record<string, unknown> | undefined;
        setState({
          equity: typeof summary?.equity === "number" ? summary.equity : 0,
          cash: typeof summary?.cash === "number" ? summary.cash : 0,
          dailyPnl: typeof summary?.daily_pnl === "number" ? summary.daily_pnl : 0,
          drawdown: typeof summary?.drawdown === "number" ? summary.drawdown : 0,
        });
      })
      .catch(() => setState(defaultPortfolioSummaryState));
  }, []);

  return state;
}
