import React from 'react';
import { Shield, ArrowLeft } from 'lucide-react';

function Header() {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-primary-600 mr-3" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">
                Concord Behavioral Analysis
              </h1>
              <p className="text-sm text-gray-600">
                Semantic coherence verification for codebase artifacts
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full">
              Ready
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;