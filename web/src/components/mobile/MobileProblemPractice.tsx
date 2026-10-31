import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { ProblemItemData } from '../../types';
import {
  X,
  Lightbulb,
  BookOpen,
  ArrowRight,
  RotateCcw,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react';

interface MobileProblemPracticeProps {
  problem: ProblemItemData;
  onNextProblem: () => void;
  onTrySimilar: () => void;
  onClose: () => void;
}

export const MobileProblemPractice: React.FC<MobileProblemPracticeProps> = ({
  problem,
  onNextProblem,
  onTrySimilar,
  onClose,
}) => {
  const [answer, setAnswer] = useState('23.9');
  const [unit, setUnit] = useState('m');
  const [showHintModal, setShowHintModal] = useState(false);
  const [showSolutionModal, setShowSolutionModal] = useState(false);

  return (
    <div className="flex-1 flex flex-col justify-between bg-[#F3FAF8] relative overflow-hidden">
      {/* Top Header */}
      <div className="p-5 pb-0">
        <div className="flex items-center justify-between mb-3">
          <button
            type="button"
            onClick={onClose}
            className="p-2 rounded-xl bg-white border text-[#1A281F] cursor-pointer"
            style={{ borderColor: '#B8D3D1' }}
          >
            <X className="w-4 h-4" strokeWidth={2} />
          </button>

          <span className="font-heading text-xs font-bold text-[#1A281F]">
            Problem 1 of 6
          </span>

          <span
            className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold"
            style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
          >
            Physics 1
          </span>
        </div>
      </div>

      {/* Main Question & Inputs */}
      <div className="p-5 space-y-4 overflow-y-auto pb-24">
        {/* Question Card */}
        <div className="rounded-[22px] p-5 border bg-white shadow-xs space-y-3" style={{ borderColor: '#B8D3D1' }}>
          <span className="text-[10px] font-bold uppercase tracking-wider text-[#635255]">
            Kinematics Problem
          </span>

          <p className="font-heading text-sm font-bold text-[#1A281F] leading-relaxed">
            A sports car starts from rest at a traffic light and{' '}
            <span
              className="inline-flex items-center px-1.5 py-0.5 rounded font-mono font-bold text-xs border"
              style={{
                backgroundColor: '#C7EAE4',
                color: '#1A281F',
                borderColor: '#B8D3D1',
              }}
            >
              accelerates at 3 m/s²
            </span>{' '}
            for{' '}
            <span
              className="inline-flex items-center px-1.5 py-0.5 rounded font-mono font-bold text-xs border"
              style={{
                backgroundColor: '#C7EAE4',
                color: '#1A281F',
                borderColor: '#B8D3D1',
              }}
            >
              4 s
            </span>{' '}
            along a straight highway lane. Calculate the total displacement.
          </p>
        </div>

        {/* Answer and Unit Inputs */}
        <div className="space-y-1.5">
          <label className="block text-xs font-semibold text-[#1A281F]">
            Your Answer &amp; Unit
          </label>
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              className="flex-1 min-h-[46px] px-3.5 py-2 rounded-xl text-sm font-mono border"
              style={{
                borderColor: '#635255',
                backgroundColor: '#FFFFFF',
                color: '#1A281F',
              }}
              placeholder="e.g. 24"
            />
            <input
              type="text"
              value={unit}
              onChange={(e) => setUnit(e.target.value)}
              className="w-20 min-h-[46px] px-2 py-2 rounded-xl text-sm font-mono text-center border"
              style={{
                borderColor: '#635255',
                backgroundColor: '#FFFFFF',
                color: '#1A281F',
              }}
              placeholder="m"
            />
          </div>
        </div>

        {/* Hint and Show Solution Buttons */}
        <div className="flex items-center gap-2 pt-1">
          <button
            type="button"
            onClick={() => setShowHintModal(!showHintModal)}
            className="flex-1 min-h-[42px] px-3 py-2 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer"
            style={{
              backgroundColor: '#FFFFFF',
              borderColor: '#635255',
              color: '#635255',
            }}
          >
            <Lightbulb className="w-3.5 h-3.5 text-[#1A281F]" />
            <span>Hint (1 of 2)</span>
          </button>

          <button
            type="button"
            onClick={() => setShowSolutionModal(!showSolutionModal)}
            className="flex-1 min-h-[42px] px-3 py-2 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer"
            style={{
              backgroundColor: '#FFFFFF',
              borderColor: '#635255',
              color: '#635255',
            }}
          >
            <BookOpen className="w-3.5 h-3.5 text-[#1A281F]" />
            <span>Show solution</span>
          </button>
        </div>

        {/* Inline Hint expander if requested */}
        {showHintModal && (
          <div
            className="p-3.5 rounded-xl border text-xs font-medium space-y-1"
            style={{
              backgroundColor: '#FFD972',
              borderColor: '#B8D3D1',
              color: '#1A281F',
            }}
          >
            <p className="font-bold">Hint 1:</p>
            <p>{problem.hints[0]}</p>
          </div>
        )}

        {/* Inline Solution expander if requested */}
        {showSolutionModal && (
          <div
            className="p-3.5 rounded-xl border text-xs space-y-2"
            style={{
              backgroundColor: '#FFFFFF',
              borderColor: '#B8D3D1',
            }}
          >
            <p className="font-bold text-[#1A281F]">Worked Solution:</p>
            {problem.workedSolution.map((s) => (
              <div key={s.stepNumber} className="flex items-start gap-2">
                <span
                  className="w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 border"
                  style={{ backgroundColor: '#A7E8BD', color: '#1A281F', borderColor: '#1A281F' }}
                >
                  {s.stepNumber}
                </span>
                <span className="text-xs text-[#635255]">{s.explanation}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Mobile Bottom Sheet: Jasmine "Very close — check your rounding" result, Similar one and Next problem */}
      <div
        className="rounded-t-[28px] border-t-2 bg-white p-5 shadow-lg space-y-3.5 z-40 transition-all"
        style={{
          borderColor: '#B8D3D1',
        }}
      >
        <div className="w-10 h-1 bg-[#B8D3D1] rounded-full mx-auto -mt-1 mb-2" />

        {/* Jasmine Result Pill */}
        <div className="flex items-center justify-between">
          <span
            className="px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-1.5"
            style={{
              backgroundColor: '#FFD972',
              borderColor: '#B8D3D1',
              color: '#1A281F',
            }}
          >
            <AlertCircle className="w-3.5 h-3.5 text-[#1A281F]" />
            <span>Very close — check your rounding</span>
          </span>

          <span className="text-xs font-bold text-[#1A281F]">
            Target: 24 m
          </span>
        </div>

        <p className="text-xs text-[#1A281F] leading-relaxed">
          You entered <strong>23.9 m</strong>. When substituting exact integers in <span className="font-mono">d = ½(3)(16)</span>, the result evaluates to exactly <strong>24 m</strong> without fractional rounding needed.
        </p>

        {/* Action Buttons: Similar one & Next problem */}
        <div className="pt-1 flex items-center gap-2">
          <button
            type="button"
            onClick={onTrySimilar}
            className="flex-1 min-h-[46px] px-3 py-2.5 rounded-xl border text-xs font-semibold flex items-center justify-center gap-1.5 cursor-pointer active:scale-95"
            style={{
              backgroundColor: '#FFFFFF',
              borderColor: '#635255',
              color: '#635255',
            }}
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Similar one</span>
          </button>

          <Button
            variant="primary"
            size="md"
            className="flex-1"
            onClick={onNextProblem}
            icon={<ArrowRight className="w-4 h-4" />}
            iconPosition="right"
          >
            Next problem
          </Button>
        </div>
      </div>
    </div>
  );
};
