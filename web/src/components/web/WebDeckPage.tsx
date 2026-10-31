import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import { Chip } from '../common/Chip';
import { Flashcard, DeckItem } from '../../types';
import {
  Play,
  Award,
  Calculator,
  Bookmark,
  ExternalLink,
  Sparkles,
  ChevronRight,
  Plus,
  BookOpen,
  Filter,
} from 'lucide-react';

interface WebDeckPageProps {
  deck: DeckItem;
  flashcards: Flashcard[];
  onStartReview: () => void;
  onStartQuiz: () => void;
  onPracticeProblems: () => void;
  onCodingProblemClick: () => void;
}

export const WebDeckPage: React.FC<WebDeckPageProps> = ({
  deck,
  flashcards: initialFlashcards,
  onStartReview,
  onStartQuiz,
  onPracticeProblems,
  onCodingProblemClick,
}) => {
  const [activeTab, setActiveTab] = useState<'flashcards' | 'quiz' | 'problems'>('flashcards');
  const [cards, setCards] = useState(initialFlashcards);
  const [selectedTopicToGenerate, setSelectedTopicToGenerate] = useState('Electron Transport Chain');
  const [isGeneratingTopic, setIsGeneratingTopic] = useState(false);
  const [addedTopicMessage, setAddedTopicMessage] = useState(false);

  const toggleFlag = (cardId: string) => {
    setCards((prev) =>
      prev.map((c) => (c.id === cardId ? { ...c, isFlagged: !c.isFlagged } : c))
    );
  };

  const handleGenerateMoreOnTopic = () => {
    setIsGeneratingTopic(true);
    setTimeout(() => {
      setIsGeneratingTopic(false);
      setAddedTopicMessage(true);
      setTimeout(() => setAddedTopicMessage(false), 3000);
    }, 700);
  };

  return (
    <div className="max-w-[1280px] mx-auto px-6 py-8 space-y-8">
      {/* 1. Deck Header Card */}
      <Card className="p-7 md:p-8 space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <span
                className="px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider"
                style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
              >
                {deck.subject}
              </span>
              <span className="text-xs text-[#635255]">
                {deck.source}
              </span>
            </div>

            <h1 className="font-heading text-3xl md:text-4xl font-bold tracking-tight text-[#1A281F]">
              {deck.title}
            </h1>

            <div className="flex items-center gap-3 text-xs text-[#635255]">
              <span>{cards.length} flashcards</span>
              <span>·</span>
              <span>12 quiz questions</span>
              <span>·</span>
              <span>6 STEM problem sets</span>
              <span>·</span>
              <span className="font-semibold text-[#1A281F]">{deck.masteryPercentage}% mastery</span>
            </div>
          </div>

          {/* Action buttons: Review N due / Start quiz / Practice problems */}
          <div className="flex flex-wrap items-center gap-3 shrink-0">
            <Button
              variant="primary"
              size="lg"
              onClick={onStartReview}
              icon={<Play className="w-4 h-4 fill-white" />}
            >
              Review {deck.dueCards} due
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={onStartQuiz}
              icon={<Award className="w-4 h-4" />}
            >
              Start quiz
            </Button>
            <Button
              variant="outline"
              size="lg"
              onClick={onPracticeProblems}
              icon={<Calculator className="w-4 h-4" />}
            >
              Practice problems
            </Button>
          </div>
        </div>

        {/* 2. "Need more on one topic?" Generate-by-Topic Bar */}
        <div
          className="p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3"
          style={{ backgroundColor: '#F3FAF8', borderColor: '#B8D3D1' }}
        >
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-[#1A281F] shrink-0" strokeWidth={2} />
            <span className="text-xs font-semibold text-[#1A281F]">
              Need more on one topic?
            </span>
            <span className="text-xs text-[#635255] hidden md:inline">
              Generate targeted questions for harder sections.
            </span>
          </div>

          <div className="flex items-center gap-2">
            <select
              value={selectedTopicToGenerate}
              onChange={(e) => setSelectedTopicToGenerate(e.target.value)}
              className="text-xs font-medium px-3 py-1.5 rounded-lg border bg-white text-[#1A281F] border-[#B8D3D1] focus:outline-none cursor-pointer"
            >
              <option value="Electron Transport Chain">Electron Transport Chain</option>
              <option value="Glycolysis">Glycolysis &amp; Substrate Level</option>
              <option value="Krebs Cycle">Citric Acid (Krebs) Cycle</option>
              <option value="Chemiosmosis">Chemiosmosis &amp; ATP Synthase</option>
            </select>

            <button
              type="button"
              disabled={isGeneratingTopic}
              onClick={handleGenerateMoreOnTopic}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer whitespace-nowrap active:scale-95"
              style={{ backgroundColor: '#1A281F', color: '#FFFFFF' }}
            >
              {isGeneratingTopic ? 'Generating...' : '+ Generate 5 cards'}
            </button>
          </div>
        </div>

        {addedTopicMessage && (
          <div
            className="p-2.5 rounded-lg text-xs font-semibold text-[#1A281F] border flex items-center gap-2"
            style={{ backgroundColor: '#A7E8BD', borderColor: '#1A281F' }}
          >
            <span>Success: 5 new targeted flashcards on "{selectedTopicToGenerate}" added to deck!</span>
          </div>
        )}
      </Card>

      {/* 3. Tabs: Flashcards · Quiz questions · Problem set */}
      <div className="space-y-6">
        <div className="flex items-center justify-between border-b border-[#B8D3D1] pb-2">
          <div className="flex items-center gap-6">
            <button
              type="button"
              onClick={() => setActiveTab('flashcards')}
              className={`pb-2 text-sm font-semibold transition-all cursor-pointer flex items-center gap-2 border-b-2 ${
                activeTab === 'flashcards'
                  ? 'border-[#1A281F] text-[#1A281F]'
                  : 'border-transparent text-[#635255] hover:text-[#1A281F]'
              }`}
            >
              <span>Flashcards</span>
              <span
                className="px-2 py-0.2 rounded-full text-xs font-bold"
                style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
              >
                {cards.length}
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('quiz')}
              className={`pb-2 text-sm font-semibold transition-all cursor-pointer flex items-center gap-2 border-b-2 ${
                activeTab === 'quiz'
                  ? 'border-[#1A281F] text-[#1A281F]'
                  : 'border-transparent text-[#635255] hover:text-[#1A281F]'
              }`}
            >
              <span>Quiz questions</span>
              <span
                className="px-2 py-0.2 rounded-full text-xs font-bold"
                style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
              >
                12
              </span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('problems')}
              className={`pb-2 text-sm font-semibold transition-all cursor-pointer flex items-center gap-2 border-b-2 ${
                activeTab === 'problems'
                  ? 'border-[#1A281F] text-[#1A281F]'
                  : 'border-transparent text-[#635255] hover:text-[#1A281F]'
              }`}
            >
              <span>Problem set</span>
              <span
                className="px-2 py-0.2 rounded-full text-xs font-bold"
                style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
              >
                6
              </span>
            </button>
          </div>

          <div className="text-xs text-[#635255] hidden sm:block">
            Showing all items in current deck
          </div>
        </div>

        {/* Tab Content: Flashcards Card Grid */}
        {activeTab === 'flashcards' && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {cards.map((card, index) => (
              <Card
                key={card.id}
                className="p-5 flex flex-col justify-between hover:border-[#1A281F] transition-all group"
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between gap-2">
                    {/* Topic label: Pale Sky / Frozen Water */}
                    <span
                      className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold"
                      style={{ backgroundColor: '#C0E8F9', color: '#1A281F' }}
                    >
                      {card.topic}
                    </span>

                    <button
                      type="button"
                      onClick={() => toggleFlag(card.id)}
                      className={`p-1 rounded-md transition-colors cursor-pointer ${
                        card.isFlagged
                          ? 'text-[#CE7B91] fill-[#CE7B91]'
                          : 'text-[#635255] hover:text-[#1A281F]'
                      }`}
                      title={card.isFlagged ? 'Flagged for priority review' : 'Flag card'}
                    >
                      <Bookmark
                        className="w-4 h-4"
                        strokeWidth={2}
                        fill={card.isFlagged ? '#CE7B91' : 'none'}
                      />
                    </button>
                  </div>

                  <div>
                    <h3 className="font-heading text-sm font-bold tracking-tight text-[#1A281F] leading-snug">
                      {card.question}
                    </h3>
                  </div>

                  <div className="pt-2 border-t border-[#B8D3D1]">
                    <p className="text-xs leading-relaxed text-[#1A281F]">
                      {card.answer}
                    </p>
                  </div>
                </div>

                {/* Card footer: Source link */}
                <div className="mt-4 pt-3 border-t border-[#B8D3D1] flex items-center justify-between text-[11px]">
                  <a
                    href="#source"
                    onClick={(e) => e.preventDefault()}
                    className="font-medium text-[#635255] hover:text-[#1A281F] flex items-center gap-1 hover:underline"
                  >
                    <span>{card.sourceRef}</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                  <span className="text-[#635255]">Card #{index + 1}</span>
                </div>
              </Card>
            ))}
          </div>
        )}

        {/* Tab Content: Quiz Questions Quick View */}
        {activeTab === 'quiz' && (
          <div className="space-y-4">
            <Card className="p-6 flex items-center justify-between">
              <div>
                <h3 className="font-heading text-base font-bold text-[#1A281F]">
                  12 Multiple-Choice Questions Ready
                </h3>
                <p className="text-xs text-[#635255] mt-0.5">
                  Includes answer-specific feedback and instant misconception analysis.
                </p>
              </div>
              <Button variant="primary" onClick={onStartQuiz} icon={<Play className="w-4 h-4 fill-white" />}>
                Launch Quiz Simulator
              </Button>
            </Card>
          </div>
        )}

        {/* Tab Content: Problem Sets Quick View */}
        {activeTab === 'problems' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Card className="p-6 space-y-4">
              <div>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-[#C7EAE4] text-[#1A281F]">
                  Physics &amp; Chemistry Calculation
                </span>
                <h3 className="font-heading text-base font-bold text-[#1A281F] mt-2">
                  Kinematics &amp; Reaction Rates Auto-Graded
                </h3>
                <p className="text-xs text-[#635255] mt-1 leading-relaxed">
                  Interactive input parsing with number extraction, common misconception diagnostic, and worked solutions.
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={onPracticeProblems}>
                Practice Kinematics Problem
              </Button>
            </Card>

            <Card className="p-6 space-y-4">
              <div>
                <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-[#C0E8F9] text-[#1A281F]">
                  Programming &amp; Logic
                </span>
                <h3 className="font-heading text-base font-bold text-[#1A281F] mt-2">
                  Predict-the-Output Code Analysis
                </h3>
                <p className="text-xs text-[#635255] mt-1 leading-relaxed">
                  Monospace code sandbox testing function returns, loops, and math simulation logic.
                </p>
              </div>
              <Button variant="outline" size="sm" onClick={onCodingProblemClick}>
                Practice Coding Problem
              </Button>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};
