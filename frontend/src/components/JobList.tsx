'use client';

import { useState, useEffect, useCallback } from 'react';
import { Job } from '@/lib/types';
import { fetchJobs } from '@/lib/api';
import { JobCard } from './JobCard';

interface JobListProps {
  userId: string;
  refreshInterval?: number;
}

export function JobList({ userId, refreshInterval = 3000 }: JobListProps) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);

  const loadJobs = useCallback(async () => {
    try {
      const data = await fetchJobs(userId);
      setJobs(data.jobs);
      setError(null);

      // Auto-expand the first active job
      const activeJob = data.jobs.find(
        (j) => !['completed', 'failed', 'pending'].includes(j.status)
      );
      if (activeJob && !expandedJobId) {
        setExpandedJobId(activeJob.id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load jobs');
    } finally {
      setLoading(false);
    }
  }, [userId, expandedJobId]);

  useEffect(() => {
    loadJobs();

    // Poll for updates
    const interval = setInterval(loadJobs, refreshInterval);
    return () => clearInterval(interval);
  }, [loadJobs, refreshInterval]);

  if (loading && jobs.length === 0) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-700 dark:text-red-300">{error}</p>
        <button
          onClick={loadJobs}
          className="mt-2 text-sm text-red-600 hover:text-red-800 dark:text-red-400"
        >
          Try again
        </button>
      </div>
    );
  }

  if (jobs.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-6xl mb-4">📁</div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          No jobs yet
        </h3>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          Upload a stream folder to Google Drive to get started
        </p>
      </div>
    );
  }

  // Separate active and completed jobs
  const activeJobs = jobs.filter(
    (j) => !['completed', 'failed'].includes(j.status)
  );
  const completedJobs = jobs.filter((j) =>
    ['completed', 'failed'].includes(j.status)
  );

  return (
    <div className="space-y-6">
      {/* Active jobs */}
      {activeJobs.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
            <span className="w-2 h-2 bg-blue-500 rounded-full mr-2 animate-pulse" />
            Processing ({activeJobs.length})
          </h2>
          <div className="space-y-3">
            {activeJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                isExpanded={expandedJobId === job.id}
                onToggle={() =>
                  setExpandedJobId(expandedJobId === job.id ? null : job.id)
                }
              />
            ))}
          </div>
        </div>
      )}

      {/* Completed jobs */}
      {completedJobs.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            History ({completedJobs.length})
          </h2>
          <div className="space-y-3">
            {completedJobs.map((job) => (
              <JobCard
                key={job.id}
                job={job}
                isExpanded={expandedJobId === job.id}
                onToggle={() =>
                  setExpandedJobId(expandedJobId === job.id ? null : job.id)
                }
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
