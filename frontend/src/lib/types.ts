export interface Job {
  id: string;
  stream_name: string;
  stream_date: string;
  status: JobStatus;
  current_step?: string;
  progress: number;
  error_message?: string;
  original_duration?: number;
  final_duration?: number;
  silence_removed?: number;
  output_folder_id?: string;
  chapters_count?: number;
  chapters_data?: Chapter[];
  title_ideas?: string[];
  thumbnail_concepts?: string[];
  tags?: string[];
  word_count?: number;
  language_breakdown?: Record<string, number>;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

export type JobStatus =
  | 'pending'
  | 'downloading'
  | 'extracting_audio'
  | 'transcribing'
  | 'detecting_silence'
  | 'analyzing'
  | 'generating_xml'
  | 'uploading'
  | 'completed'
  | 'failed';

export interface Chapter {
  title: string;
  start_time: number;
  end_time: number;
  summary?: string;
}

export interface JobsResponse {
  jobs: Job[];
  total: number;
  limit: number;
  offset: number;
}

export interface CurrentJobResponse {
  job: Job | null;
}

export const STEP_LABELS: Record<string, string> = {
  pending: 'Waiting to start',
  downloading: 'Downloading from Google Drive',
  extracting_audio: 'Extracting audio track',
  transcribing: 'Transcribing audio (Return Zero)',
  detecting_silence: 'Detecting silence segments',
  analyzing: 'Analyzing content (Claude AI)',
  generating_xml: 'Generating Premiere timeline',
  uploading: 'Uploading to Google Drive',
  completed: 'Completed',
  failed: 'Failed',
};

export const STEP_ORDER: JobStatus[] = [
  'pending',
  'downloading',
  'extracting_audio',
  'transcribing',
  'detecting_silence',
  'analyzing',
  'generating_xml',
  'uploading',
  'completed',
];
