import React, { useState } from "react";

export default function LayerEditor({ imageB64, onGenerateLayer }) {
  const [steps, setSteps] = useState([""]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState(null);

  const addStep = () => {
    setSteps([...steps, ""]);
  };

  const removeStep = (index) => {
    if (steps.length > 1) {
      const newSteps = steps.filter((_, i) => i !== index);
      setSteps(newSteps);
    }
  };

  const updateStep = (index, value) => {
    const newSteps = [...steps];
    newSteps[index] = value;
    setSteps(newSteps);
  };

  const handleGenerateLayer = async () => {
    if (!imageB64 || steps.some(step => !step.trim())) return;

    setIsGenerating(true);

    try {
      const response = await fetch("/api/layer", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          image_b64: imageB64,
          steps: steps.filter(step => step.trim()),
          seed: 42
        })
      });

      const data = await response.json();

      if (response.ok) {
        setResult(data);
        onGenerateLayer?.(data);
      } else {
        console.error("Failed to generate layered edit:", data.detail);
      }
    } catch (err) {
      console.error("Error generating layered edit:", err);
    }

    setIsGenerating(false);
  };

  return (
    <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
      <h3 className="font-display font-semibold text-xl text-ink-100 mb-4">Layered Editing</h3>

      <div className="mb-4">
        <label className="block text-sm font-semibold text-ink-300 mb-2">Editing Steps</label>
        {steps.map((step, index) => (
          <div key={index} className="flex gap-2 mb-2">
            <input
              type="text"
              value={step}
              onChange={(e) => updateStep(index, e.target.value)}
              placeholder={`Step ${index + 1} instruction...`}
              className="flex-1 bg-raised border border-hairline rounded-control px-3.5 py-2.5
                text-sm text-ink-100 placeholder-ink-500 shadow-control transition
                focus:outline-none focus:border-copper-500 focus:ring-2 focus:ring-copper-400/25"
            />
            <button
              onClick={() => removeStep(index)}
              className="bg-raised hover:bg-raised-hi text-ink-300 hover:text-ink-100 p-2.5 rounded-control
                border border-hairline-2 shadow-control transition-colors duration-200"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        ))}

        <button
          onClick={addStep}
          className="text-ink-500 hover:text-ink-300 text-sm flex items-center gap-1 mb-4 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          Add Step
        </button>
      </div>

      <button
        onClick={handleGenerateLayer}
        disabled={isGenerating || !imageB64 || steps.some(step => !step.trim())}
        className="w-full bg-copper-400 hover:bg-copper-300 text-[#1a130c] font-semibold rounded-control
          px-5 py-3 shadow-cta transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-copper-400/40
          disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {isGenerating ? "Processing..." : "Generate Layered Edit"}
      </button>

      {result && (
        <div className="mt-6">
          <p className="text-sm font-semibold text-ink-300 mb-2">Result</p>
          <img
            src={`data:image/png;base64,${result.final_b64}`}
            alt="Layered edit result"
            className="w-full rounded-control border border-hairline shadow-control"
          />
          {Array.isArray(result.steps) && result.steps.length > 1 && (
            <div className="mt-3 grid grid-cols-3 gap-2">
              {result.steps.map((s, i) => (
                <div key={i}>
                  <img
                    src={`data:image/png;base64,${s.image_b64}`}
                    alt={`Step ${i + 1}`}
                    className="w-full rounded-control border border-hairline"
                  />
                  <p className="mt-1 text-[11px] text-ink-500 truncate" title={s.instruction}>
                    {i + 1}. {s.instruction}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
