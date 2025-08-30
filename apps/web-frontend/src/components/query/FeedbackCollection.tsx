import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import {
  ThumbsUp,
  ThumbsDown,
  Star,
  MessageSquare,
  Send,
  CheckCircle,
  AlertCircle
} from 'lucide-react';

interface FeedbackData {
  rating: number;
  isHelpful: boolean | null;
  comment: string;
  categories: string[];
}

interface FeedbackCollectionProps {
  onSubmitFeedback: (feedback: FeedbackData) => void;
  isSubmitting?: boolean;
  showRating?: boolean;
  showCategories?: boolean;
}

export default function FeedbackCollection({
  onSubmitFeedback,
  isSubmitting = false,
  showRating = true,
  showCategories = true
}: FeedbackCollectionProps) {
  const [rating, setRating] = React.useState(0);
  const [isHelpful, setIsHelpful] = React.useState<boolean | null>(null);
  const [comment, setComment] = React.useState('');
  const [selectedCategories, setSelectedCategories] = React.useState<string[]>(
    []
  );
  const [isSubmitted, setIsSubmitted] = React.useState(false);

  const feedbackCategories = [
    'Accuracy',
    'Performance',
    'Clarity',
    'Completeness',
    'Ease of Use',
    'Documentation'
  ];

  const handleCategoryToggle = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  const handleSubmit = () => {
    const feedbackData: FeedbackData = {
      rating,
      isHelpful,
      comment,
      categories: selectedCategories
    };

    onSubmitFeedback(feedbackData);
    setIsSubmitted(true);

    // Reset form after a delay
    setTimeout(() => {
      setRating(0);
      setIsHelpful(null);
      setComment('');
      setSelectedCategories([]);
      setIsSubmitted(false);
    }, 3000);
  };

  const isFormValid = () => {
    return (isHelpful !== null || rating > 0) && comment.trim().length > 0;
  };

  if (isSubmitted) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="text-center py-8">
            <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">Thank You!</h3>
            <p className="text-muted-foreground">
              Your feedback has been submitted and will help us improve the
              system.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Provide Feedback
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Quick Feedback */}
        <div>
          <h4 className="text-sm font-medium mb-3">
            Was this SQL generation helpful?
          </h4>
          <div className="flex gap-3">
            <Button
              variant={isHelpful === true ? 'default' : 'outline'}
              onClick={() => setIsHelpful(true)}
              className="flex items-center gap-2"
            >
              <ThumbsUp className="h-4 w-4" />
              Yes, helpful
            </Button>
            <Button
              variant={isHelpful === false ? 'default' : 'outline'}
              onClick={() => setIsHelpful(false)}
              className="flex items-center gap-2"
            >
              <ThumbsDown className="h-4 w-4" />
              Needs improvement
            </Button>
          </div>
        </div>

        {/* Star Rating */}
        {showRating && (
          <div>
            <h4 className="text-sm font-medium mb-3">Overall Rating</h4>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => setRating(star)}
                  className="p-1 hover:scale-110 transition-transform"
                >
                  <Star
                    className={`h-6 w-6 ${
                      star <= rating
                        ? 'fill-yellow-400 text-yellow-400'
                        : 'text-gray-300 hover:text-yellow-400'
                    }`}
                  />
                </button>
              ))}
            </div>
            {rating > 0 && (
              <p className="text-sm text-muted-foreground mt-1">
                {rating === 1 && 'Poor'}
                {rating === 2 && 'Fair'}
                {rating === 3 && 'Good'}
                {rating === 4 && 'Very Good'}
                {rating === 5 && 'Excellent'}
              </p>
            )}
          </div>
        )}

        {/* Feedback Categories */}
        {showCategories && (
          <div>
            <h4 className="text-sm font-medium mb-3">
              What aspects would you like to comment on?
            </h4>
            <div className="flex flex-wrap gap-2">
              {feedbackCategories.map((category) => (
                <Button
                  key={category}
                  variant={
                    selectedCategories.includes(category)
                      ? 'default'
                      : 'outline'
                  }
                  size="sm"
                  onClick={() => handleCategoryToggle(category)}
                >
                  {category}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Comment */}
        <div>
          <h4 className="text-sm font-medium mb-3">
            Additional Comments
            <span className="text-destructive ml-1">*</span>
          </h4>
          <Textarea
            placeholder="Please share your thoughts on the SQL generation, accuracy, or any suggestions for improvement..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            className="min-h-[100px]"
          />
          <p className="text-xs text-muted-foreground mt-1">
            {comment.length}/500 characters
          </p>
        </div>

        {/* Feedback Guidelines */}
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="flex items-start gap-2">
            <AlertCircle className="h-4 w-4 text-blue-500 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-sm font-medium text-blue-900 mb-1">
                Feedback Guidelines
              </h5>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>
                  • Be specific about what worked well or what could be improved
                </li>
                <li>
                  • Include details about accuracy, performance, or usability
                  issues
                </li>
                <li>
                  • Suggest alternative approaches if the generated SQL wasn't
                  optimal
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end">
          <Button
            onClick={handleSubmit}
            disabled={!isFormValid() || isSubmitting}
            className="flex items-center gap-2"
          >
            <Send className="h-4 w-4" />
            {isSubmitting ? 'Submitting...' : 'Submit Feedback'}
          </Button>
        </div>

        {/* Validation Message */}
        {!isFormValid() &&
          (isHelpful !== null || rating > 0 || comment.length > 0) && (
            <div className="text-sm text-muted-foreground">
              Please provide both a rating/helpfulness indicator and a comment.
            </div>
          )}
      </CardContent>
    </Card>
  );
}
