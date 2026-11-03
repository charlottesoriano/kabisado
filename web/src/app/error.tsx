'use client';

import React from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { AlertTriangle, RotateCcw } from 'lucide-react';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

/**
 * Next.js Default App Router Error Component
 */
export default function ErrorBoundary({ error, reset }: ErrorProps) {
  return (
    <div className="max-w-[720px] mx-auto px-6 py-16">
      <Card className="p-10 text-center space-y-5">
        <div
          className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center border"
          style={{ backgroundColor: '#FCBCB8', color: '#1A281F', borderColor: '#EFA7A7' }}
        >
          <AlertTriangle className="w-8 h-8" strokeWidth={2} />
        </div>

        <div className="space-y-1.5">
          <span className="text-xs font-bold uppercase tracking-wider text-[#635255]">
            Error encountered
          </span>
          <h1 className="font-heading text-2xl font-bold tracking-tight text-[#1A281F]">
            Something interrupted your study session
          </h1>
          <p className="text-xs text-[#635255] max-w-md mx-auto">
            {error?.message || 'An unexpected error occurred while parsing study material.'}
          </p>
        </div>

        <div className="pt-2">
          <Button
            variant="primary"
            onClick={() => reset()}
            icon={<RotateCcw className="w-4 h-4" />}
          >
            Try again
          </Button>
        </div>
      </Card>
    </div>
  );
}
