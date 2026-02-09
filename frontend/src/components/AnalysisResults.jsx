import React, { useState } from 'react';
import { 
  AlertTriangle, 
  CheckCircle, 
  AlertCircle,
  XCircle,
  FileText,
  ArrowLeft,
  TrendingUp,
  TrendingDown,
  Info
} from 'lucide-react';

function AnalysisResults({ results, onReset, uploadedFiles }) {
  const [selectedUnit, setSelectedUnit] = useState(null);

  const getRiskBadge = (riskBand) => {
    const badgeClasses = {
      critical: 'bg-red-100 text-red-800 border border-red-200',
      high: 'bg-orange-100 text-orange-800 border border-orange-200', 
      medium: 'bg-yellow-100 text-yellow-800 border border-yellow-200',
      low: 'bg-green-100 text-green-800 border border-green-200'
    };
    
    return (
      <span className={`px-2 py-1 text-xs font-medium rounded-full ${badgeClasses[riskBand] || badgeClasses.medium}`}>
        {riskBand.toUpperCase()}
      </span>
    );
  };

  const getConflictIcon = (hasConflicts) => {
    return hasConflicts ? 
      <XCircle className="h-4 w-4 text-red-500" /> :
      <CheckCircle className="h-4 w-4 text-green-500" />;
  };

  const formatAssertion = (assertion) => {
    // Convert technical assertion codes to user-friendly descriptions
    if (!assertion || typeof assertion !== 'string') return assertion;
    
    // Mapping of technical codes to readable descriptions
    const mappings = {
      // HTTP Response patterns
      'OUT_HTTP_200': 'Returns 200 (Success)',
      'OUT_HTTP_201': 'Returns 201 (Created)',
      'OUT_HTTP_204': 'Returns 204 (No Content)',
      'OUT_HTTP_400': 'Returns 400 (Bad Request)',
      'OUT_HTTP_401': 'Returns 401 (Unauthorized)',
      'OUT_HTTP_403': 'Returns 403 (Forbidden)',
      'OUT_HTTP_404': 'Returns 404 (Not Found)',
      'OUT_HTTP_500': 'Returns 500 (Server Error)',
      
      // Error response patterns
      'ERR_HTTP_400': 'Error: Bad Request (400)',
      'ERR_HTTP_401': 'Error: Unauthorized (401)',
      'ERR_HTTP_403': 'Error: Forbidden (403)',
      'ERR_HTTP_404': 'Error: Not Found (404)',
      'ERR_HTTP_500': 'Error: Server Error (500)',
      
      // Schema and body patterns
      'OUT_SCHEMA_COMPONENTS': 'Response body schema',
      'REQUEST_BODY': 'Request body required',
      'SCHEMA_REF': 'Schema reference',
      
      // Authentication patterns
      'PRE_AUTH_REQUIRED': 'Authentication required',
      'PRE_AUTH': 'Authentication required',
      
      // General patterns
      'ENDPOINT_EXISTS': 'Endpoint exists',
      'INPUT_PRECONDITION': 'Input validation',
      'OUTPUT_GUARANTEE': 'Output guarantee',
      'ERROR_SEMANTICS': 'Error handling',
      'IDEMPOTENCY': 'Idempotent operation'
    };
    
    // Check for exact matches first
    if (mappings[assertion]) {
      return mappings[assertion];
    }
    
    // Handle partial matches and complex patterns
    for (const [pattern, description] in Object.entries(mappings)) {
      if (assertion.includes(pattern)) {
        return description;
      }
    }
    
    // Fallback: clean up the original assertion
    return assertion
      .replace(/_/g, ' ')
      .replace(/HTTP(\d+)/gi, 'HTTP $1')
      .replace(/\b(OUT|ERR|PRE|IN)([A-Z])/g, '$1 $2')
      .replace(/([a-z])([A-Z])/g, '$1 $2')
      .replace(/\s+/g, ' ')
      .trim();
  };

  if (!results) return null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
          <p className="text-gray-600 mt-1">
            Behavioral consistency analysis across {results.total_behaviors} units
          </p>
        </div>
        <button
          onClick={onReset}
          className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          New Analysis
        </button>
      </div>

      {/* Summary Cards */}
      <div className="grid md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <FileText className="h-5 w-5 text-blue-500 mr-2" />
            <span className="text-sm font-medium text-gray-600">Total Behaviors</span>
          </div>
          <div className="text-2xl font-bold text-gray-900 mt-1">
            {results.total_behaviors}
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <AlertTriangle className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-sm font-medium text-gray-600">Contradictions</span>
          </div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {results.total_contradictions}
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <TrendingDown className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-sm font-medium text-gray-600">Critical Risk</span>
          </div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {results.risk_distribution.critical}
          </div>
        </div>

        <div className="bg-white rounded-lg border p-4">
          <div className="flex items-center">
            <TrendingUp className="h-5 w-5 text-orange-500 mr-2" />
            <span className="text-sm font-medium text-gray-600">Medium Risk</span>
          </div>
          <div className="text-2xl font-bold text-orange-600 mt-1">
            {results.risk_distribution.medium}
          </div>
        </div>
      </div>

      {/* Source Coverage */}
      <div className="bg-white rounded-lg border p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Uploaded Files</h3>
        <div className="grid md:grid-cols-3 gap-4">
          {Object.entries(uploadedFiles).map(([type, file]) => (
            file && (
              <div key={type} className="flex items-center space-x-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <div>
                  <div className="text-sm font-medium text-gray-900 capitalize">
                    {type.replace('_', ' ')}
                  </div>
                  <div className="text-xs text-gray-500">{file.name}</div>
                </div>
              </div>
            )
          ))}
        </div>
      </div>

      {/* Behavioral Units (Three-Tier Display) */}
      <div className="bg-white rounded-lg border">
        <div className="px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">Behavioral Units</h3>
          <p className="text-sm text-gray-600 mt-1">
            Analysis organized by the three-tier information architecture
          </p>
        </div>
        
        <div className="divide-y">
          {results.behavioral_units.map((unit, index) => (
            <div key={index} className="p-6 hover:bg-gray-50">
              {/* TIER 1: REQUIRED TRUTH */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                      {unit.endpoint}
                    </div>
                    <div className="text-sm text-gray-600">
                      when <span className="italic">{unit.condition}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    {getRiskBadge(unit.risk_band)}
                    {getConflictIcon(unit.assertion_state.has_conflicts)}
                  </div>
                </div>

                {/* Assertions - Required Truth */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <div className="flex items-center mb-2">
                    <Info className="h-4 w-4 text-blue-600 mr-2" />
                    <span className="text-sm font-medium text-blue-900">Required Truth</span>
                  </div>
                  <div className="space-y-1">
                    {unit.assertion_state.assertions.map((assertion, assertionIndex) => (
                      <div key={assertionIndex} className="flex items-center justify-between text-sm">
                        <span className="font-medium text-blue-800 break-words">
                          {formatAssertion(assertion.assertion)}
                        </span>
                        <div className="flex items-center space-x-2 flex-shrink-0 ml-2">
                          <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                            {assertion.sources.join(', ')}
                          </span>
                          {assertion.is_conflicted && (
                            <AlertTriangle className="h-3 w-3 text-red-500" />
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* SEMANTIC ANALYSIS - Show for conflicts */}
                {unit.semantic_description && (
                  <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                    <div className="flex items-center mb-3">
                      <FileText className="h-4 w-4 text-purple-600 mr-2" />
                      <span className="text-sm font-medium text-purple-900">Analysis Summary</span>
                    </div>
                    <div className="text-sm text-purple-800 leading-relaxed">
                      {unit.semantic_description}
                    </div>
                  </div>
                )}

                {/* TIER 2: STRUCTURAL WARNINGS */}
                {unit.structural_warnings.length > 0 && (
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
                    <div className="flex items-center mb-2">
                      <AlertTriangle className="h-4 w-4 text-yellow-600 mr-2" />
                      <span className="text-sm font-medium text-yellow-900">Structural Warnings</span>
                    </div>
                    <div className="space-y-1">
                      {unit.structural_warnings.map((warning, warningIndex) => (
                        <div key={warningIndex} className="text-sm text-yellow-800">
                          {warning.replace(/_/g, ' ')}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* TIER 3: HEURISTIC CONTEXT */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <div className="flex items-center mb-2">
                    <TrendingUp className="h-4 w-4 text-gray-600 mr-2" />
                    <span className="text-sm font-medium text-gray-900">Heuristic Context</span>
                  </div>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-gray-600">Coverage Score:</span>
                      <div className="font-medium text-gray-900">
                        {(unit.coverage_score * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Confidence:</span>
                      <div className="font-medium text-gray-900">
                        {(unit.confidence_score * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div>
                      <span className="text-gray-600">Sources:</span>
                      <div className="text-xs space-x-1 mt-1">
                        {Object.entries(unit.source_coverage).map(([source, covered]) => (
                          <span
                            key={source}
                            className={`px-1 py-0.5 rounded ${
                              covered 
                                ? 'bg-green-100 text-green-700' 
                                : 'bg-gray-100 text-gray-500'
                            }`}
                          >
                            {source}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action Recommendations */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">Recommended Actions</h3>
        <div className="space-y-2 text-sm text-blue-800">
          {results.total_contradictions > 0 && (
            <div className="flex items-start space-x-2">
              <AlertTriangle className="h-4 w-4 text-red-500 mt-0.5" />
              <span>
                Resolve {results.total_contradictions} behavioral contradiction(s) to prevent runtime issues
              </span>
            </div>
          )}
          <div className="flex items-start space-x-2">
            <Info className="h-4 w-4 text-blue-500 mt-0.5" />
            <span>
              Review structural warnings for missing documentation or specifications
            </span>
          </div>
          <div className="flex items-start space-x-2">
            <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
            <span>
              Increase source coverage by adding missing README, spec, or test files
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default AnalysisResults;