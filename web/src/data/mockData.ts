import {
  DeckItem,
  Flashcard,
  QuizQuestionItem,
  ProblemItemData,
  CodingProblemData,
  WeakTopic,
} from '../types';

export const MOCK_DECKS: DeckItem[] = [
  {
    id: 'deck-1',
    title: 'Biology 101 · Cellular Respiration',
    subject: 'Biology',
    source: 'Campbell Biology Ch. 9 (Uploaded 2 days ago · 38 pages)',
    totalPages: 38,
    totalCards: 28,
    dueCards: 12,
    masteryPercentage: 68,
    status: 'ready',
    lastStudied: 'Yesterday, 8:45 PM',
  },
  {
    id: 'deck-2',
    title: 'Philippine History · Week 4',
    subject: 'History',
    source: 'Teodoro Agoncillo notes · Tejeros to Malolos (Uploaded 4 days ago · 24 pages)',
    totalPages: 24,
    totalCards: 22,
    dueCards: 8,
    masteryPercentage: 82,
    status: 'ready',
    lastStudied: '3 days ago',
  },
  {
    id: 'deck-3',
    title: 'Physics 1 · Kinematics',
    subject: 'Physics',
    source: 'Halliday & Resnick Ch. 2-4 (Uploaded 1 week ago · 45 pages)',
    totalPages: 45,
    totalCards: 18,
    dueCards: 4,
    masteryPercentage: 54,
    status: 'ready',
    lastStudied: '5 days ago',
  },
  {
    id: 'deck-4',
    title: 'Chemistry 16 · Chemical Equilibrium',
    subject: 'Chemistry',
    source: 'Le Chatelier & Equilibrium Constants PDF (19 pages)',
    totalPages: 19,
    totalCards: 16,
    dueCards: 0,
    masteryPercentage: 0,
    status: 'generating',
    generatingProgress: 64, // using Old Rose progress as requested
  },
];

export const MOCK_WEAK_TOPICS: WeakTopic[] = [
  {
    id: 'wt-1',
    name: 'Oxidative Phosphorylation & ATP Synthase',
    deckName: 'Biology 101',
    accuracy: 42,
    dueCount: 7,
  },
  {
    id: 'wt-2',
    name: 'Two-Dimensional Projectile Motion',
    deckName: 'Physics 1',
    accuracy: 50,
    dueCount: 5,
  },
  {
    id: 'wt-3',
    name: 'Pact of Biak-na-Bato & Truce Terms',
    deckName: 'Philippine History',
    accuracy: 58,
    dueCount: 4,
  },
];

export const MOCK_FLASHCARDS: Flashcard[] = [
  {
    id: 'fc-1',
    deckId: 'deck-1',
    topic: 'Electron Transport Chain',
    question: 'What is the primary role of molecular oxygen (O₂) in the mitochondrial electron transport chain?',
    answer: 'It acts as the final electron acceptor in the electron transport chain, binding with free protons to produce water (H₂O) and maintaining the chemiosmotic gradient.',
    highlightedKeyword: 'final electron acceptor',
    sourceRef: 'Campbell Biology · Ch. 9, p. 172',
    pageNumber: 172,
    isFlagged: false,
  },
  {
    id: 'fc-2',
    deckId: 'deck-1',
    topic: 'Glycolysis',
    question: 'Where does glycolysis take place in eukaryotic cells, and what is the net yield of ATP per glucose?',
    answer: 'Glycolysis occurs in the cytosol and yields a net of 2 ATP (via substrate-level phosphorylation) and 2 NADH molecules per molecule of glucose.',
    highlightedKeyword: 'cytosol',
    sourceRef: 'Campbell Biology · Ch. 9, p. 165',
    pageNumber: 165,
    isFlagged: true,
  },
  {
    id: 'fc-3',
    deckId: 'deck-1',
    topic: 'Krebs Cycle',
    question: 'Which four-carbon molecule condenses with acetyl-CoA in the first step of the citric acid cycle?',
    answer: 'Oxaloacetate combines with the acetyl group from acetyl-CoA to form citrate, regenerated through successive oxidation steps.',
    highlightedKeyword: 'Oxaloacetate',
    sourceRef: 'Campbell Biology · Ch. 9, p. 169',
    pageNumber: 169,
    isFlagged: false,
  },
  {
    id: 'fc-4',
    deckId: 'deck-1',
    topic: 'Chemiosmosis',
    question: 'How does ATP synthase utilize the proton-motive force across the inner mitochondrial membrane?',
    answer: 'Protons flow through the stator down their electrochemical gradient, causing the rotor and catalytic knob to spin, phosphorylating ADP into ATP.',
    highlightedKeyword: 'electrochemical gradient',
    sourceRef: 'Campbell Biology · Ch. 9, p. 174',
    pageNumber: 174,
    isFlagged: false,
  },
  {
    id: 'fc-5',
    deckId: 'deck-1',
    topic: 'Fermentation',
    question: 'Why must cells perform fermentation under anaerobic conditions if no ATP is directly made in the recycling step?',
    answer: 'Fermentation oxidizes NADH back to NAD⁺, which is required as an electron carrier to allow glycolysis to continue producing ATP.',
    highlightedKeyword: 'regenerates NAD⁺',
    sourceRef: 'Campbell Biology · Ch. 9, p. 178',
    pageNumber: 178,
    isFlagged: false,
  },
  {
    id: 'fc-6',
    deckId: 'deck-1',
    topic: 'Pyruvate Oxidation',
    question: 'What multi-enzyme complex converts pyruvate to acetyl-CoA before entry into the mitochondrial matrix?',
    answer: 'The pyruvate dehydrogenase complex removes a carboxyl group as CO₂, reduces NAD⁺ to NADH, and attaches coenzyme A.',
    highlightedKeyword: 'pyruvate dehydrogenase',
    sourceRef: 'Campbell Biology · Ch. 9, p. 168',
    pageNumber: 168,
    isFlagged: false,
  },
];

export const MOCK_QUIZ_QUESTION: QuizQuestionItem = {
  id: 'q-101',
  question: 'Which stage of cellular respiration produces the greatest net yield of ATP per single glucose molecule?',
  options: [
    { id: 'opt-a', label: 'A', text: 'Glycolysis' },
    { id: 'opt-b', label: 'B', text: 'Pyruvate oxidation to acetyl-CoA' },
    { id: 'opt-c', label: 'C', text: 'Citric Acid (Krebs) cycle' },
    { id: 'opt-d', label: 'D', text: 'Oxidative phosphorylation (electron transport and chemiosmosis)' },
  ],
  correctOptionId: 'opt-d',
  userSelectedOptionId: 'opt-c', // Wrong answer chosen to show the exact answered state requested
  explanation: 'Oxidative phosphorylation accounts for roughly 26 to 28 of the 30–32 ATP generated per glucose molecule, powered by the proton gradient established by the electron transport chain. The Krebs cycle produces only 2 ATP/GTP directly via substrate-level phosphorylation.',
  sourceRef: 'Campbell Biology · Ch. 9, p. 174',
  pageNumber: 174,
  detailedMistakeExplanation: 'You selected the Citric Acid (Krebs) Cycle. While the Krebs cycle generates the majority of electron carriers (6 NADH and 2 FADH₂), it only produces 2 ATP directly via substrate-level phosphorylation. The actual massive ATP payoff occurs later in oxidative phosphorylation when those carriers donate electrons to the ETC.',
};

export const MOCK_QUIZ_RESULTS = {
  score: 7,
  total: 10,
  percentage: 70,
  previousPercentage: 60,
  missedQuestions: [
    {
      id: 'mq-1',
      question: 'Which stage of cellular respiration produces the greatest net yield of ATP?',
      userAnswer: 'Citric Acid (Krebs) cycle',
      correctAnswer: 'Oxidative phosphorylation (chemiosmosis)',
      topic: 'Cellular Respiration',
    },
    {
      id: 'mq-2',
      question: 'What is the immediate electron donor to Complex I of the respiratory chain?',
      userAnswer: 'FADH₂',
      correctAnswer: 'NADH',
      topic: 'Electron Transport Chain',
    },
    {
      id: 'mq-3',
      question: 'In lactic acid fermentation, what molecule receives electrons directly from NADH?',
      userAnswer: 'Acetaldehyde',
      correctAnswer: 'Pyruvate',
      topic: 'Fermentation',
    },
  ],
};

export const MOCK_PROBLEM: ProblemItemData = {
  id: 'prob-101',
  title: 'Uniform Acceleration Kinematics',
  subject: 'Physics 1 · Kinematics',
  questionHtml: 'A sports car starts from rest at a traffic light and accelerates at 3 m/s² for 4 s along a straight highway lane. Calculate the total displacement traveled by the car during this time interval.',
  rawQuestion: 'A sports car starts from rest at a traffic light and accelerates at 3 m/s² for 4 s along a straight highway lane. Calculate the total displacement traveled by the car during this time interval.',
  highlightedValues: ['3 m/s²', '4 s'],
  unit: 'm',
  correctAnswer: '24',
  userAnswer: '48', // User entered 48 without 1/2 factor
  userUnit: 'm',
  statusText: 'Not quite',
  mistakeFeedback: 'You may have dropped the ½ in d = ½at². Remember that when starting from rest (v₀ = 0), displacement is equal to half the acceleration times the time squared: d = v₀t + ½at².',
  hints: [
    'Since the car starts from rest, initial velocity v₀ = 0 m/s.',
    'Use the kinematic equation relating displacement, initial velocity, acceleration, and time: d = v₀t + (1/2)at².',
  ],
  usedHintsCount: 1,
  workedSolution: [
    {
      stepNumber: 1,
      title: 'Identify given variables and constants',
      explanation: 'Initial velocity v₀ = 0 m/s (from rest), acceleration a = 3 m/s², and time interval t = 4 s.',
    },
    {
      stepNumber: 2,
      title: 'Select the appropriate kinematic equation',
      explanation: 'Use the second kinematic equation for uniform acceleration: d = v₀t + ½at².',
    },
    {
      stepNumber: 3,
      title: 'Substitute values and solve for displacement d',
      explanation: 'd = (0)(4) + ½(3 m/s²)(4 s)² = ½(3)(16) = ½(48) = 24 m.',
      formula: 'd = 24 m',
    },
  ],
};

export const MOCK_CODING_PROBLEM: CodingProblemData = {
  id: 'code-101',
  title: 'Python Kinematics · Predict the Output',
  language: 'python',
  task: 'Analyze the projectile motion function below. Predict the exact console output printed when calculate_range(20, 45) is evaluated with default gravitational constant g = 9.8 m/s².',
  codeSnippet: `import math

def calculate_range(v0, angle_deg, g=9.8):
    # R = (v0^2 * sin(2*theta)) / g
    theta = math.radians(angle_deg)
    range_m = (v0 ** 2) * math.sin(2 * theta) / g
    return round(range_m, 1)

print(calculate_range(20, 45))`,
  expectedOutput: '40.8',
  userOutput: '40.81',
  explanation: 'For v₀ = 20 m/s and θ = 45°, 2θ = 90° and sin(90°) = 1.0. Thus R = (20² * 1.0) / 9.8 = 400 / 9.8 ≈ 40.8163... The round(..., 1) built-in limits the precision to exactly 1 decimal place, producing 40.8.',
};
