import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import {
  Calendar as CalendarIcon,
  ChevronLeft,
  ChevronRight,
  Clock,
  BookOpen,
  CheckCircle2,
  Sparkles,
  Layers,
  ArrowRight,
} from 'lucide-react';

export type ActivityLevel = 'none' | 'light' | 'moderate' | 'high';

export interface PlannedSession {
  id: string;
  deckTitle: string;
  subject: string;
  dueCards: number;
  timeEstimateMins: number;
  isExamPrep?: boolean;
}

export interface CalendarDayData {
  date: number; // 1-30
  month: number; // 10 for November (0-indexed) or 11
  year: number; // 2026
  dayOfWeek: number; // 0 for Sun, 1 for Mon...
  activityLevel: ActivityLevel;
  totalCardsDue: number;
  completed?: boolean;
  isToday?: boolean;
  sessions: PlannedSession[];
}

// Generate realistic mock study schedule for November 2026
const generateNovember2026Data = (): CalendarDayData[] => {
  const days: CalendarDayData[] = [];

  // Nov 2026 starts on Sunday (day 0) and has 30 days
  for (let d = 1; d <= 30; d++) {
    const dayOfWeek = (d - 1) % 7; // Nov 1 = Sun (0), Nov 2 = Mon (1), etc.
    let activityLevel: ActivityLevel = 'light';
    let totalCardsDue = 0;
    const sessions: PlannedSession[] = [];
    const isToday = d === 2; // Nov 2, 2026 based on metadata
    const isPast = d < 2;

    // Distribute realistic planned sessions
    if (d === 2) {
      // Today: 24 cards due across 3 decks (matches dashboard hero)
      activityLevel = 'high';
      totalCardsDue = 24;
      sessions.push(
        { id: `s-${d}-1`, deckTitle: 'Biology 101 · Cellular Respiration', subject: 'Biology', dueCards: 12, timeEstimateMins: 6 },
        { id: `s-${d}-2`, deckTitle: 'Philippine History · Week 4', subject: 'History', dueCards: 8, timeEstimateMins: 4 },
        { id: `s-${d}-3`, deckTitle: 'Physics 1 · Kinematics', subject: 'Physics', dueCards: 4, timeEstimateMins: 2 }
      );
    } else if (d === 5 || d === 12 || d === 19 || d === 26) {
      // Thursdays: High study activity (Pre-weekend review / quiz prep)
      activityLevel = 'high';
      totalCardsDue = 32;
      sessions.push(
        { id: `s-${d}-1`, deckTitle: 'Biology 101 · Midterm Review Batch', subject: 'Biology', dueCards: 18, timeEstimateMins: 10, isExamPrep: true },
        { id: `s-${d}-2`, deckTitle: 'Physics 1 · Kinematics Problem Set', subject: 'Physics', dueCards: 14, timeEstimateMins: 8 }
      );
    } else if (d === 10 || d === 17 || d === 24) {
      // Tuesdays: Moderate study activity
      activityLevel = 'moderate';
      totalCardsDue = 16;
      sessions.push(
        { id: `s-${d}-1`, deckTitle: 'Philippine History · Katipunan to Biak-na-Bato', subject: 'History', dueCards: 10, timeEstimateMins: 5 },
        { id: `s-${d}-2`, deckTitle: 'Chemistry 16 · Le Chatelier Equilibrium', subject: 'Chemistry', dueCards: 6, timeEstimateMins: 4 }
      );
    } else if (d === 8 || d === 15 || d === 22 || d === 29) {
      // Sundays: Light consolidation
      activityLevel = 'light';
      totalCardsDue = 8;
      sessions.push(
        { id: `s-${d}-1`, deckTitle: 'CS 21 · Python Output Review', subject: 'CS', dueCards: 8, timeEstimateMins: 4 }
      );
    } else if (d === 6 || d === 13 || d === 20 || d === 27) {
      // Fridays: Moderate
      activityLevel = 'moderate';
      totalCardsDue = 18;
      sessions.push(
        { id: `s-${d}-1`, deckTitle: 'Biology 101 · Glycolysis & Krebs Drills', subject: 'Biology', dueCards: 12, timeEstimateMins: 6 },
        { id: `s-${d}-2`, deckTitle: 'Philippine History · Tejeros Convention', subject: 'History', dueCards: 6, timeEstimateMins: 3 }
      );
    } else if (d === 1 || d === 7 || d === 14 || d === 21 || d === 28) {
      // Rest or very light
      activityLevel = 'light';
      totalCardsDue = 6;
      sessions.push(
        { id: `s-${d}-1`, deckTitle: 'Spaced Recall Maintenance', subject: 'General', dueCards: 6, timeEstimateMins: 3 }
      );
    } else {
      activityLevel = 'light';
      totalCardsDue = 10;
      sessions.push(
        { id: `s-${d}-1`, deckTitle: 'Physics 1 · Uniform Acceleration', subject: 'Physics', dueCards: 10, timeEstimateMins: 5 }
      );
    }

    days.push({
      date: d,
      month: 10, // November
      year: 2026,
      dayOfWeek,
      activityLevel,
      totalCardsDue,
      completed: isPast,
      isToday,
      sessions,
    });
  }

  return days;
};

interface StudyCalendarProps {
  onStartReviewForDay?: (day: CalendarDayData) => void;
  className?: string;
}

export const StudyCalendar: React.FC<StudyCalendarProps> = ({
  onStartReviewForDay,
  className = '',
}) => {
  const [calendarData] = useState<CalendarDayData[]>(generateNovember2026Data());
  const [selectedDayNumber, setSelectedDayNumber] = useState<number>(2); // Default to today (Nov 2)
  const [filterLevel, setFilterLevel] = useState<ActivityLevel | 'all'>('all');

  const selectedDay =
    calendarData.find((d) => d.date === selectedDayNumber) || calendarData[1];

  const weekDayHeaders = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  // Activity level styling conforming to Kabisado exact palette
  // High activity: subtle Celadon (#A7E8BD) background with Evergreen (#1A281F) text and Jasmine (#FFD972) dot
  // Moderate activity: soft Frozen Water (#C7EAE4) with Evergreen (#1A281F) text
  // Light activity: white background with subtle border
  const getActivityTileStyle = (day: CalendarDayData, isSelected: boolean) => {
    let backgroundColor = '#FFFFFF';
    let borderColor = '#B8D3D1';
    let textColor = '#1A281F';

    if (day.isToday) {
      borderColor = '#1A281F';
    }

    if (day.activityLevel === 'high') {
      backgroundColor = '#A7E8BD'; // Celadon
    } else if (day.activityLevel === 'moderate') {
      backgroundColor = '#C7EAE4'; // Frozen Water
    } else {
      backgroundColor = '#FFFFFF';
    }

    if (isSelected) {
      borderColor = '#1A281F';
    }

    return {
      backgroundColor,
      borderColor,
      color: textColor,
    };
  };

  const filteredDays = calendarData.filter((d) =>
    filterLevel === 'all' ? true : d.activityLevel === filterLevel
  );

  return (
    <Card
      className={`p-6 md:p-8 space-y-6 transition-all ${className}`}
      style={{
        backgroundColor: '#FFFFFF',
        borderColor: '#B8D3D1',
      }}
    >
      {/* 1. Header with Month Title, Legend, and Navigation */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 pb-4 border-b border-[#B8D3D1]">
        <div>
          <div className="flex items-center gap-2">
            <span
              className="px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider"
              style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
            >
              Planned Reviews
            </span>
            <span className="text-xs text-[#635255]">
              Spaced repetition schedule (SM-2)
            </span>
          </div>

          <div className="flex items-center gap-3 mt-1.5">
            <h2 className="font-heading text-2xl font-bold tracking-tight text-[#1A281F]">
              November 2026
            </h2>
            <span
              className="px-2 py-0.5 rounded-full text-xs font-semibold"
              style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
            >
              Today: Nov 2
            </span>
          </div>
        </div>

        {/* Legend for subtle color-coded activity levels */}
        <div className="flex flex-wrap items-center gap-4 text-xs font-medium text-[#635255]">
          <div className="flex items-center gap-1.5">
            <span
              className="w-3.5 h-3.5 rounded border"
              style={{ backgroundColor: '#FFFFFF', borderColor: '#B8D3D1' }}
            />
            <span>Light (&lt;12 cards)</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span
              className="w-3.5 h-3.5 rounded border"
              style={{ backgroundColor: '#C7EAE4', borderColor: '#B8D3D1' }}
            />
            <span>Moderate (12–20 cards)</span>
          </div>

          <div className="flex items-center gap-1.5">
            <span
              className="w-3.5 h-3.5 rounded border"
              style={{ backgroundColor: '#A7E8BD', borderColor: '#1A281F' }}
            />
            <span className="font-semibold text-[#1A281F]">High activity (&gt;20 cards)</span>
          </div>

          {/* Month Switcher Controls */}
          <div className="flex items-center gap-1 ml-auto">
            <button
              type="button"
              className="p-1.5 rounded-lg border bg-white hover:bg-[#F3FAF8] text-[#1A281F] cursor-pointer"
              style={{ borderColor: '#B8D3D1' }}
              title="Previous month (October 2026)"
            >
              <ChevronLeft className="w-4 h-4" strokeWidth={2} />
            </button>
            <button
              type="button"
              className="p-1.5 rounded-lg border bg-white hover:bg-[#F3FAF8] text-[#1A281F] cursor-pointer"
              style={{ borderColor: '#B8D3D1' }}
              title="Next month (December 2026)"
            >
              <ChevronRight className="w-4 h-4" strokeWidth={2} />
            </button>
          </div>
        </div>
      </div>

      {/* 2. Main Layout: Monthly Calendar Grid (8 cols) + Selected Day Review Plan (4 cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left Column: Calendar Grid */}
        <div className="lg:col-span-8 space-y-3">
          {/* Day of Week Headers */}
          <div className="grid grid-cols-7 gap-2 text-center text-xs font-bold text-[#635255]">
            {weekDayHeaders.map((day) => (
              <div key={day} className="py-1">
                {day}
              </div>
            ))}
          </div>

          {/* 30 Day Cells (Nov 1 is Sunday, index 0) */}
          <div className="grid grid-cols-7 gap-2 select-none">
            {calendarData.map((day) => {
              const isSelected = day.date === selectedDayNumber;
              const style = getActivityTileStyle(day, isSelected);

              return (
                <button
                  key={day.date}
                  type="button"
                  onClick={() => setSelectedDayNumber(day.date)}
                  className={`min-h-[72px] sm:min-h-[82px] p-2 rounded-xl border text-left flex flex-col justify-between transition-all cursor-pointer relative active:scale-[0.98] ${
                    isSelected ? 'ring-2 ring-[#1A281F] shadow-xs' : 'hover:border-[#1A281F]'
                  }`}
                  style={style}
                >
                  {/* Top row in day cell: Date number & Today dot */}
                  <div className="flex items-center justify-between w-full">
                    <span
                      className={`font-heading text-xs sm:text-sm font-bold tabular-nums ${
                        day.isToday ? 'px-1.5 py-0.2 rounded-md bg-[#1A281F] text-white' : ''
                      }`}
                    >
                      {day.date}
                    </span>

                    {/* High activity badge or completed check */}
                    {day.activityLevel === 'high' && (
                      <span
                        className="w-2 h-2 rounded-full"
                        style={{ backgroundColor: '#FFD972' }}
                        title="High review load"
                      />
                    )}
                  </div>

                  {/* Bottom info: Cards scheduled & session count */}
                  <div className="space-y-0.5">
                    <p className="text-[11px] font-semibold truncate leading-tight text-[#1A281F]">
                      {day.totalCardsDue} cards
                    </p>
                    <p className="text-[10px] text-[#635255] hidden sm:block truncate">
                      {day.sessions.length} {day.sessions.length === 1 ? 'deck' : 'decks'}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>

          {/* Quick Filter buttons */}
          <div className="pt-2 flex items-center justify-between text-xs text-[#635255]">
            <span className="font-medium">Filter view:</span>
            <div className="flex items-center gap-1.5">
              {(['all', 'high', 'moderate', 'light'] as const).map((lvl) => (
                <button
                  key={lvl}
                  type="button"
                  onClick={() => setFilterLevel(lvl)}
                  className={`px-2.5 py-1 rounded-lg text-xs font-semibold capitalize transition-all cursor-pointer border ${
                    filterLevel === lvl
                      ? 'bg-[#1A281F] text-white border-[#1A281F]'
                      : 'bg-white text-[#635255] border-[#B8D3D1] hover:bg-[#F3FAF8]'
                  }`}
                >
                  {lvl === 'all' ? 'All Days' : `${lvl} load`}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: Selected Day Detail Panel */}
        <div
          className="lg:col-span-4 rounded-[16px] p-5 border space-y-4"
          style={{
            backgroundColor: '#F3FAF8',
            borderColor: '#B8D3D1',
          }}
        >
          {/* Day Detail Header */}
          <div className="flex items-start justify-between pb-3 border-b border-[#B8D3D1]">
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-xs font-semibold text-[#635255]">
                  November {selectedDay.date}, 2026
                </span>
                {selectedDay.isToday && (
                  <span
                    className="px-1.5 py-0.2 rounded text-[10px] font-bold"
                    style={{ backgroundColor: '#1A281F', color: '#FFFFFF' }}
                  >
                    Today
                  </span>
                )}
              </div>
              <h3 className="font-heading text-xl font-bold tracking-tight text-[#1A281F] mt-0.5">
                {selectedDay.totalCardsDue} Cards Planned
              </h3>
            </div>

            {/* Activity Pill */}
            <span
              className="px-2.5 py-0.5 rounded-full text-xs font-bold border capitalize"
              style={{
                backgroundColor:
                  selectedDay.activityLevel === 'high'
                    ? '#A7E8BD'
                    : selectedDay.activityLevel === 'moderate'
                    ? '#C7EAE4'
                    : '#FFFFFF',
                color: '#1A281F',
                borderColor: selectedDay.activityLevel === 'high' ? '#1A281F' : '#B8D3D1',
              }}
            >
              {selectedDay.activityLevel} load
            </span>
          </div>

          {/* Time Estimate & Status */}
          <div className="flex items-center justify-between text-xs text-[#635255]">
            <span className="flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 text-[#1A281F]" />
              <span>
                Est.{' '}
                {selectedDay.sessions.reduce((acc, s) => acc + s.timeEstimateMins, 0)}{' '}
                minutes
              </span>
            </span>
            <span>{selectedDay.sessions.length} scheduled sessions</span>
          </div>

          {/* Planned Sessions List */}
          <div className="space-y-2.5">
            {selectedDay.sessions.map((session) => (
              <div
                key={session.id}
                className="p-3.5 rounded-xl border bg-white space-y-2 shadow-2xs"
                style={{ borderColor: '#B8D3D1' }}
              >
                <div className="flex items-center justify-between">
                  <span
                    className="px-2 py-0.2 rounded text-[10px] font-semibold uppercase tracking-wide"
                    style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
                  >
                    {session.subject}
                  </span>
                  {session.isExamPrep && (
                    <span
                      className="px-2 py-0.2 rounded text-[10px] font-bold"
                      style={{ backgroundColor: '#FFD972', color: '#1A281F' }}
                    >
                      Exam Prep
                    </span>
                  )}
                </div>

                <h4 className="font-heading text-xs sm:text-sm font-bold text-[#1A281F] leading-snug">
                  {session.deckTitle}
                </h4>

                <div className="flex items-center justify-between text-[11px] text-[#635255] pt-1 border-t border-[#B8D3D1]">
                  <span>{session.dueCards} cards due</span>
                  <span>~{session.timeEstimateMins} mins</span>
                </div>
              </div>
            ))}
          </div>

          {/* Action Button for the Selected Day */}
          <div className="pt-2">
            <Button
              variant="primary"
              size="md"
              fullWidth
              onClick={() => onStartReviewForDay?.(selectedDay)}
              icon={<ArrowRight className="w-4 h-4" />}
              iconPosition="right"
            >
              {selectedDay.isToday ? 'Start today’s review' : `Review Nov ${selectedDay.date} batch`}
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
};
