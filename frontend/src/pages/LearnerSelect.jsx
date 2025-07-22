import { useEffect, useState } from "react";
import api from "../api";

export default function LearnerSelect({ onPick, onShowProgress, user }) {
  const [learners, setLearners] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({ name: "", dob: "" });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadLearners();
  }, []);

  const loadLearners = async () => {
    try {
      const response = await api.get("/learners");
      setLearners(response.data);
    } catch (error) {
      console.error("Failed to load learners:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddLearner = async (e) => {
    e.preventDefault();
    
    const newErrors = {};
    if (!formData.name.trim()) {
      newErrors.name = "Name is required";
    }
    if (!formData.dob) {
      newErrors.dob = "Date of birth is required";
    } else if (!/^\d{4}-\d{2}$/.test(formData.dob)) {
      newErrors.dob = "Please use YYYY-MM format";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setSubmitting(true);
    setErrors({});

    try {
      const response = await api.post("/learners", formData);
      setLearners(prev => [...prev, response.data]);
      setFormData({ name: "", dob: "" });
      setShowAddForm(false);
    } catch (error) {
      console.error("Failed to add learner:", error);
      setErrors({
        submit: error.response?.data?.detail || "Failed to add learner"
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("lp_jwt");
    window.location.reload();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-semibold">LearnPal</h1>
              <p className="text-sm text-gray-600">{user?.email}</p>
            </div>
            <button onClick={handleLogout} className="btn-secondary text-sm">
              Sign Out
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto p-4">
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-2">Who's learning today?</h2>
          <p className="text-gray-600 text-sm">Select a learner to start a session or view progress</p>
        </div>

        {/* Learners */}
        {learners.length === 0 ? (
          <div className="card text-center py-8">
            <div className="card-body">
              <p className="text-gray-600 mb-4">No learners yet</p>
              <button
                onClick={() => setShowAddForm(true)}
                className="btn-primary"
              >
                Add Your First Learner
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {learners.map((learner) => (
              <div key={learner.id} className="card hover:shadow-md transition-shadow">
                <div className="card-body">
                  <div className="flex items-center justify-between">
                    <div 
                      onClick={() => onPick(learner)}
                      className="flex-1 cursor-pointer"
                    >
                      <h3 className="font-medium">{learner.name}</h3>
                      <p className="text-sm text-gray-500">Born {learner.dob}</p>
                    </div>
                    <div className="flex space-x-2">
                      <button
                        onClick={() => onShowProgress && onShowProgress(learner)}
                        className="btn-secondary btn-sm"
                      >
                        Progress
                      </button>
                      <button
                        onClick={() => onPick(learner)}
                        className="btn-primary btn-sm"
                      >
                        Start Session
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            <button
              onClick={() => setShowAddForm(true)}
              className="w-full card hover:shadow-md transition-shadow cursor-pointer border-dashed"
            >
              <div className="card-body text-center py-6">
                <div className="text-gray-400 mb-2">
                  <svg className="w-6 h-6 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </div>
                <p className="text-gray-600">Add Another Learner</p>
              </div>
            </button>
          </div>
        )}

        {/* Add Learner Modal */}
        {showAddForm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg w-full max-w-md">
              <div className="p-4 border-b border-gray-200">
                <h3 className="font-semibold">Add New Learner</h3>
              </div>
              
              <form onSubmit={handleAddLearner} className="p-4 space-y-4">
                {errors.submit && (
                  <div className="bg-red-50 border border-red-200 rounded p-3">
                    <p className="text-sm text-red-600">{errors.submit}</p>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Name *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    className={`input ${errors.name ? 'input-error' : ''}`}
                    placeholder="Child's name"
                  />
                  {errors.name && (
                    <p className="text-sm text-red-600 mt-1">{errors.name}</p>
                  )}
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Date of Birth *
                  </label>
                  <input
                    type="text"
                    value={formData.dob}
                    onChange={(e) => setFormData(prev => ({ ...prev, dob: e.target.value }))}
                    className={`input ${errors.dob ? 'input-error' : ''}`}
                    placeholder="YYYY-MM (e.g., 2018-05)"
                  />
                  <p className="text-xs text-gray-500 mt-1">Year and month only for privacy</p>
                  {errors.dob && (
                    <p className="text-sm text-red-600 mt-1">{errors.dob}</p>
                  )}
                </div>

                <div className="flex justify-end space-x-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setShowAddForm(false);
                      setFormData({ name: "", dob: "" });
                      setErrors({});
                    }}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="btn-primary"
                  >
                    {submitting ? "Adding..." : "Add Learner"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
