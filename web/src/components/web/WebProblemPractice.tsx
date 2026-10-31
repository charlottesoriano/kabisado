import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Chip } from '../common/Chip';
import { ProblemItemData } from '../../types';
import {
  HelpCircle,
  Lightbulb,
  CheckCircle2,
  XCircle,
  RotateCcw,
  ArrowRight,
  Flag,
  BookOpen,
} from 'lucide-react';

interface WebProblemPracticeProps {
  problem: ProblemItemData;
  onNextProblem: () => void;
  onTrySimilar: () => void;
}

export const WebProblemPractice: React.FC<WebProblemPracticeProps> = ({
  problem,
  onNextProblem,
  onTrySimilar,
}) => {
  const [answerInput, setAnswerInput] = useState(problem.userAnswer || '48');
  const [unitInput, setUnitInput] = useState(problem.userUnit || 'm');
  const [showSolution, setShowSolution] = useState(true); // default true to show the exact answered & worked solution state requested
  const [showHint, setShowHint] = useState(true);
  const [reported, setReported] = useState(false);

  return (
    <div className="max-w-[840px] mx-auto px-6 py-8 space-y-6">
      {/* Subject Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider"
            style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
          >
            {problem.subject}
          </span>
          <span className="text-xs text-[#635255]">
            Auto-graded Problem Set
          </span>
        </div>
        <span className="text-xs font-bold text-[#1A281F]">
          Problem 1 of 6
        </span>
      </div>

      {/* Question Card */}
      <Card className="p-7 md:p-8 space-y-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#635255]">
            Kinematics Calculation
          </span>

          {/* Question with the given numbers highlighted in Frozen Water chips ("accelerates at 3 m/s² for 4 s") */}
          <h2 className="font-heading text-lg md:text-xl font-bold tracking-tight text-[#1A281F] mt-2 leading-relaxed">
            A sports car starts from rest at a traffic light and{' '}
            <span
              className="inline-flex items-center px-2 py-0.5 rounded font-mono font-bold text-sm mx-1 align-baseline border"
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
              className="inline-flex items-center px-2 py-0.5 rounded font-mono font-bold text-sm mx-1 align-baseline border"
              style={{
                backgroundColor: '#C7EAE4',
                color: '#1A281F',
                borderColor: '#B8D3D1',
              }}
            >
              4 s
            </span>{' '}
            along a straight highway lane. Calculate the total displacement traveled by the car during this time interval.
          </h2>
        </div>

        {/* Input Row: Answer Input & Unit Input */}
        <div className="pt-2">
          <label className="block text-xs font-semibold text-[#1A281F] mb-2">
            Your Calculated Answer &amp; SI Unit
          </label>
          <div className="flex items-center gap-3 max-w-md">
            <div className="flex-1">
              <input
                type="text"
                value={answerInput}
                onChange={(e) => setAnswerInput(e.target.value)}
                placeholder="Magnitude (e.g. 24)"
                className="w-full min-h-[44px] px-3.5 py-2 rounded-xl text-sm font-mono border focus:outline-none focus:ring-1 focus:ring-[#1A281F]"
                style={{
                  borderColor: '#635255',
                  backgroundColor: '#FFFFFF',
                  color: '#1A281F',
                }}
              />
            </div>
            <div className="w-24">
              <input
                type="text"
                value={unitInput}
                onChange={(e) => setUnitInput(e.target.value)}
                placeholder="Unit (e.g. m)"
                className="w-full min-h-[44px] px-3 py-2 rounded-xl text-sm font-mono text-center border focus:outline-none focus:ring-1 focus:ring-[#1A281F]"
                style={{
                  borderColor: '#635255',
                  backgroundColor: '#FFFFFF',
                  color: '#1A281F',
                }}
              />
            </div>
          </div>
        </div>

        {/* Result Banner: "Not quite", feedback naming the common mistake ("You may have dropped the ½ in d = ½at²"), "Correct answer: 24 m" */}
        <div
          className="p-5 rounded-xl border space-y-2.5"
          style={{
            backgroundColor: '#FCBCB8',
            borderColor: '#EFA7A7',
          }}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <XCircle className="w-4 h-4 text-[#1A281F]" strokeWidth={2.5} />
              <span className="font-heading text-base font-bold text-[#1A281F]">
                {problem.statusText}
              </span>
            </div>
            <span
              className="px-2.5 py-0.5 rounded text-xs font-bold border"
              style={{
                backgroundColor: '#A7E8BD',
                color: '#1A281F',
                borderColor: '#1A281F',
              }}
            >
              Correct answer: {problem.correctAnswer} {problem.unit}
            </span>
          </div>

          <p className="text-xs text-[#1A281F] leading-relaxed">
            {problem.mistakeFeedback}
          </p>
        </div>

        {/* Hints Panel: "1 of 2 used", hint in a Jasmine (#FFD972) box */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold text-[#1A281F] flex items-center gap-1.5">
              <Lightbulb className="w-3.5 h-3.5 text-[#1A281F]" />
              <span>Hints ({problem.usedHintsCount} of {problem.hints.length} used)</span>
            </span>
            <button
              type="button"
              onClick={() => setShowHint(!showHint)}
              className="text-xs text-[#635255] hover:text-[#1A281F] underline font-medium cursor-pointer"
            >
              {showHint ? 'Collapse hint' : 'View hint'}
            </button>
          </div>

          {showHint && (
            <div
              className="p-4 rounded-xl border text-xs leading-relaxed font-medium"
              style={{
                backgroundColor: '#FFD972',
                borderColor: '#B8D3D1',
                color: '#1A281F',
              }}
            >
              <strong>Hint 1:</strong> {problem.hints[0]}
            </div>
          )}
        </div>

        {/* Worked Solution Panel: Numbered steps with Celadon (#A7E8BD) circles */}
        <div className="space-y-3 pt-2 border-t border-[#B8D3D1]">
          <div className="flex items-center justify-between">
            <span className="font-heading text-sm font-bold text-[#1A281F] flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-[#1A281F]" />
              <span>Worked Solution &amp; Derivation</span>
            </span>
            <button
              type="button"
              onClick={() => setShowSolution(!showSolution)}
              className="text-xs text-[#635255] hover:text-[#1A281F] underline font-medium cursor-pointer"
            >
              {showSolution ? 'Hide steps' : 'Show full steps'}
            </button>
          </div>

          {showSolution && (
            <div className="space-y-3 pt-1">
              {problem.workedSolution.map((step) => (
                <div
                  key={step.stepNumber}
                  className="p-4 rounded-xl border flex items-start gap-3.5"
                  style={{ backgroundColor: '#F3FAF8', borderColor: '#B8D3D1' }}
                >
                  {/* Celadon (#A7E8BD) circle with Evergreen text */}
                  <div
                    className="w-7 h-7 rounded-full flex items-center justify-center font-bold text-xs shrink-0 border"
                    style={{
                      backgroundColor: '#A7E8BD',
                      color: '#1A281F',
                      borderColor: '#1A281F',
                    }}
                  >
                    {step.stepNumber}
                  </div>

                  <div className="space-y-1">
                    <h4 className="text-xs font-bold text-[#1A281F]">
                      {step.title}
                    </h4>
                    <p className="text-xs text-[#635255] leading-relaxed">
                      {step.explanation}
                    </p>
                    {step.formula && (
                      <div
                        className="inline-block px-2.5 py-1 rounded-md text-xs font-mono font-bold mt-1 border"
                        style={{
                          backgroundColor: '#FFFFFF',
                          borderColor: '#B8D3D1',
                          color: '#1A281F',
                        }}
                      >
                        {step.formula}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Buttons: Report problem, Try a similar one, Next problem */}
        <div className="pt-4 border-t border-[#B8D3D1] flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
          <button
            type="button"
            onClick={() => setReported(true)}
            className="text-xs text-[#635255] hover:text-[#1A281F] flex items-center gap-1.5 font-medium cursor-pointer"
          >
            <Flag className="w-3.5 h-3.5" />
            <span>{reported ? 'Reported' : 'Report problem'}</span>
          </button>

          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="md"
              onClick={onTrySimilar}
              icon={<RotateCcw className="w-4 h-4" />}
            >
              Try a similar one
            </Button>

            <Button
              variant="primary"
              size="md"
              onClick={onNextProblem}
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
            >
              Next problem
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};
