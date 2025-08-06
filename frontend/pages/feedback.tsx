import React from 'react';
import FeedbackDashboard from '../components/FeedbackDashboard';
import { GlobalStyle } from '../styles/GlobalStyle';

export default function FeedbackPage() {
  return (
    <div>
      <GlobalStyle />
      <div className="min-h-screen bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">AI Feedback Analytics</h1>
            <p className="mt-2 text-gray-600">
              View insights and analytics from user feedback to improve AI responses
            </p>
          </div>
          
          <FeedbackDashboard />
        </div>
      </div>
    </div>
  );
} 