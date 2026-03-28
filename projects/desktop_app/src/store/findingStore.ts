export interface FindingItem {
  finding_id: string;
  severity: string;
  status: string;
  title: string;
}

export interface FindingStoreState {
  findings: FindingItem[];
}

export const defaultFindingStoreState: FindingStoreState = {
  findings: [],
};
