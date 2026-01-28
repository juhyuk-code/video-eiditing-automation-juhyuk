'use client';

import { JobStatus, STEP_ORDER } from '@/lib/types';

interface ProgressBarProps {
  status: JobStatus;
  progress: number;
}

export function ProgressBar({ status, progress }: ProgressBarProps) {
  // Calculate step-based progress
  const stepIndex = STEP_ORDER.indexOf(status);
  const totalSteps = STEP_ORDER.length - 1; // Exclude 'completed'
  const stepProgress = status === 'completed' ? 100 : (stepIndex / totalSteps) * 100;

  const getBarColor = () => {
    if (status === 'completed') return 'bg-green-500';
    if (status === 'failed') return 'bg-red-500';
    return 'bg-blue-500';
  };

  return (
    <div className="w-full">
      <div className="flex justify-between text-xs text-gray-500 mb-1">
        <span>Progress</span>
        <span>{Math.round(stepProgress)}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2 dark:bg-gray-700">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${getBarColor()}`}
          style={{ width: `${stepProgress}%` }}
        />
      </div>
    </div>
  );
}
