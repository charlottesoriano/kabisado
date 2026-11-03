import React from 'react';
import { Card } from '../components/common/Card';
import { Button } from '../components/common/Button';
import { Link } from '../lib/router';
import { BookOpen, ArrowLeft } from 'lucide-react';

/**
 * Next.js Default App Router Not-Found (404) Component
 */
export default function NotFound() {
  return (
    <div className="max-w-[720px] mx-auto px-6 py-16">
      <Card className="p-10 text-center space-y-5">
        <div
          className="w-16 h-16 rounded-2xl mx-auto flex items-center justify-center border"
          style={{ backgroundColor: '#C7EAE4', color: '#1A281F', borderColor: '#B8D3D1' }}
        >
          <BookOpen className="w-8 h-8" strokeWidth={2} />
        </div>

        <div className="space-y-1.5">
          <span className="text-xs font-bold uppercase tracking-wider text-[#635255]">
            404 · Page Not Found
          </span>
          <h1 className="font-heading text-3xl font-bold tracking-tight text-[#1A281F]">
            Reviewer or page missing
          </h1>
          <p className="text-sm text-[#635255] max-w-md mx-auto">
            The study deck, review session, or route you are looking for doesn't exist or has been relocated.
          </p>
        </div>

        <div className="pt-3">
          <Link href="/dashboard">
            <Button variant="primary" icon={<ArrowLeft className="w-4 h-4" />}>
              Return to Dashboard
            </Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
