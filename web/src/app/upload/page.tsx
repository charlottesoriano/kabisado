import React from 'react';
import { WebUpload } from '../../components/web/WebUpload';
import { useRouter } from '../../lib/router';

interface UploadPageProps {
  isFailedUploadState?: boolean;
  onRetryUpload?: () => void;
  onGenerateSuccess?: (title: string) => void;
}

/**
 * Next.js Page Route: /upload
 */
export default function UploadPage({
  isFailedUploadState = false,
  onRetryUpload,
  onGenerateSuccess,
}: UploadPageProps) {
  const router = useRouter();

  return (
    <WebUpload
      isFailedUploadState={isFailedUploadState}
      onRetryUpload={onRetryUpload}
      onGenerateSuccess={(title) => {
        if (onGenerateSuccess) {
          onGenerateSuccess(title);
        } else {
          router.push('/decks/deck-1');
        }
      }}
      onCancel={() => router.push('/dashboard')}
    />
  );
}
