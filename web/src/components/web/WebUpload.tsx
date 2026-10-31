import React, { useState } from 'react';
import { Card } from '../common/Card';
import { Button } from '../common/Button';
import {
  UploadCloud,
  FileText,
  FileCheck,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  X,
  File,
  CheckCircle2,
} from 'lucide-react';

interface WebUploadProps {
  isFailedUploadState?: boolean;
  onRetryUpload?: () => void;
  onGenerateSuccess: (title: string) => void;
  onCancel: () => void;
}

export const WebUpload: React.FC<WebUploadProps> = ({
  isFailedUploadState = false,
  onRetryUpload,
  onGenerateSuccess,
  onCancel,
}) => {
  const [activeTab, setActiveTab] = useState<'pdf' | 'paste'>('pdf');
  const [deckTitle, setDeckTitle] = useState('Biology 101 · Cellular Respiration');
  const [generationType, setGenerationType] = useState<
    'all' | 'flashcards-quiz' | 'flashcards-only'
  >('all');
  const [pastedNotes, setPastedNotes] = useState(
    `Cellular Respiration Overview:
1. Glycolysis: Takes place in cytoplasm/cytosol. Glucose is broken down into 2 molecules of pyruvate. Yields net 2 ATP and 2 NADH.
2. Pyruvate Oxidation: Pyruvate transported into mitochondrial matrix, converted to Acetyl-CoA by pyruvate dehydrogenase.
3. Krebs Cycle (Citric Acid Cycle): Acetyl-CoA condenses with oxaloacetate to form citrate. Yields 2 ATP, 6 NADH, 2 FADH2 per glucose.
4. Oxidative Phosphorylation: Electron transport chain and chemiosmosis across inner membrane. ATP synthase drives bulk ATP production (~26-28 ATP). Oxygen acts as the final electron acceptor.`
  );
  const [selectedFile, setSelectedFile] = useState<{
    name: string;
    size: string;
    pages: number;
  } | null>({
    name: 'Bio101_Lecture3_CellularRespiration.pdf',
    size: '4.2 MB',
    pages: 38,
  });

  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerate = () => {
    setIsGenerating(true);
    setTimeout(() => {
      setIsGenerating(false);
      onGenerateSuccess(deckTitle);
    }, 800);
  };

  return (
    <div className="max-w-[840px] mx-auto px-6 py-10 space-y-8">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl font-bold tracking-tight text-[#1A281F]">
          Create a new study reviewer
        </h1>
        <p className="mt-1.5 text-[15px] text-[#635255]">
          Upload your lecture slides, syllabus, or handwritten notes to generate active recall study sets.
        </p>
      </div>

      {/* Main Form Card */}
      <Card className="p-7 md:p-8 space-y-6">
        {/* Tab switch */}
        <div
          className="flex items-center p-1 rounded-xl border max-w-sm"
          style={{ backgroundColor: '#F3FAF8', borderColor: '#B8D3D1' }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('pdf')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === 'pdf'
                ? 'bg-[#1A281F] text-white shadow-xs'
                : 'text-[#635255] hover:text-[#1A281F]'
            }`}
          >
            <UploadCloud className="w-3.5 h-3.5" strokeWidth={2} />
            <span>Upload PDF</span>
          </button>
          <button
            type="button"
            onClick={() => setActiveTab('paste')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all cursor-pointer ${
              activeTab === 'paste'
                ? 'bg-[#1A281F] text-white shadow-xs'
                : 'text-[#635255] hover:text-[#1A281F]'
            }`}
          >
            <FileText className="w-3.5 h-3.5" strokeWidth={2} />
            <span>Paste notes</span>
          </button>
        </div>

        {/* Tab 1: Upload PDF */}
        {activeTab === 'pdf' && (
          <div className="space-y-4">
            {isFailedUploadState ? (
              /* Failed upload state banner */
              <div
                className="p-6 rounded-[16px] border space-y-3"
                style={{
                  backgroundColor: '#FCBCB8',
                  borderColor: '#EFA7A7',
                }}
              >
                <div className="flex items-start gap-3">
                  <div
                    className="w-10 h-10 rounded-xl flex items-center justify-center shrink-0"
                    style={{ backgroundColor: '#FFFFFF', color: '#1A281F' }}
                  >
                    <AlertTriangle className="w-5 h-5 text-[#1A281F]" strokeWidth={2} />
                  </div>
                  <div>
                    <h3 className="font-heading text-base font-bold text-[#1A281F]">
                      This looks like a scanned PDF
                    </h3>
                    <p className="text-xs text-[#1A281F] mt-1 leading-relaxed">
                      Kabisado works best with searchable, text-based PDFs. Image-only scans may fail formula parsing. Try exporting as text or paste your raw notes directly.
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3 pt-2">
                  <button
                    type="button"
                    onClick={onRetryUpload}
                    className="px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer"
                    style={{ backgroundColor: '#1A281F', color: '#FFFFFF' }}
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Retry with another file</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('paste')}
                    className="px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer"
                    style={{ backgroundColor: '#FFFFFF', color: '#1A281F', border: '1px solid #1A281F' }}
                  >
                    Switch to Paste notes
                  </button>
                </div>
              </div>
            ) : (
              <>
                {/* Drop Zone: Old Rose (#CE7B91) dashed border */}
                <div
                  className="rounded-[16px] p-8 text-center border-2 border-dashed transition-all hover:bg-[#F3FAF8] flex flex-col items-center justify-center cursor-pointer"
                  style={{
                    borderColor: '#CE7B91',
                    backgroundColor: '#FFFFFF',
                  }}
                  onClick={() =>
                    setSelectedFile({
                      name: 'Bio101_Lecture3_CellularRespiration.pdf',
                      size: '4.2 MB',
                      pages: 38,
                    })
                  }
                >
                  <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center mb-3"
                    style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
                  >
                    <UploadCloud className="w-6 h-6" strokeWidth={2} />
                  </div>
                  <p className="text-sm font-semibold text-[#1A281F]">
                    Click to browse or drag and drop your file here
                  </p>
                  <p className="text-xs text-[#635255] mt-1">
                    Text-based PDFs up to 50 pages (Max file size 25 MB)
                  </p>
                </div>

                {/* Selected File Row */}
                {selectedFile && (
                  <div
                    className="p-3.5 rounded-xl border flex items-center justify-between gap-3"
                    style={{ backgroundColor: '#F3FAF8', borderColor: '#B8D3D1' }}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div
                        className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0"
                        style={{ backgroundColor: '#C7EAE4', color: '#1A281F' }}
                      >
                        <File className="w-5 h-5" strokeWidth={2} />
                      </div>
                      <div className="min-w-0">
                        <p className="text-xs font-semibold text-[#1A281F] truncate">
                          {selectedFile.name}
                        </p>
                        <p className="text-[11px] text-[#635255]">
                          {selectedFile.size} · {selectedFile.pages} pages detected
                        </p>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={() => setSelectedFile(null)}
                      className="p-1 rounded-md text-[#635255] hover:text-[#1A281F] cursor-pointer"
                      title="Remove file"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {/* Tab 2: Paste notes */}
        {activeTab === 'paste' && (
          <div>
            <label className="block text-xs font-semibold text-[#1A281F] mb-1.5">
              Paste your raw notes, outlines, or transcript
            </label>
            <textarea
              rows={6}
              value={pastedNotes}
              onChange={(e) => setPastedNotes(e.target.value)}
              placeholder="Paste raw text from Google Docs, Notion, or PDF slides..."
              className="w-full p-3.5 rounded-xl text-xs leading-relaxed border font-mono focus:outline-none focus:ring-1 focus:ring-[#1A281F]"
              style={{
                borderColor: '#635255',
                backgroundColor: '#FFFFFF',
                color: '#1A281F',
              }}
            />
          </div>
        )}

        {/* Configuration Fields */}
        <div className="space-y-4 pt-2 border-t border-[#B8D3D1]">
          {/* Deck Title field */}
          <div>
            <label className="block text-xs font-semibold text-[#1A281F] mb-1.5">
              Reviewer Title
            </label>
            <input
              type="text"
              value={deckTitle}
              onChange={(e) => setDeckTitle(e.target.value)}
              placeholder="e.g. Biology 101 · Cellular Respiration"
              className="w-full min-h-[44px] px-3.5 py-2 rounded-xl text-sm border focus:outline-none focus:ring-1 focus:ring-[#1A281F]"
              style={{
                borderColor: '#635255',
                backgroundColor: '#FFFFFF',
                color: '#1A281F',
              }}
            />
          </div>

          {/* "Generate" select */}
          <div>
            <label className="block text-xs font-semibold text-[#1A281F] mb-1.5">
              Generation Outputs
            </label>
            <select
              value={generationType}
              onChange={(e) =>
                setGenerationType(e.target.value as 'all' | 'flashcards-quiz' | 'flashcards-only')
              }
              className="w-full min-h-[44px] px-3.5 py-2 rounded-xl text-sm border bg-white focus:outline-none focus:ring-1 focus:ring-[#1A281F] cursor-pointer"
              style={{
                borderColor: '#635255',
                color: '#1A281F',
              }}
            >
              <option value="all">
                Flashcards, quiz and problem sets (Recommended for STEM)
              </option>
              <option value="flashcards-quiz">Flashcards and quiz</option>
              <option value="flashcards-only">Flashcards only</option>
            </select>
          </div>
        </div>

        {/* Action Button & Background Processing Note */}
        <div className="pt-4 border-t border-[#B8D3D1] space-y-3">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
            <Button
              variant="primary"
              size="lg"
              disabled={isGenerating}
              onClick={handleGenerate}
              icon={<Sparkles className="w-4 h-4" />}
            >
              {isGenerating ? 'Processing notes...' : 'Generate reviewer'}
            </Button>

            <button
              type="button"
              onClick={onCancel}
              className="text-xs font-semibold text-[#635255] hover:text-[#1A281F] cursor-pointer px-3 py-2 text-center"
            >
              Cancel
            </button>
          </div>

          {/* Background Processing Note */}
          <p className="text-[12px] text-[#635255] leading-relaxed">
            Note: Reviewers are generated in the background. You can safely study other decks while Kabisado parses your notes and extracts key concepts.
          </p>
        </div>
      </Card>
    </div>
  );
};
