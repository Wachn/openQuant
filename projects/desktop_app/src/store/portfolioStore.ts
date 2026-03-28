export interface PortfolioSummaryState {
  equity: number;
  cash: number;
  dailyPnl: number;
  drawdown: number;
}

export const defaultPortfolioSummaryState: PortfolioSummaryState = {
  equity: 0,
  cash: 0,
  dailyPnl: 0,
  drawdown: 0,
};
