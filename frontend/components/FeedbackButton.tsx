import React, { useState } from 'react';

interface FeedbackButtonProps {
  userQuestion: string;
  aiResponse: string;
  searchMethod: string;
  sourcesUsed: string[];
  relevanceScore: number;
  onFeedbackSubmitted?: (insights: string[]) => void;
}

const FeedbackButton: React.FC<FeedbackButtonProps> = ({
  userQuestion,
  aiResponse,
  searchMethod,
  sourcesUsed,
  relevanceScore,
  onFeedbackSubmitted
}) => {
  const [showModal, setShowModal] = useState(false);
  const [rating, setRating] = useState<number | null>(null);
  const [feedbackType, setFeedbackType] = useState<string>('');
  const [feedbackText, setFeedbackText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [learningInsights, setLearningInsights] = useState<string[]>([]);

  const handleFeedbackSubmit = async () => {
    if (!rating || !feedbackType) return;

    setIsSubmitting(true);
    
    try {
      const response = await fetch('http://localhost:5557/feedback', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_question: userQuestion,
          ai_response: aiResponse,
          rating: rating,
          feedback_type: feedbackType,
          feedback_text: feedbackText,
          search_method: searchMethod,
          sources_used: sourcesUsed,
          relevance_score: relevanceScore,
          user_session_id: Date.now().toString()
        }),
      });

      if (response.ok) {
        setSubmitted(true);
        
        // Generate learning insights based on feedback
        const insights = generateLearningInsights(rating, feedbackType, feedbackText);
        setLearningInsights(insights);
        
        // Call the callback to notify parent component
        if (onFeedbackSubmitted) {
          onFeedbackSubmitted(insights);
        }
        
        // Show success message for 5 seconds then close
        setTimeout(() => {
          setShowModal(false);
          setSubmitted(false);
          setRating(null);
          setFeedbackType('');
          setFeedbackText('');
          setLearningInsights([]);
        }, 5000);
      } else {
        console.error('Failed to submit feedback');
      }
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const generateLearningInsights = (rating: number, feedbackType: string, feedbackText: string): string[] => {
    const insights: string[] = [];
    
    if (rating >= 4) {
      insights.push("✅ This response pattern will be reinforced for similar queries");
      insights.push("🎯 Future searches will prioritize this type of content");
    } else if (rating <= 2) {
      insights.push("🔍 The system will avoid similar response patterns");
      insights.push("📈 Search relevance will be adjusted for better results");
    }
    
    if (feedbackText.toLowerCase().includes('more detail') || feedbackText.toLowerCase().includes('incomplete')) {
      insights.push("📝 Future responses will include more comprehensive information");
    }
    
    if (feedbackText.toLowerCase().includes('irrelevant') || feedbackText.toLowerCase().includes('not helpful')) {
      insights.push("🎯 Search relevance thresholds will be improved");
    }
    
    if (feedbackText.toLowerCase().includes('confusing') || feedbackText.toLowerCase().includes('unclear')) {
      insights.push("💡 Response clarity and structure will be enhanced");
    }
    
    if (feedbackText.toLowerCase().includes('too long') || feedbackText.toLowerCase().includes('verbose')) {
      insights.push("✂️ Future responses will be more concise");
    }
    
    if (feedbackText.toLowerCase().includes('examples') || feedbackText.toLowerCase().includes('specific')) {
      insights.push("📋 Responses will include more specific examples");
    }
    
    return insights;
  };



  return (
    <>
      <button
        onClick={() => setShowModal(true)}
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
      >
        💬 Provide Feedback
      </button>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
            {!submitted ? (
              <>
                <h3 className="text-lg font-semibold mb-4">Rate this response</h3>
                
                {/* Rating */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Rating:</label>
                  <div className="flex gap-2">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        onClick={() => setRating(star)}
                        className={`p-2 rounded ${
                          rating === star ? 'bg-yellow-200' : 'bg-gray-100'
                        }`}
                      >
                        {star} ⭐
                      </button>
                    ))}
                  </div>
                </div>

                {/* Feedback Type */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">Feedback Type:</label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setFeedbackType('thumbs_up')}
                      className={`p-2 rounded ${
                        feedbackType === 'thumbs_up' ? 'bg-green-200' : 'bg-gray-100'
                      }`}
                    >
                      👍 Good
                    </button>
                    <button
                      onClick={() => setFeedbackType('neutral')}
                      className={`p-2 rounded ${
                        feedbackType === 'neutral' ? 'bg-yellow-200' : 'bg-gray-100'
                      }`}
                    >
                      😐 Okay
                    </button>
                    <button
                      onClick={() => setFeedbackType('thumbs_down')}
                      className={`p-2 rounded ${
                        feedbackType === 'thumbs_down' ? 'bg-red-200' : 'bg-gray-100'
                      }`}
                    >
                      👎 Poor
                    </button>
                  </div>
                </div>

                {/* Feedback Text */}
                <div className="mb-4">
                  <label className="block text-sm font-medium mb-2">
                    Additional Comments (Optional):
                  </label>
                  <textarea
                    value={feedbackText}
                    onChange={(e) => setFeedbackText(e.target.value)}
                    placeholder="Tell us how we can improve..."
                    className="w-full p-2 border rounded resize-none"
                    rows={3}
                  />
                </div>

                {/* Submit Button */}
                <div className="flex gap-2">
                  <button
                    onClick={handleFeedbackSubmit}
                    disabled={!rating || !feedbackType || isSubmitting}
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-300"
                  >
                    {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
                  </button>
                  <button
                    onClick={() => setShowModal(false)}
                    className="px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                  >
                    Cancel
                  </button>
                </div>
              </>
            ) : (
              <div className="text-center">
                <div className="text-6xl mb-4">🎉</div>
                <h3 className="text-lg font-semibold mb-4 text-green-600">
                  Feedback Submitted Successfully!
                </h3>
                
                <div className="mb-6">
                  <p className="text-sm text-gray-600 mb-4">
                    Your feedback will help improve future responses. Here's how the system will learn:
                  </p>
                  
                  <div className="space-y-2">
                    {learningInsights.map((insight, index) => (
                      <div key={index} className="text-sm text-left bg-blue-50 p-3 rounded">
                        {insight}
                      </div>
                    ))}
                  </div>
                </div>

                <div className="space-y-3">
                  <button
                    onClick={() => setShowModal(false)}
                    className="w-full px-4 py-2 bg-gray-300 text-gray-700 rounded hover:bg-gray-400"
                  >
                    Close
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
};

export default FeedbackButton; 