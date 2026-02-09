import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { FileText, X, CheckCircle, AlertTriangle } from 'lucide-react';

function FileUploadZone({ 
  fileType, 
  file, 
  onFileUpload, 
  onRemoveFile, 
  title, 
  description, 
  acceptedTypes,
  icon: Icon = FileText 
}) {
  const onDrop = useCallback((acceptedFiles, rejectedFiles) => {
    if (rejectedFiles.length > 0) {
      console.warn('Rejected files:', rejectedFiles);
      return;
    }

    if (acceptedFiles.length > 0) {
      onFileUpload(fileType, acceptedFiles[0]);
    }
  }, [fileType, onFileUpload]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: {
      'text/plain': acceptedTypes.split(','),
      'application/json': ['.json'],
      'text/yaml': ['.yml', '.yaml'],
      'text/markdown': ['.md'],
      'text/x-rst': ['.rst']
    },
    multiple: false,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const handleRemove = (e) => {
    e.stopPropagation();
    onRemoveFile(fileType);
  };

  const getZoneClasses = () => {
    const baseClasses = "border-2 border-dashed rounded-lg p-6 text-center transition-colors cursor-pointer";
    
    if (file) {
      return `${baseClasses} border-green-600 bg-green-900/30`;
    }
    
    if (isDragReject) {
      return `${baseClasses} border-red-600 bg-red-900/30`;
    }
    
    if (isDragActive) {
      return `${baseClasses} border-blue-600 bg-blue-900/30`;
    }
    
    return `${baseClasses} border-gray-600 hover:border-gray-500 bg-gray-800/50`;
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center space-x-2">
        <Icon className="h-5 w-5 text-gray-400" />
        <h3 className="text-lg font-medium text-white">{title}</h3>
      </div>
      
      <div {...getRootProps()} className={getZoneClasses()}>
        <input {...getInputProps()} />
        
        {file ? (
          // File uploaded state
          <div className="space-y-2">
            <CheckCircle className="mx-auto h-8 w-8 text-green-500" />
            <div className="flex items-center justify-center space-x-2">
              <span className="text-sm font-medium text-green-300">
                {file.name}
              </span>
              <button
                onClick={handleRemove}
                className="text-green-400 hover:text-green-300"
                title="Remove file"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <p className="text-xs text-green-400">
              {(file.size / 1024).toFixed(1)} KB • Click to replace
            </p>
          </div>
        ) : (
          // Upload zone state
          <div className="space-y-2">
            {isDragReject ? (
              <>
                <AlertTriangle className="mx-auto h-8 w-8 text-red-500" />
                <p className="text-sm text-red-400">
                  Invalid file type. Expected: {acceptedTypes}
                </p>
              </>
            ) : (
              <>
                <Icon className="mx-auto h-8 w-8 text-gray-500" />
                <div>
                  <p className="text-sm font-medium text-gray-200">
                    {isDragActive ? 'Drop file here...' : 'Drop file or click to upload'}
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    {description}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">
                    Max 10MB • {acceptedTypes}
                  </p>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default FileUploadZone;