import React, { useState, useEffect } from "react";

export default function FinishSelector({ onFinishChange, onSelectionChange }) {
  const [finishData, setFinishData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("cabinets");
  const [selected, setSelected] = useState([]);

  useEffect(() => {
    fetch("/api/finishes")
      .then(response => response.json())
      .then(data => {
        setFinishData(data);
        setLoading(false);
      })
      .catch(err => {
        setError("Failed to load finish presets");
        setLoading(false);
      });
  }, []);

  const handleFinishSelect = (finish) => {
    onFinishChange(finish.instruction);
    setSelected((prev) => {
      const exists = prev.some((f) => f.instruction === finish.instruction);
      const next = exists
        ? prev.filter((f) => f.instruction !== finish.instruction)
        : [...prev, { ...finish, category: selectedCategory }];
      onSelectionChange?.(next);
      return next;
    });
  };

  const isSelected = (finish) =>
    selected.some((f) => f.instruction === finish.instruction);

  if (loading) {
    return (
      <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
        <p className="text-center text-ink-500 py-4">Loading finishes...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
        <p className="flex gap-3 bg-copper-400/[0.07] border border-copper-400/25 rounded-control p-3.5 text-sm leading-relaxed text-copper-300">
          {error}
        </p>
      </div>
    );
  }

  const categories = Object.keys(finishData || {});

  return (
    <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
      <h3 className="font-display font-semibold text-xl text-ink-100 mb-4">Finish Presets</h3>

      {/* Category tabs */}
      <div className="flex flex-wrap gap-2 mb-4">
        {categories.map(category => (
          <button
            key={category}
            onClick={() => setSelectedCategory(category)}
            className={
              selectedCategory === category
                ? "bg-copper-400 text-[#1a130c] font-semibold rounded-[9px] px-4 py-2 text-sm shadow-control"
                : "bg-raised text-ink-300 hover:bg-raised-hi hover:text-ink-100 border border-hairline rounded-[9px] px-4 py-2 text-sm transition-colors"
            }
          >
            {category.charAt(0).toUpperCase() + category.slice(1)}
          </button>
        ))}
      </div>

      {/* Finish tiles */}
      {finishData && finishData[selectedCategory] && (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {finishData[selectedCategory].map((finish, index) => (
            <button
              key={index}
              onClick={() => handleFinishSelect(finish)}
              className={
                isSelected(finish)
                  ? "flex items-center justify-between w-full p-3.5 rounded-tile text-left transition-all bg-copper-400/10 border border-copper-400 text-ink-100 shadow-glow"
                  : "flex items-center justify-between w-full p-3.5 rounded-tile text-left transition-all bg-raised border border-hairline text-ink-100 shadow-control"
              }
            >
              <span className="text-sm">{finish.label}</span>
              {isSelected(finish) && (
                <span className="ml-2 flex-shrink-0 w-5 h-5 rounded-full bg-copper-400 flex items-center justify-center">
                  <svg className="w-3 h-3 text-[#1a130c]" viewBox="0 0 12 12" fill="none">
                    <path d="M2 6l3 3 5-5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </span>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
