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
      
      // Add files to FormData with correct field names for backend
      Object.entries(files).forEach(([type, file]) => {
        if (file) {
          formData.append(type, file);
        }
      });

      // Call backend API
      console.log('🚀 Sending files to backend API...');
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      const analysisResults = await response.json();
      console.log('✅ Analysis results received:', analysisResults);
      
      setAnalysisResults(analysisResults);
      setIsAnalyzing(false);

    } catch (err) {
      console.error('❌ Analysis failed:', err);
      
      // Check if it's a network error
      if (err.message.includes('fetch')) {
        setError('Cannot connect to analysis server. Make sure the backend is running on localhost:8000');
      } else {
        setError(`Analysis failed: ${err.message}`);
      }
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
    <div className="min-h-screen bg-gray-900">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!analysisResults ? (
          // Upload Interface
          <div className="space-y-8">
            {/* Upload Instructions */}
            <div className="text-center">
              <Upload className="mx-auto h-12 w-12 text-gray-500 mb-4" />
              <h2 className="text-2xl font-bold text-white mb-2">
                Upload Your Codebase Artifacts
              </h2>
              <p className="text-gray-300 max-w-2xl mx-auto">
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
              <div className="rounded-md bg-red-900 border border-red-700 p-4">
                <div className="flex">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-200">
                      Validation Error
                    </h3>
                    <div className="mt-2 text-sm text-red-300">
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
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:ring-offset-gray-800 disabled:opacity-50 disabled:cursor-not-allowed">
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
