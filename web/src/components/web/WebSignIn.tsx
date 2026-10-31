import React, { useState } from 'react';
import { Logo } from '../common/Logo';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Chip } from '../common/Chip';
import { Check, ShieldCheck, ArrowRight } from 'lucide-react';

interface WebSignInProps {
  onSignInSuccess: () => void;
}

export const WebSignIn: React.FC<WebSignInProps> = ({ onSignInSuccess }) => {
  const [email, setEmail] = useState('miguel.ramos@student.edu.ph');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setTimeout(() => {
      setIsSubmitting(false);
      onSignInSuccess();
    }, 400);
  };

  return (
    <div
      className="min-h-[calc(100vh-120px)] flex items-center justify-center p-6"
      style={{ backgroundColor: '#F3FAF8' }}
    >
      <div className="w-full max-w-[960px] grid grid-cols-1 md:grid-cols-12 rounded-[22px] overflow-hidden border"
        style={{ borderColor: '#B8D3D1', backgroundColor: '#FFFFFF' }}
      >
        {/* Left: Evergreen Brand Panel (7 cols on md) */}
        <div
          className="md:col-span-7 p-8 md:p-12 flex flex-col justify-between"
          style={{ backgroundColor: '#1A281F', color: '#FFFFFF' }}
        >
          <div>
            <Logo size="lg" showSubtitle subtitle="Reviewer" inverted />

            <div className="mt-12 max-w-md">
              <h1 className="font-heading text-3xl md:text-4xl font-bold leading-tight tracking-tight text-white">
                Upload your notes. Get a reviewer.
              </h1>
              <p className="mt-4 text-[15px] leading-relaxed text-[#C7EAE4]">
                Kabisado turns your lectures, slides, and syllabus into active recall flashcards, practice quizzes, and auto-graded STEM problem sets.
              </p>
            </div>

            {/* Feature Chips */}
            <div className="mt-8 flex flex-wrap gap-2.5">
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
                style={{ backgroundColor: '#A7E8BD', color: '#1A281F' }}
              >
                <Check className="w-3.5 h-3.5" strokeWidth={2.5} />
                Flashcards
              </span>
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
                style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
              >
                <Check className="w-3.5 h-3.5" strokeWidth={2.5} />
                Quizzes
              </span>
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
                style={{ backgroundColor: '#C0E8F9', color: '#1A281F' }}
              >
                <Check className="w-3.5 h-3.5" strokeWidth={2.5} />
                Problem sets
              </span>
              <span
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold"
                style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
              >
                <Check className="w-3.5 h-3.5" strokeWidth={2.5} />
                Spaced repetition
              </span>
            </div>
          </div>

          <div className="mt-12 pt-6 border-t border-[#635255]/40 text-xs text-[#C7EAE4]/80 flex items-center justify-between">
            <span>Designed for Filipino High School &amp; College Students</span>
            <span>v2.4</span>
          </div>
        </div>

        {/* Right: Clerk-Style White Auth Card (5 cols on md) */}
        <div className="md:col-span-5 p-8 md:p-10 flex flex-col justify-between bg-white">
          <div>
            <div className="mb-6">
              <h2 className="font-heading text-2xl font-bold tracking-tight text-[#1A281F]">
                Sign in to Kabisado
              </h2>
              <p className="text-xs text-[#635255] mt-1">
                Welcome back. Choose your preferred login method.
              </p>
            </div>

            {/* Continue with Google */}
            <button
              type="button"
              onClick={onSignInSuccess}
              className="w-full min-h-[46px] px-4 py-2.5 rounded-xl border flex items-center justify-center gap-3 text-sm font-semibold transition-all cursor-pointer hover:bg-[#F3FAF8] active:scale-[0.99]"
              style={{
                borderColor: '#B8D3D1',
                backgroundColor: '#FFFFFF',
                color: '#1A281F',
              }}
            >
              {/* Google 4-color G icon */}
              <svg className="w-4 h-4 shrink-0" viewBox="0 0 24 24">
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

            {/* "or" divider */}
            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-[1px]" style={{ backgroundColor: '#B8D3D1' }} />
              <span className="text-xs uppercase font-medium" style={{ color: '#635255' }}>
                or
              </span>
              <div className="flex-1 h-[1px]" style={{ backgroundColor: '#B8D3D1' }} />
            </div>

            {/* Email form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-[#1A281F] mb-1.5">
                  Email address
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="student@university.edu.ph"
                  required
                  className="w-full min-h-[44px] px-3.5 py-2 rounded-xl text-sm border focus:outline-none focus:ring-1 focus:ring-[#1A281F]"
                  style={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#635255',
                    color: '#1A281F',
                  }}
                />
              </div>

              <Button
                type="submit"
                variant="primary"
                fullWidth
                disabled={isSubmitting}
                icon={<ArrowRight className="w-4 h-4" />}
                iconPosition="right"
              >
                {isSubmitting ? 'Signing in...' : 'Continue'}
              </Button>
            </form>

            <div className="mt-5 text-center">
              <p className="text-xs text-[#635255]">
                Don't have an account?{' '}
                <button
                  type="button"
                  onClick={onSignInSuccess}
                  className="font-semibold underline text-[#1A281F] hover:opacity-80 cursor-pointer"
                >
                  Sign up for free
                </button>
              </p>
            </div>
          </div>

          {/* Secured by Clerk footer */}
          <div className="pt-6 border-t border-[#B8D3D1] flex items-center justify-center gap-1.5 text-[11px] text-[#635255]">
            <ShieldCheck className="w-3.5 h-3.5 text-[#1A281F]" strokeWidth={2} />
            <span>Secured by <strong className="font-semibold text-[#1A281F]">Clerk</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
