import React from 'react';
import { Shield, ArrowLeft } from 'lucide-react';

function Header() {
  return (
    <header className="bg-gray-800 shadow-lg shadow-gray-900/20 border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-6">
          <div className="flex items-center">
            <Shield className="h-8 w-8 text-blue-400 mr-3" />
            <div>
              <h1 className="text-xl font-bold text-white">
                Concord Behavioral Analysis
              </h1>
              <p className="text-sm text-gray-300">
                Semantic coherence verification for codebase artifacts
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2 text-sm text-gray-400">
            <span className="px-2 py-1 bg-green-900 text-green-300 rounded-full">
              Ready
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;