import { Job, JobsResponse, CurrentJobResponse } from './types';

// Direct API calls from browser to backend
const API_BASE = 'http://localhost:8000/api';

export async function fetchJobs(userId: string): Promise<JobsResponse> {
  const res = await fetch(`${API_BASE}/jobs?user_id=${userId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch jobs');
  }
  return res.json();
}

export async function fetchCurrentJob(userId: string): Promise<CurrentJobResponse> {
  const res = await fetch(`${API_BASE}/jobs/current?user_id=${userId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch current job');
  }
  return res.json();
}

export async function fetchJob(jobId: string, userId: string): Promise<Job> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}?user_id=${userId}`);
  if (!res.ok) {
    throw new Error('Failed to fetch job');
  }
  return res.json();
}

export async function reprocessJob(jobId: string, userId: string): Promise<{ new_job_id: string }> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}/reprocess?user_id=${userId}`, {
    method: 'POST',
  });
  if (!res.ok) {
    throw new Error('Failed to reprocess job');
  }
  return res.json();
}

export async function deleteJob(jobId: string, userId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/jobs/${jobId}?user_id=${userId}`, {
    method: 'DELETE',
  });
  if (!res.ok) {
    throw new Error('Failed to delete job');
  }
}
