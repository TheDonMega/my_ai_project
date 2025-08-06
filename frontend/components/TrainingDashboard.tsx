import React, { useState, useEffect } from 'react';

interface TrainingStats {
  total_documents: number;
  last_training_time: string;
  training_duration: number;
  documents_processed: number;
  categories_trained: number;
  vector_store_size: number;
  improvement_score: number;
}

interface TrainingHistory {
  timestamp: string;
  documents_processed: number;
  duration: number;
  success: boolean;
}

interface FeedbackInsights {
  has_data: boolean;
  message?: string;
  learning_summary: {
    total_feedback_analyzed: number;
    successful_patterns: number;
    common_issues: number;
    query_improvements: number;
  };
  successful_patterns: number;
  common_issues: string[];
  query_improvements: number;
  high_rated_count: number;
  low_rated_count: number;
  response_guidelines: {
    response_length: string;
    detail_level: string;
    include_examples: boolean;
    structure_style: string;
    avoid_issues: string[];
  };
  last_updated: string;
}

const TrainingDashboard: React.FC = () => {
  const [stats, setStats] = useState<TrainingStats | null>(null);
  const [history, setHistory] = useState<TrainingHistory[]>([]);
  const [feedbackInsights, setFeedbackInsights] = useState<FeedbackInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTrainingData();
  }, []);

  const fetchTrainingData = async () => {
    try {
      setLoading(true);
      
      // Fetch training stats from backend
      const statsResponse = await fetch('http://localhost:5557/training/stats');
      if (statsResponse.ok) {
        const statsData = await statsResponse.json();
        setStats(statsData);
      }

      // Fetch training history from backend
      const historyResponse = await fetch('http://localhost:5557/training/history');
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setHistory(historyData);
      }

      // Fetch feedback insights from backend
      const insightsResponse = await fetch('http://localhost:5557/training/feedback-insights');
      if (insightsResponse.ok) {
        const insightsData = await insightsResponse.json();
        setFeedbackInsights(insightsData);
      }
    } catch (err) {
      setError('Failed to load training data');
      console.error('Error fetching training data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getImprovementColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2">Loading training data...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-md p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error</h3>
            <div className="mt-2 text-sm text-red-700">{error}</div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="border-b border-gray-200 pb-4">
        <h2 className="text-2xl font-bold text-gray-900">Training Progress & Analytics</h2>
        <p className="mt-1 text-sm text-gray-500">
          Track how your AI is learning and improving over time
        </p>
      </div>

      {/* Training Stats */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Total Documents</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.total_documents}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Improvement Score</dt>
                    <dd className={`text-lg font-medium ${getImprovementColor(stats.improvement_score)}`}>
                      {stats.improvement_score}%
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Categories</dt>
                    <dd className="text-lg font-medium text-gray-900">{stats.categories_trained}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-6 w-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">Last Training</dt>
                    <dd className="text-sm font-medium text-gray-900">
                      {new Date(stats.last_training_time).toLocaleDateString()}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Training History */}
      {history.length > 0 && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Training History
            </h3>
            <div className="space-y-3">
              {history.slice(0, 10).map((entry, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-md">
                  <div className="flex items-center space-x-4">
                    <div className={`w-3 h-3 rounded-full ${entry.success ? 'bg-green-400' : 'bg-red-400'}`}></div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {new Date(entry.timestamp).toLocaleString()}
                      </p>
                      <p className="text-xs text-gray-500">
                        {entry.documents_processed} documents processed
                      </p>
                    </div>
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDuration(entry.duration)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Feedback Learning Insights */}
      {feedbackInsights && feedbackInsights.has_data && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              🧠 Feedback Learning Insights
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
              <div className="bg-green-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-green-600">{feedbackInsights.high_rated_count}</div>
                <div className="text-sm text-green-700">High-Rated Responses</div>
              </div>
              <div className="bg-red-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-red-600">{feedbackInsights.low_rated_count}</div>
                <div className="text-sm text-red-700">Low-Rated Responses</div>
              </div>
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-blue-600">{feedbackInsights.successful_patterns}</div>
                <div className="text-sm text-blue-700">Successful Patterns</div>
              </div>
              <div className="bg-purple-50 p-4 rounded-lg">
                <div className="text-2xl font-bold text-purple-600">{feedbackInsights.query_improvements}</div>
                <div className="text-sm text-purple-700">Query Improvements</div>
              </div>
            </div>
            
            {/* Response Guidelines */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 mb-3">📋 Response Guidelines (Learned from Feedback)</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm font-medium text-gray-700">Response Length</div>
                  <div className="text-sm text-gray-600 capitalize">{feedbackInsights.response_guidelines.response_length}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm font-medium text-gray-700">Detail Level</div>
                  <div className="text-sm text-gray-600 capitalize">{feedbackInsights.response_guidelines.detail_level}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm font-medium text-gray-700">Structure Style</div>
                  <div className="text-sm text-gray-600 capitalize">{feedbackInsights.response_guidelines.structure_style.replace('_', ' ')}</div>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <div className="text-sm font-medium text-gray-700">Include Examples</div>
                  <div className="text-sm text-gray-600">{feedbackInsights.response_guidelines.include_examples ? 'Yes' : 'No'}</div>
                </div>
              </div>
            </div>

            {/* Issues to Avoid */}
            {feedbackInsights.response_guidelines.avoid_issues.length > 0 && (
              <div className="mb-6">
                <h4 className="font-medium text-gray-900 mb-3">⚠️ Issues to Avoid</h4>
                <div className="flex flex-wrap gap-2">
                  {feedbackInsights.response_guidelines.avoid_issues.map((issue, index) => (
                    <span key={index} className="px-3 py-1 bg-red-100 text-red-800 text-sm rounded-full">
                      {issue.replace('_', ' ')}
                    </span>
                  ))}
                </div>
              </div>
            )}

            <div className="text-xs text-gray-500">
              Last updated: {new Date(feedbackInsights.last_updated).toLocaleString()}
            </div>
          </div>
        </div>
      )}

      {/* No Feedback Data Message */}
      {feedbackInsights && !feedbackInsights.has_data && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">No Feedback Learning Data</h3>
              <div className="mt-2 text-sm text-yellow-700">
                {feedbackInsights.message || 'Train the system and provide feedback to see learning insights.'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Improvement Tips */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-medium text-blue-900 mb-3">
          💡 How Training Improves Your AI
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="font-medium text-blue-800 mb-2">📊 Better Indexing</h4>
            <p className="text-sm text-blue-700">
              Training creates optimized indexes for faster and more accurate document retrieval.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-blue-800 mb-2">🎯 Improved Relevance</h4>
            <p className="text-sm text-blue-700">
              The AI learns to better understand context and provide more relevant responses.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-blue-800 mb-2">🧠 Semantic Understanding</h4>
            <p className="text-sm text-blue-700">
              Creates embeddings that capture the meaning of your documents, not just keywords.
            </p>
          </div>
          <div>
            <h4 className="font-medium text-blue-800 mb-2">📈 Continuous Learning</h4>
            <p className="text-sm text-blue-700">
              Each training session builds upon previous knowledge for better performance.
            </p>
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <div className="flex justify-center">
        <button
          onClick={fetchTrainingData}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Refresh Data
        </button>
      </div>
    </div>
  );
};

export default TrainingDashboard; 