import { useEffect, useState } from "react";
import api from "../api";

const colorFor = (correct, attempts) => {
  if (attempts === 0) return "bg-gray-200";
  const pct = Math.round((correct / attempts) * 100);
  return pct >= 80 ? "bg-green-400" : pct >= 50 ? "bg-yellow-400" : "bg-red-400";
};

export default function ParentProgress({ learner, user, onBack }) {
  const [progress, setProgress] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (learner) {
      loadProgress();
    }
  }, [learner]);

  const loadProgress = async () => {
    try {
      const response = await api.get(`/progress/${learner.id}`);
      setProgress(response.data);
    } catch (error) {
      console.error("Failed to load progress:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (onBack) {
      onBack();
    } else {
      window.location.reload();
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p className="text-gray-600">Loading progress...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold">{learner.name}'s Progress</h1>
              <p className="text-sm text-gray-500">Learning progress overview</p>
            </div>
            <button
              onClick={handleBack}
              className="btn-secondary text-sm"
            >
              Back
            </button>
          </div>
        </div>
      </div>

      {/* Progress Content */}
      <div className="max-w-4xl mx-auto p-4">
        {Object.keys(progress).length === 0 ? (
          <div className="card text-center py-8">
            <div className="card-body">
              <p className="text-gray-600 mb-4">No progress data yet</p>
              <p className="text-sm text-gray-500">
                {learner.name} needs to complete some lessons first.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="card">
              <div className="card-body">
                <h3 className="font-semibold mb-4">Concept Mastery</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(progress).map(([concept, data]) => {
                    const percentage = data.attempts > 0 ? Math.round((data.correct / data.attempts) * 100) : 0;
                    return (
                      <div
                        key={concept}
                        className={`p-4 rounded-lg text-center ${colorFor(data.correct, data.attempts)}`}
                      >
                        <div className="font-medium text-sm mb-2">{concept}</div>
                        <div className="text-2xl font-bold">{percentage}%</div>
                        <div className="text-xs mt-1">
                          {data.correct} correct out of {data.attempts} attempts
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Summary Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="card">
                <div className="card-body text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {Object.keys(progress).length}
                  </div>
                  <div className="text-sm text-gray-600">Concepts Practiced</div>
                </div>
              </div>
              
              <div className="card">
                <div className="card-body text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {Object.values(progress).reduce((sum, data) => sum + data.correct, 0)}
                  </div>
                  <div className="text-sm text-gray-600">Correct Answers</div>
                </div>
              </div>
              
              <div className="card">
                <div className="card-body text-center">
                  <div className="text-2xl font-bold text-gray-600">
                    {Object.values(progress).reduce((sum, data) => sum + data.attempts, 0)}
                  </div>
                  <div className="text-sm text-gray-600">Total Attempts</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
