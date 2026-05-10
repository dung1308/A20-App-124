import React from 'react';

/**
 * TokenUsagePage Component
 * A placeholder page for displaying LLM token usage statistics.
 */
const TokenUsagePage = () => {
  return (
    <div className="p-8 h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
        <h1 className="text-3xl font-bold text-gray-800 mb-4">LLM Token Usage</h1>
        <p className="text-gray-600 mb-6">
          This page will display detailed statistics on token consumption by the AI models, including daily budgets and cost breakdowns.
        </p>
        <p className="text-gray-500 italic">Data and charts coming soon!</p>
      </div>
    </div>
  );
};

export default TokenUsagePage;