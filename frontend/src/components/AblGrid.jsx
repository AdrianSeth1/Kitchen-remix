import React, { useState } from "react";

export default function AblGrid({
  imageB64,
  baseInstruction,
  finishes,
  labels = [],
  onSelectFinish,
  onBaseInstructionChange,
  onGenerateAB
}) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState([]);
  const [selectedFinishIndex, setSelectedFinishIndex] = useState(null);

  const handleGenerateAB = async () => {
    if (!imageB64 || finishes.length === 0) return;

    setIsGenerating(true);

    try {
      const payload = {
        image_b64: imageB64,
        base_instruction: baseInstruction,
        finishes: finishes,
        seed: 42
      };
      if (labels.length === finishes.length) {
        payload.labels = labels;
      }

      const response = await fetch("/api/ab", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (response.ok) {
        setResults(data.results);
        onGenerateAB?.(data.results);
      } else {
        console.error("Failed to generate A/B results:", data.detail);
      }
    } catch (err) {
      console.error("Error generating A/B results:", err);
    }

    setIsGenerating(false);
  };

  const handleSelectFinish = (finish, index) => {
    setSelectedFinishIndex(index);
    onSelectFinish(finish);
  };

  return (
    <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
      <h3 className="font-display font-semibold text-xl text-ink-100 mb-4">A/B Comparison</h3>

      <div className="mb-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-semibold text-ink-300 mb-2">Base Instruction</label>
            <input
              type="text"
              value={baseInstruction}
              onChange={(e) => onBaseInstructionChange?.(e.target.value)}
              className="w-full bg-raised border border-hairline rounded-control px-3.5 py-2.5
                text-sm text-ink-100 placeholder-ink-500 shadow-control transition
                focus:outline-none focus:border-copper-500 focus:ring-2 focus:ring-copper-400/25"
              placeholder="e.g. keep everything else unchanged"
            />
          </div>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-semibold text-ink-300 mb-2">Selected finishes</label>
          {finishes.length === 0 ? (
            <p className="text-sm text-ink-500">
              Pick finishes above to compare them side by side.
            </p>
          ) : (
            <div className="flex flex-wrap gap-2">
              {finishes.map((finish, index) => (
                <button
                  key={index}
                  onClick={() => handleSelectFinish(finish, index)}
                  className={
                    selectedFinishIndex === index
                      ? "bg-copper-400/10 border border-copper-400 text-ink-100 font-semibold rounded-control px-4 py-2 text-sm shadow-glow transition-colors"
                      : "bg-raised hover:bg-raised-hi text-ink-300 border border-hairline rounded-control px-4 py-2 text-sm transition-colors"
                  }
                >
                  {labels[index] || finish}
                </button>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={handleGenerateAB}
          disabled={isGenerating || !imageB64 || finishes.length === 0}
          className="w-full bg-copper-400 hover:bg-copper-300 text-[#1a130c] font-semibold rounded-control
            px-5 py-3 shadow-cta transition-colors duration-200
            focus:outline-none focus:ring-2 focus:ring-copper-400/40
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isGenerating ? "Generating..." : "Generate A/B Comparison"}
        </button>
      </div>

      {results.length > 0 && (
        <div className="mt-6">
          <h4 className="text-sm font-semibold text-ink-300 mb-3">Results</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {results.map((result, index) => (
              <div key={index} className="bg-raised border border-hairline rounded-tile p-2.5 shadow-control">
                <p className="text-sm font-semibold text-ink-100 mb-2 px-1">{result.label}</p>
                <img
                  src={`data:image/png;base64,${result.image_b64}`}
                  alt={`Result ${index + 1}`}
                  className="w-full rounded-lg"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
