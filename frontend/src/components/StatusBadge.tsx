'use client';

import { JobStatus, STEP_LABELS } from '@/lib/types';

interface StatusBadgeProps {
  status: JobStatus;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  const getStatusColor = (status: JobStatus) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
      case 'pending':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
      default:
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
    }
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(
        status
      )}`}
    >
      {status !== 'completed' && status !== 'failed' && status !== 'pending' && (
        <span className="w-2 h-2 mr-1.5 bg-blue-500 rounded-full animate-pulse" />
      )}
      {STEP_LABELS[status] || status}
    </span>
  );
}
