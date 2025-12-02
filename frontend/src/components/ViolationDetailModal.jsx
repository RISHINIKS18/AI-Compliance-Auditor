import { useEffect } from 'react';
import PropTypes from 'prop-types';

const ViolationDetailModal = ({ violation, onClose }) => {
  useEffect(() => {
    // Close modal on escape key
    const handleEscape = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  if (!violation) return null;

  const severityColors = {
    critical: 'bg-red-100 text-red-800 border-red-200',
    high: 'bg-orange-100 text-orange-800 border-orange-200',
    medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    low: 'bg-blue-100 text-blue-800 border-blue-200',
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        />

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-4xl sm:w-full">
          {/* Header */}
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <h3 className="text-lg font-medium text-gray-900">
                  Violation Details
                </h3>
                <span
                  className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium border ${
                    severityColors[violation.severity] ||
                    'bg-gray-100 text-gray-800 border-gray-200'
                  }`}
                >
                  {violation.severity}
                </span>
              </div>
              <button
                onClick={onClose}
                className="text-gray-400 hover:text-gray-500 focus:outline-none"
              >
                <svg
                  className="h-6 w-6"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-[70vh] overflow-y-auto">
            {/* Violation Info */}
            <div className="mb-6">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-700">Document:</span>
                  <p className="mt-1 text-gray-900">{violation.document_name}</p>
                </div>
                <div>
                  <span className="font-medium text-gray-700">Detected:</span>
                  <p className="mt-1 text-gray-900">
                    {new Date(violation.detected_at).toLocaleString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            </div>

            {/* Rule Description */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2">
                Violated Rule
              </h4>
              <div className="bg-red-50 border border-red-200 rounded-md p-4">
                <p className="text-sm text-gray-900">{violation.rule_description}</p>
              </div>
            </div>

            {/* Side-by-side excerpts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              {/* Policy Excerpt */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Policy Excerpt
                </h4>
                <div className="bg-blue-50 border border-blue-200 rounded-md p-4 h-48 overflow-y-auto">
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">
                    {violation.policy_excerpt ||
                      'Policy excerpt not available. This rule was extracted from the organization policy documents.'}
                  </p>
                </div>
              </div>

              {/* Document Excerpt */}
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Document Excerpt
                </h4>
                <div className="bg-orange-50 border border-orange-200 rounded-md p-4 h-48 overflow-y-auto">
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">
                    {violation.document_excerpt ||
                      'Document excerpt not available.'}
                  </p>
                </div>
              </div>
            </div>

            {/* Explanation */}
            {violation.explanation && (
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Explanation
                </h4>
                <div className="bg-gray-50 border border-gray-200 rounded-md p-4">
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">
                    {violation.explanation}
                  </p>
                </div>
              </div>
            )}

            {/* Remediation Suggestions */}
            <div className="mb-6">
              <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                <svg
                  className="h-5 w-5 text-green-600 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                AI-Generated Remediation Suggestions
              </h4>
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <p className="text-sm text-gray-900 whitespace-pre-wrap">
                  {violation.remediation ||
                    'No remediation suggestions available. Please consult with your compliance team.'}
                </p>
              </div>
            </div>
          </div>

          {/* Footer Actions */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200 flex justify-between">
            <div className="flex space-x-3">
              <button
                onClick={() => {
                  // TODO: Implement mark as resolved
                  console.log('Mark as resolved:', violation.id);
                }}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg
                  className="h-4 w-4 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                Mark as Resolved
              </button>
              <button
                onClick={() => {
                  // TODO: Implement export
                  console.log('Export violation:', violation.id);
                }}
                className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                <svg
                  className="h-4 w-4 mr-2"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
                Export
              </button>
            </div>
            <button
              onClick={onClose}
              className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

ViolationDetailModal.propTypes = {
  violation: PropTypes.shape({
    id: PropTypes.string,
    severity: PropTypes.string,
    document_name: PropTypes.string,
    detected_at: PropTypes.string,
    rule_description: PropTypes.string,
    policy_excerpt: PropTypes.string,
    document_excerpt: PropTypes.string,
    explanation: PropTypes.string,
    remediation: PropTypes.string,
  }),
  onClose: PropTypes.func.isRequired,
};

export default ViolationDetailModal;
