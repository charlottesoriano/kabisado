import React, { useState } from 'react';
import { Logo } from '../common/Logo';
import { Button } from '../common/Button';
import { ShieldCheck, Check, ArrowRight } from 'lucide-react';

interface MobileSignInProps {
  onSignInSuccess: () => void;
}

export const MobileSignIn: React.FC<MobileSignInProps> = ({ onSignInSuccess }) => {
  const [email, setEmail] = useState('student@university.edu.ph');

  return (
    <div className="flex-1 flex flex-col justify-between bg-white">
      {/* 1. Evergreen Hero Top Section with Logo, Headline, and Chips */}
      <div
        className="p-6 pt-4 rounded-b-[28px] text-white space-y-4"
        style={{ backgroundColor: '#1A281F' }}
      >
        <Logo size="md" showSubtitle subtitle="Reviewer" inverted />

        <div className="pt-2">
          <h1 className="font-heading text-2xl font-bold tracking-tight text-white leading-snug">
            Upload your notes. Get a reviewer.
          </h1>
          <p className="text-xs text-[#C7EAE4] mt-1 leading-relaxed">
            Flashcards, quizzes, and auto-graded STEM problems generated from your PDF files.
          </p>
        </div>

        {/* Feature chips */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          <span
            className="px-2.5 py-1 rounded-full text-[11px] font-semibold"
            style={{ backgroundColor: '#A7E8BD', color: '#1A281F' }}
          >
            Flashcards
          </span>
          <span
            className="px-2.5 py-1 rounded-full text-[11px] font-semibold"
            style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
          >
            Quizzes
          </span>
          <span
            className="px-2.5 py-1 rounded-full text-[11px] font-semibold"
            style={{ backgroundColor: '#C0E8F9', color: '#1A281F' }}
          >
            Problem sets
          </span>
          <span
            className="px-2.5 py-1 rounded-full text-[11px] font-semibold"
            style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
          >
            Spaced repetition
          </span>
        </div>
      </div>

      {/* 2. Below: Continue with Google, Email, Continue, Sign-up Link, Clerk Footer */}
      <div className="p-6 space-y-4 flex-1 flex flex-col justify-between">
        <div className="space-y-4 pt-2">
          {/* Continue with Google */}
          <button
            type="button"
            onClick={onSignInSuccess}
            className="w-full min-h-[48px] px-4 py-2.5 rounded-xl border flex items-center justify-center gap-2.5 text-xs font-semibold cursor-pointer active:scale-[0.98]"
            style={{
              borderColor: '#B8D3D1',
              backgroundColor: '#FFFFFF',
              color: '#1A281F',
            }}
          >
            <svg className="w-4 h-4" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
              />
            </svg>
            <span>Continue with Google</span>
          </button>

          <div className="flex items-center gap-2">
            <div className="flex-1 h-[1px] bg-[#B8D3D1]" />
            <span className="text-[11px] uppercase font-semibold text-[#635255]">or</span>
            <div className="flex-1 h-[1px] bg-[#B8D3D1]" />
          </div>

          <div>
            <label className="block text-xs font-semibold text-[#1A281F] mb-1">
              Email address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full min-h-[46px] px-3.5 py-2 rounded-xl text-xs border"
              style={{
                borderColor: '#635255',
                color: '#1A281F',
              }}
            />
          </div>

          <Button
            variant="primary"
            fullWidth
            onClick={onSignInSuccess}
            icon={<ArrowRight className="w-4 h-4" />}
            iconPosition="right"
          >
            Continue
          </Button>

          <p className="text-center text-xs text-[#635255]">
            New to Kabisado?{' '}
            <span
              onClick={onSignInSuccess}
              className="font-semibold underline text-[#1A281F] cursor-pointer"
            >
              Sign up
            </span>
          </p>
        </div>

        {/* Secured by Clerk */}
        <div className="pt-4 border-t border-[#B8D3D1] flex items-center justify-center gap-1.5 text-[11px] text-[#635255]">
          <ShieldCheck className="w-3.5 h-3.5 text-[#1A281F]" />
          <span>Secured by <strong className="text-[#1A281F]">Clerk</strong></span>
        </div>
      </div>
    </div>
  );
};
