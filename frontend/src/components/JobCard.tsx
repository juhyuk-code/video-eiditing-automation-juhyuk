'use client';

import { Job, STEP_LABELS } from '@/lib/types';
import { StatusBadge } from './StatusBadge';
import { ProgressBar } from './ProgressBar';

interface JobCardProps {
  job: Job;
  isExpanded?: boolean;
  onToggle?: () => void;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`;
  }
  if (minutes > 0) {
    return `${minutes}m ${secs}s`;
  }
  return `${secs}s`;
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleString();
}

export function JobCard({ job, isExpanded, onToggle }: JobCardProps) {
  const isProcessing = !['completed', 'failed', 'pending'].includes(job.status);

  return (
    <div
      className={`bg-white dark:bg-gray-800 rounded-lg shadow-md overflow-hidden transition-all duration-200 ${
        isProcessing ? 'ring-2 ring-blue-500 ring-opacity-50' : ''
      }`}
    >
      {/* Header */}
      <div
        className="p-4 cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-700"
        onClick={onToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">
              {job.status === 'completed' ? '✅' : job.status === 'failed' ? '❌' : '🎬'}
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white">
                {job.stream_name || job.stream_date}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {formatDate(job.created_at)}
              </p>
            </div>
          </div>
          <StatusBadge status={job.status} />
        </div>

        {/* Progress bar for active jobs */}
        {isProcessing && (
          <div className="mt-3">
            <ProgressBar status={job.status} progress={job.progress} />
          </div>
        )}
      </div>

      {/* Expanded details */}
      {isExpanded && (
        <div className="px-4 pb-4 border-t border-gray-100 dark:border-gray-700">
          <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
            {/* Duration info */}
            {job.original_duration && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Original:</span>
                <span className="ml-2 font-medium dark:text-white">
                  {formatDuration(job.original_duration)}
                </span>
              </div>
            )}
            {job.final_duration && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Final:</span>
                <span className="ml-2 font-medium dark:text-white">
                  {formatDuration(job.final_duration)}
                </span>
              </div>
            )}
            {job.silence_removed && job.silence_removed > 0 && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Silence removed:</span>
                <span className="ml-2 font-medium text-green-600 dark:text-green-400">
                  {formatDuration(job.silence_removed)}
                </span>
              </div>
            )}
            {job.chapters_count && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Chapters:</span>
                <span className="ml-2 font-medium dark:text-white">{job.chapters_count}</span>
              </div>
            )}
            {job.word_count && (
              <div>
                <span className="text-gray-500 dark:text-gray-400">Words:</span>
                <span className="ml-2 font-medium dark:text-white">
                  {job.word_count.toLocaleString()}
                </span>
              </div>
            )}
          </div>

          {/* Error message */}
          {job.error_message && (
            <div className="mt-4 p-3 bg-red-50 dark:bg-red-900/30 rounded-md">
              <p className="text-sm text-red-700 dark:text-red-300">{job.error_message}</p>
            </div>
          )}

          {/* Output link */}
          {job.output_folder_id && (
            <div className="mt-4">
              <a
                href={`https://drive.google.com/drive/folders/${job.output_folder_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                </svg>
                Open Output Folder
              </a>
            </div>
          )}

          {/* Title ideas */}
          {job.title_ideas && job.title_ideas.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                Title Ideas
              </h4>
              <ul className="space-y-1">
                {job.title_ideas.map((title, i) => (
                  <li
                    key={i}
                    className="text-sm text-gray-600 dark:text-gray-300 flex items-start"
                  >
                    <span className="mr-2 text-blue-500">•</span>
                    {title}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Chapters */}
          {job.chapters_data && job.chapters_data.length > 0 && (
            <div className="mt-4">
              <h4 className="font-medium text-gray-900 dark:text-white mb-2">
                Chapters
              </h4>
              <div className="space-y-2">
                {job.chapters_data.map((chapter, i) => (
                  <div
                    key={i}
                    className="flex items-center text-sm text-gray-600 dark:text-gray-300"
                  >
                    <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded mr-2">
                      {formatDuration(chapter.start_time)}
                    </span>
                    {chapter.title}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
