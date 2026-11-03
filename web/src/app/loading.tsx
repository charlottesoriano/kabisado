import React from 'react';

/**
 * Next.js Default App Router Loading Component
 * Rendered during route transitions or suspense fallbacks
 */
export default function Loading() {
  return (
    <div className="max-w-[1280px] mx-auto px-6 py-8 animate-pulse space-y-8">
      {/* Hero skeleton */}
      <div
        className="h-44 rounded-[16px] border"
        style={{ backgroundColor: '#B8D3D1', opacity: 0.3, borderColor: '#B8D3D1' }}
      />
      {/* Stat tiles skeleton */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div
          className="h-28 rounded-[16px] border"
          style={{ backgroundColor: '#B8D3D1', opacity: 0.25, borderColor: '#B8D3D1' }}
        />
        <div
          className="h-28 rounded-[16px] border"
          style={{ backgroundColor: '#B8D3D1', opacity: 0.25, borderColor: '#B8D3D1' }}
        />
        <div
          className="h-28 rounded-[16px] border"
          style={{ backgroundColor: '#B8D3D1', opacity: 0.25, borderColor: '#B8D3D1' }}
        />
      </div>
      {/* Grid skeleton */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        <div className="lg:col-span-8 space-y-4">
          <div
            className="h-24 rounded-[16px] border"
            style={{ backgroundColor: '#B8D3D1', opacity: 0.25, borderColor: '#B8D3D1' }}
          />
          <div
            className="h-24 rounded-[16px] border"
            style={{ backgroundColor: '#B8D3D1', opacity: 0.25, borderColor: '#B8D3D1' }}
          />
        </div>
        <div
          className="lg:col-span-4 h-72 rounded-[16px] border"
          style={{ backgroundColor: '#B8D3D1', opacity: 0.25, borderColor: '#B8D3D1' }}
        />
      </div>
    </div>
  );
}
