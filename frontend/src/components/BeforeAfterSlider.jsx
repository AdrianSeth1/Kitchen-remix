import React, { useState } from "react";

export default function BeforeAfterSlider({ originalImageB64, editedImageB64 }) {
  const [sliderPosition, setSliderPosition] = useState(50);

  if (!originalImageB64 || !editedImageB64) {
    return (
      <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
        <h3 className="font-display font-semibold text-xl text-ink-100 mb-4">Before/After</h3>
        <p className="text-ink-500 text-center py-8">Upload an image to compare before/after</p>
      </div>
    );
  }

  return (
    <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
      <h3 className="font-display font-semibold text-xl text-ink-100 mb-4">Before/After Comparison</h3>

      <div className="relative">
        <div
          className="relative overflow-hidden rounded-lg"
          style={{ height: '512px' }}
        >
          <img
            src={`data:image/png;base64,${originalImageB64}`}
            alt="Original"
            className="absolute top-0 left-0 w-full h-full object-contain"
          />
          <img
            src={`data:image/png;base64,${editedImageB64}`}
            alt="Edited"
            className="absolute top-0 left-0 w-full h-full object-contain"
            style={{ clipPath: `inset(0 ${100 - sliderPosition}% 0 0)` }}
          />
        </div>

        <div className="relative mt-4">
          <input
            type="range"
            min="0"
            max="100"
            value={sliderPosition}
            onChange={(e) => setSliderPosition(Number(e.target.value))}
            className="ba"
          />
        </div>

        <div className="flex justify-between text-xs text-ink-500 mt-2">
          <span>Original</span>
          <span>Edited</span>
        </div>
      </div>
    </div>
  );
}
