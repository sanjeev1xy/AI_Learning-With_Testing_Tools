export const STATUS_VALUES = ['Pending', 'Writing', 'Imaging', 'Done', 'Error'] as const;
export type StatusType = (typeof STATUS_VALUES)[number];

export interface ContentRow {
  date: string;          // YYYY-MM-DD
  topic: string;
  linkedinPost: string;
  mediumArticle: string;
  igScript: string;
  ytScript: string;
  devtoArticle: string;
  status: StatusType;
  linkedinImage: string; // /images/linkedin-YYYYMMDD.jpg
  mediumImage: string;
  igImage: string;
}

export interface PipelineState {
  running: boolean;
  step: string;
  startedAt: string | null;
  lastCompletedAt: string | null;
  error: string | null;
}

export interface StatusResponse extends PipelineState {
  nextRunAt: string;
  groqOk: boolean;
  geminiOk: boolean;
}
