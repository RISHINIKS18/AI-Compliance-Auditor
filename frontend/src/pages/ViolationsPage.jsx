import { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from '../lib/axios';
import toast from 'react-hot-toast';
import ViolationsTable from '../components/ViolationsTable';
import ViolationFilters from '../components/ViolationFilters';
import ViolationDetailModal from '../components/ViolationDetailModal';

const ViolationsPage = () => {
  const [selectedViolation, setSelectedViolation] = useState(null);
  const [filters, setFilters] = useState({
    severity: '',
    document: '',
    dateFrom: '',
    dateTo: '',
  });

  // Fetch all violations
  const {
    data: violationsData,
    isLoading: violationsLoading,
    error: violationsError,
  } = useQuery({
    queryKey: ['violations'],
    queryFn: async () => {
      const response = await axios.get('/api/audits/violations');
      return response.data;
    },
    onError: (error) => {
      toast.error(`Failed to load violations: ${error.message}`);
    },
  });

  // Fetch audit documents for filter dropdown
  const { data: auditsData } = useQuery({
    queryKey: ['audits'],
    queryFn: async () => {
      const response = await axios.get('/api/audits');
      return response.data;
    },
  });

  // Apply filters to violations
  const filteredViolations = useMemo(() => {
    if (!violationsData) return [];

    let filtered = [...violationsData];

    // Filter by severity
    if (filters.severity) {
      filtered = filtered.filter(
        (v) => v.severity.toLowerCase() === filters.severity.toLowerCase()
      );
    }

    // Filter by document
    if (filters.document) {
      filtered = filtered.filter((v) => v.audit_document_id === filters.document);
    }

    // Filter by date range
    if (filters.dateFrom) {
      const fromDate = new Date(filters.dateFrom);
      filtered = filtered.filter((v) => new Date(v.detected_at) >= fromDate);
    }

    if (filters.dateTo) {
      const toDate = new Date(filters.dateTo);
      toDate.setHours(23, 59, 59, 999); // End of day
      filtered = filtered.filter((v) => new Date(v.detected_at) <= toDate);
    }

    return filtered;
  }, [violationsData, filters]);

  const handleFilterChange = (newFilters) => {
    setFilters(newFilters);
  };

  const handleRowClick = (violation) => {
    setSelectedViolation(violation);
  };

  const handleCloseModal = () => {
    setSelectedViolation(null);
  };

  if (violationsLoading) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Violations</h1>
        <div className="bg-white rounded-lg shadow p-12">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <span className="ml-3 text-gray-600">Loading violations...</span>
          </div>
        </div>
      </div>
    );
  }

  if (violationsError) {
    return (
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-6">Violations</h1>
        <div className="bg-white rounded-lg shadow p-12">
          <div className="text-center">
            <svg
              className="mx-auto h-12 w-12 text-red-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Error loading violations
            </h3>
            <p className="mt-1 text-sm text-gray-500">{violationsError.message}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Violations Dashboard</h1>
        <p className="mt-1 text-sm text-gray-600">
          Review and manage compliance violations detected in your documents
        </p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm font-medium text-gray-500">Total Violations</div>
          <div className="mt-1 text-2xl font-semibold text-gray-900">
            {violationsData?.length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm font-medium text-gray-500">Critical</div>
          <div className="mt-1 text-2xl font-semibold text-red-600">
            {violationsData?.filter((v) => v.severity === 'critical').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm font-medium text-gray-500">High</div>
          <div className="mt-1 text-2xl font-semibold text-orange-600">
            {violationsData?.filter((v) => v.severity === 'high').length || 0}
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-sm font-medium text-gray-500">Medium/Low</div>
          <div className="mt-1 text-2xl font-semibold text-yellow-600">
            {violationsData?.filter(
              (v) => v.severity === 'medium' || v.severity === 'low'
            ).length || 0}
          </div>
        </div>
      </div>

      {/* Filters */}
      <ViolationFilters
        onFilterChange={handleFilterChange}
        documents={auditsData || []}
      />

      {/* Violations Table */}
      <ViolationsTable
        violations={filteredViolations}
        onRowClick={handleRowClick}
      />

      {/* Detail Modal */}
      {selectedViolation && (
        <ViolationDetailModal
          violation={selectedViolation}
          onClose={handleCloseModal}
        />
      )}
    </div>
  );
};

export default ViolationsPage;
