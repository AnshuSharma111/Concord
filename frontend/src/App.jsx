import React, { useState } from 'react';
import './App.css';
import FileUploadZone from './components/FileUploadZone';
import AnalysisResults from './components/AnalysisResults';
import Header from './components/Header';
import { Upload, FileText, AlertTriangle, CheckCircle } from 'lucide-react';

function App() {
  const [files, setFiles] = useState({
    readme: null,
    spec: null,
    test: null
  });
  const [analysisResults, setAnalysisResults] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState(null);

  const handleFileUpload = (fileType, file) => {
    setFiles(prev => ({
      ...prev,
      [fileType]: file
    }));
    setError(null);
  };

  const removeFile = (fileType) => {
    setFiles(prev => ({
      ...prev,
      [fileType]: null
    }));
  };

  const validateFiles = () => {
    const errors = [];
    
    // At least one file is required
    if (!files.readme && !files.spec && !files.test) {
      errors.push('At least one file is required');
    }

    // File type validation
    Object.entries(files).forEach(([type, file]) => {
      if (file) {
        const validExtensions = {
          readme: ['.md', '.txt', '.rst'],
          spec: ['.yml', '.yaml', '.json'],
          test: ['.py', '.java', '.js', '.ts', '.cs', '.go', '.rs']
        };

        const fileExt = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
        if (!validExtensions[type].includes(fileExt)) {
          errors.push(`${type.toUpperCase()}: Invalid file extension. Expected: ${validExtensions[type].join(', ')}`);
        }

        // File size validation (10MB max)
        if (file.size > 10 * 1024 * 1024) {
          errors.push(`${type.toUpperCase()}: File too large (max 10MB)`);
        }
      }
    });

    return errors;
  };

  const analyzeFiles = async () => {
    const validationErrors = validateFiles();
    if (validationErrors.length > 0) {
      setError(validationErrors.join('; '));
      return;
    }

    setIsAnalyzing(true);
    setError(null);

    try {
      const formData = new FormData();
      
      // Add files to FormData
      Object.entries(files).forEach(([type, file]) => {
        if (file) {
          formData.append(type, file);
        }
      });

      // For now, we'll simulate the API call since backend integration would need CORS setup
      // TODO: Replace with actual API call to backend process.py
      setTimeout(() => {
        // Mock results based on our three-tier display system
        setAnalysisResults({
          behavioral_units: [
            {
              endpoint: 'GET /api/users',
              condition: 'valid request',
              assertion_state: {
                assertions: [
                  { assertion: 'OUT_HTTP_200', sources: ['TEST'], is_conflicted: false }
                ],
                has_conflicts: false
              },
              source_coverage: { test: true, api_spec: false, readme: false },
              structural_warnings: ['MISSING_SPEC', 'MISSING_README'],
              risk_band: 'medium',
              coverage_score: 0.33,
              confidence_score: 0.85
            },
            {
              endpoint: 'POST /api/users',
              condition: 'invalid data',
              assertion_state: {
                assertions: [
                  { assertion: 'ERR_HTTP_400', sources: ['TEST'], is_conflicted: false },
                  { assertion: 'ERR_HTTP_422', sources: ['API_SPEC'], is_conflicted: true }
                ],
                has_conflicts: true
              },
              source_coverage: { test: true, api_spec: true, readme: false },
              structural_warnings: ['CONTRADICTION', 'MISSING_README'],
              risk_band: 'critical',
              coverage_score: 0.67,
              confidence_score: 0.72
            }
          ],
          total_behaviors: 2,
          total_contradictions: 1,
          risk_distribution: {
            critical: 1,
            high: 0,
            medium: 1,
            low: 0
          }
        });
        setIsAnalyzing(false);
      }, 3000);

    } catch (err) {
      setError(`Analysis failed: ${err.message}`);
      setIsAnalyzing(false);
    }
  };

  const resetAnalysis = () => {
    setFiles({ readme: null, spec: null, test: null });
    setAnalysisResults(null);
    setError(null);
  };

  const hasFiles = Object.values(files).some(file => file !== null);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!analysisResults ? (
          // Upload Interface
          <div className="space-y-8">
            {/* Upload Instructions */}
            <div className="text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h2 className="text-2xl font-bold text-gray-900 mb-2">
                Upload Your Codebase Artifacts
              </h2>
              <p className="text-gray-600 max-w-2xl mx-auto">
                Upload README files, API specifications, and test files to analyze behavioral consistency 
                and identify potential issues across your codebase.
              </p>
            </div>

            {/* File Upload Zones */}
            <div className="grid md:grid-cols-3 gap-6">
              <FileUploadZone
                fileType="readme"
                file={files.readme}
                onFileUpload={handleFileUpload}
                onRemoveFile={removeFile}
                title="README Files"
                description="Documentation and user guides"
                acceptedTypes=".md,.txt,.rst"
                icon={FileText}
              />
              
              <FileUploadZone
                fileType="spec"
                file={files.spec}
                onFileUpload={handleFileUpload}
                onRemoveFile={removeFile}
                title="API Specifications"
                description="OpenAPI, Swagger, or schema files"
                acceptedTypes=".yml,.yaml,.json"
                icon={FileText}
              />
              
              <FileUploadZone
                fileType="test"
                file={files.test}
                onFileUpload={handleFileUpload}
                onRemoveFile={removeFile}
                title="Test Files"
                description="Unit tests, integration tests, or spec files"
                acceptedTypes=".py,.java,.js,.ts,.cs,.go,.rs"
                icon={FileText}
              />
            </div>

            {/* Error Display */}
            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <div className="flex">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                      Validation Error
                    </h3>
                    <div className="mt-2 text-sm text-red-700">
                      {error}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Analyze Button */}
            {hasFiles && (
              <div className="text-center">
                <button
                  onClick={analyzeFiles}
                  disabled={isAnalyzing}
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin -ml-1 mr-3 h-5 w-5 border-2 border-white border-t-transparent rounded-full"></div>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="-ml-1 mr-2 h-5 w-5" />
                      Analyze Codebase
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        ) : (
          // Results Interface
          <AnalysisResults 
            results={analysisResults}
            onReset={resetAnalysis}
            uploadedFiles={files}
          />
        )}
      </main>
    </div>
  );
}

export default App;
