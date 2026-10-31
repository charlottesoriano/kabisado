import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Chip } from '../common/Chip';
import { CodingProblemData } from '../../types';
import {
  Code,
  Terminal,
  XCircle,
  CheckCircle2,
  RotateCcw,
  ArrowRight,
  Flag,
  Sparkles,
} from 'lucide-react';

interface WebCodingProblemProps {
  codingProblem: CodingProblemData;
  onNextProblem: () => void;
  onTrySimilar: () => void;
}

export const WebCodingProblem: React.FC<WebCodingProblemProps> = ({
  codingProblem,
  onNextProblem,
  onTrySimilar,
}) => {
  const [userOutput, setUserOutput] = useState(codingProblem.userOutput || '40.81');
  const [reported, setReported] = useState(false);

  return (
    <div className="max-w-[840px] mx-auto px-6 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider"
            style={{ backgroundColor: '#C0E8F9', color: '#1A281F' }}
          >
            Python 3 · CS 21
          </span>
          <span className="text-xs text-[#635255]">
            Code Output Evaluation
          </span>
        </div>
        <span className="text-xs font-bold text-[#1A281F]">
          Problem 2 of 6
        </span>
      </div>

      {/* Main Coding Card */}
      <Card className="p-7 md:p-8 space-y-6">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-[#635255] flex items-center gap-1.5">
            <Code className="w-3.5 h-3.5" strokeWidth={2} />
            <span>Predict the output</span>
          </span>
          <h2 className="font-heading text-lg md:text-xl font-bold tracking-tight text-[#1A281F] mt-2 leading-relaxed">
            {codingProblem.task}
          </h2>
        </div>

        {/* Syntax-Highlighted Code Block (Monospace, light background) */}
        <div
          className="rounded-xl border overflow-hidden"
          style={{ backgroundColor: '#F3FAF8', borderColor: '#B8D3D1' }}
        >
          <div
            className="px-4 py-2 border-b flex items-center justify-between text-xs font-mono text-[#635255]"
            style={{ backgroundColor: '#FFFFFF', borderColor: '#B8D3D1' }}
          >
            <div className="flex items-center gap-2">
              <Terminal className="w-3.5 h-3.5 text-[#1A281F]" />
              <span>kinematics_sim.py</span>
            </div>
            <span>Python 3.11</span>
          </div>

          <pre className="p-5 font-code text-xs md:text-sm leading-relaxed overflow-x-auto text-[#1A281F]">
            <code>
              <span className="text-[#635255] font-semibold">import</span> math{'\n\n'}
              <span className="text-[#635255] font-semibold">def</span>{' '}
              <span className="font-bold">calculate_range</span>(v0, angle_deg, g=
              <span className="text-[#1A281F] font-bold">9.8</span>):{'\n'}
              {'    '}
              <span className="text-[#635255] italic"># Formula: R = (v0² * sin(2θ)) / g</span>{'\n'}
              {'    '}theta = math.radians(angle_deg){'\n'}
              {'    '}range_m = (v0 ** <span className="font-bold">2</span>) * math.sin(
              <span className="font-bold">2</span> * theta) / g{'\n'}
              {'    '}
              <span className="text-[#635255] font-semibold">return</span> round(range_m,{' '}
              <span className="font-bold">1</span>){'\n\n'}
              <span className="text-[#635255] font-semibold">print</span>(calculate_range(
              <span className="font-bold">20</span>, <span className="font-bold">45</span>))
            </code>
          </pre>
        </div>

        {/* Monospace multiline answer box */}
        <div className="space-y-2">
          <label className="block text-xs font-semibold text-[#1A281F]">
            Predicted Standard Output (stdout):
          </label>
          <textarea
            rows={2}
            value={userOutput}
            onChange={(e) => setUserOutput(e.target.value)}
            placeholder="Type console output exactly..."
            className="w-full p-3.5 rounded-xl font-code text-sm border focus:outline-none focus:ring-1 focus:ring-[#1A281F]"
            style={{
              borderColor: '#635255',
              backgroundColor: '#FFFFFF',
              color: '#1A281F',
            }}
          />
        </div>

        {/* Result banner: "Not quite", feedback naming mistake, "Correct answer: 40.8" */}
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
                Not quite
              </span>
            </div>
            <span
              className="px-2.5 py-0.5 rounded text-xs font-bold border font-code"
              style={{
                backgroundColor: '#A7E8BD',
                color: '#1A281F',
                borderColor: '#1A281F',
              }}
            >
              Correct output: {codingProblem.expectedOutput}
            </span>
          </div>

          <p className="text-xs text-[#1A281F] leading-relaxed">
            You entered <code className="font-code font-bold">40.81</code>. Notice that{' '}
            <code className="font-code font-bold">round(range_m, 1)</code> limits precision to 1 decimal place. Although 400 / 9.8 is approximately 40.816, the Python interpreter rounds to a single decimal digit, printing <code className="font-code font-bold">40.8</code>.
          </p>
        </div>

        {/* Explanation Card */}
        <div
          className="p-4 rounded-xl border space-y-1.5"
          style={{ backgroundColor: '#F3FAF8', borderColor: '#B8D3D1' }}
        >
          <span className="text-xs font-bold uppercase tracking-wider text-[#1A281F] flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Logic Analysis</span>
          </span>
          <p className="text-xs leading-relaxed text-[#635255]">
            {codingProblem.explanation}
          </p>
        </div>

        {/* Action Buttons */}
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
