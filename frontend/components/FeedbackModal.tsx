import React, { useState } from 'react';

interface FeedbackModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (feedback: FeedbackData) => void;
  userQuestion: string;
  aiResponse: string;
  searchMethod: string;
  sourcesUsed: string[];
  relevanceScore: number;
}

interface FeedbackData {
  user_question: string;
  ai_response: string;
  rating: number;
  feedback_type: 'thumbs_up' | 'thumbs_down' | 'neutral';
  feedback_text: string;
  search_method: string;
  sources_used: string[];
  relevance_score: number;
  user_session_id: string;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({
  isOpen,
  onClose,
  onSubmit,
  userQuestion,
  aiResponse,
  searchMethod,
  sourcesUsed,
  relevanceScore
}) => {
  const [rating, setRating] = useState<number>(0);
  const [feedbackType, setFeedbackType] = useState<'thumbs_up' | 'thumbs_down' | 'neutral'>('neutral');
  const [feedbackText, setFeedbackText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) {
      alert('Please provide a rating');
      return;
    }

    setIsSubmitting(true);
    
    const feedbackData: FeedbackData = {
      user_question: userQuestion,
      ai_response: aiResponse,
      rating,
      feedback_type: feedbackType,
      feedback_text: feedbackText,
      search_method: searchMethod,
      sources_used: sourcesUsed,
      relevance_score: relevanceScore,
      user_session_id: `session_${Date.now()}`
    };

    try {
      await onSubmit(feedbackData);
      onClose();
      // Reset form
      setRating(0);
      setFeedbackType('neutral');
      setFeedbackText('');
    } catch (error) {
      console.error('Error submitting feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">Rate This Response</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl"
          >
            ×
          </button>
        </div>

        {/* Original Question */}
        <div className="mb-4">
          <h3 className="font-semibold text-gray-700 mb-2">Your Question:</h3>
          <p className="text-gray-600 bg-gray-50 p-3 rounded">{userQuestion}</p>
        </div>

        {/* AI Response Preview */}
        <div className="mb-4">
          <h3 className="font-semibold text-gray-700 mb-2">AI Response:</h3>
          <div className="bg-gray-50 p-3 rounded max-h-32 overflow-y-auto">
            <p className="text-gray-600 text-sm">
              {aiResponse.length > 200 ? `${aiResponse.substring(0, 200)}...` : aiResponse}
            </p>
          </div>
        </div>

        {/* Rating */}
        <div className="mb-4">
          <h3 className="font-semibold text-gray-700 mb-2">How would you rate this response?</h3>
          <div className="flex space-x-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => setRating(star)}
                className={`text-2xl ${
                  star <= rating ? 'text-yellow-400' : 'text-gray-300'
                } hover:text-yellow-400 transition-colors`}
              >
                ★
              </button>
            ))}
          </div>
          <p className="text-sm text-gray-500 mt-1">
            {rating === 0 && 'Click a star to rate'}
            {rating === 1 && 'Poor - Not helpful at all'}
            {rating === 2 && 'Fair - Somewhat helpful'}
            {rating === 3 && 'Good - Moderately helpful'}
            {rating === 4 && 'Very Good - Quite helpful'}
            {rating === 5 && 'Excellent - Very helpful'}
          </p>
        </div>

        {/* Quick Feedback Type */}
        <div className="mb-4">
          <h3 className="font-semibold text-gray-700 mb-2">Quick Feedback:</h3>
          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="radio"
                name="feedbackType"
                value="thumbs_up"
                checked={feedbackType === 'thumbs_up'}
                onChange={(e) => setFeedbackType(e.target.value as any)}
                className="mr-2"
              />
              👍 Helpful
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="feedbackType"
                value="neutral"
                checked={feedbackType === 'neutral'}
                onChange={(e) => setFeedbackType(e.target.value as any)}
                className="mr-2"
              />
              😐 Okay
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                name="feedbackType"
                value="thumbs_down"
                checked={feedbackType === 'thumbs_down'}
                onChange={(e) => setFeedbackType(e.target.value as any)}
                className="mr-2"
              />
              👎 Not Helpful
            </label>
          </div>
        </div>

        {/* Detailed Feedback */}
        <div className="mb-4">
          <h3 className="font-semibold text-gray-700 mb-2">
            Additional Comments (Optional):
          </h3>
          <textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Tell us what you were looking for, what was wrong, or how we can improve..."
            className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={3}
          />
        </div>

        {/* Response Details */}
        <div className="mb-4 text-sm text-gray-600">
          <p><strong>Search Method:</strong> {searchMethod}</p>
          <p><strong>Relevance Score:</strong> {(relevanceScore * 100).toFixed(1)}%</p>
          <p><strong>Sources Used:</strong> {sourcesUsed.length} document(s)</p>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-end space-x-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
            disabled={isSubmitting}
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || rating === 0}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default FeedbackModal; 