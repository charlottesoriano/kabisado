import React from 'react';
import { WebSignIn } from '../../components/web/WebSignIn';
import { useRouter } from '../../lib/router';

/**
 * Next.js Page Route: /sign-in
 */
export default function SignInPage() {
  const router = useRouter();

  return (
    <WebSignIn
      onSignInSuccess={() => router.push('/dashboard')}
    />
  );
}
