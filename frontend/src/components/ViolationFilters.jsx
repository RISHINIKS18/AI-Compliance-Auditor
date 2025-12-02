import { useState } from 'react';
import PropTypes from 'prop-types';

const ViolationFilters = ({ onFilterChange, documents }) => {
  const [filters, setFilters] = useState({
    severity: '',
    document: '',
    dateFrom: '',
    dateTo: '',
  });

  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const handleReset = () => {
    const resetFilters = {
      severity: '',
      document: '',
      dateFrom: '',
      dateTo: '',
    };
    setFilters(resetFilters);
    onFilterChange(resetFilters);
  };

  const hasActiveFilters = Object.values(filters).some((value) => value !== '');

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Filters</h3>
        {hasActiveFilters && (
          <button
            onClick={handleReset}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            Reset Filters
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Severity Filter */}
        <div>
          <label
            htmlFor="severity-filter"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Severity
          </label>
          <select
            id="severity-filter"
            value={filters.severity}
            onChange={(e) => handleFilterChange('severity', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Document Filter */}
        <div>
          <label
            htmlFor="document-filter"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Document
          </label>
          <select
            id="document-filter"
            value={filters.document}
            onChange={(e) => handleFilterChange('document', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          >
            <option value="">All Documents</option>
            {documents.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.filename}
              </option>
            ))}
          </select>
        </div>

        {/* Date From Filter */}
        <div>
          <label
            htmlFor="date-from-filter"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Date From
          </label>
          <input
            type="date"
            id="date-from-filter"
            value={filters.dateFrom}
            onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
        </div>

        {/* Date To Filter */}
        <div>
          <label
            htmlFor="date-to-filter"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            Date To
          </label>
          <input
            type="date"
            id="date-to-filter"
            value={filters.dateTo}
            onChange={(e) => handleFilterChange('dateTo', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
        </div>
      </div>

      {/* Active Filters Display */}
      {hasActiveFilters && (
        <div className="mt-4 flex flex-wrap gap-2">
          {filters.severity && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              Severity: {filters.severity}
              <button
                onClick={() => handleFilterChange('severity', '')}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          )}
          {filters.document && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              Document: {documents.find((d) => d.id === filters.document)?.filename}
              <button
                onClick={() => handleFilterChange('document', '')}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          )}
          {filters.dateFrom && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              From: {filters.dateFrom}
              <button
                onClick={() => handleFilterChange('dateFrom', '')}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          )}
          {filters.dateTo && (
            <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
              To: {filters.dateTo}
              <button
                onClick={() => handleFilterChange('dateTo', '')}
                className="ml-2 text-blue-600 hover:text-blue-800"
              >
                ×
              </button>
            </span>
          )}
        </div>
      )}
    </div>
  );
};

ViolationFilters.propTypes = {
  onFilterChange: PropTypes.func.isRequired,
  documents: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.string,
      filename: PropTypes.string,
    })
  ).isRequired,
};

export default ViolationFilters;
