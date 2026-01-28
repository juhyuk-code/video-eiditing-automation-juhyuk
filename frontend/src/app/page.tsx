'use client';

import { useState, useEffect } from 'react';
import { JobList } from '@/components';

export default function Dashboard() {
  const [userId, setUserId] = useState<string>('');
  const [inputUserId, setInputUserId] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  // Check for stored user ID on mount
  useEffect(() => {
    const stored = localStorage.getItem('stream_automation_user_id');
    if (stored) {
      setUserId(stored);
      setIsConnected(true);
    }
  }, []);

  const handleConnect = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputUserId.trim()) {
      localStorage.setItem('stream_automation_user_id', inputUserId.trim());
      setUserId(inputUserId.trim());
      setIsConnected(true);
    }
  };

  const handleDisconnect = () => {
    localStorage.removeItem('stream_automation_user_id');
    setUserId('');
    setInputUserId('');
    setIsConnected(false);
  };

  return (
    <main className="min-h-screen">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🎬</span>
            <h1 className="text-xl font-bold text-gray-900 dark:text-white">
              Stream Automation
            </h1>
          </div>
          {isConnected && (
            <button
              onClick={handleDisconnect}
              className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            >
              Disconnect
            </button>
          )}
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {!isConnected ? (
          // Connect form
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 max-w-md mx-auto">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Connect to Dashboard
            </h2>
            <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm">
              Enter your user ID from when you logged in via Google.
            </p>
            <form onSubmit={handleConnect}>
              <input
                type="text"
                value={inputUserId}
                onChange={(e) => setInputUserId(e.target.value)}
                placeholder="Enter your user ID"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
              <button
                type="submit"
                className="mt-4 w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 transition-colors"
              >
                Connect
              </button>
            </form>
            <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded-md">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Your user ID was shown when you logged in. It looks like:
                <br />
                <code className="text-blue-600 dark:text-blue-400">
                  fe684389-9247-49e7-ae50-d20c1fae6432
                </code>
              </p>
            </div>
          </div>
        ) : (
          // Job list
          <JobList userId={userId} refreshInterval={3000} />
        )}
      </div>

      {/* Footer */}
      <footer className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-2">
        <div className="max-w-4xl mx-auto px-4 flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
          <span>Auto-refreshing every 3 seconds</span>
          {isConnected && (
            <span className="flex items-center">
              <span className="w-2 h-2 bg-green-500 rounded-full mr-2" />
              Connected
            </span>
          )}
        </div>
      </footer>
    </main>
  );
}
