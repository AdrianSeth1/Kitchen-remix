import React, { useState } from "react";

export default function ExportSpecSheet({ originalImageB64, selections, finalImageB64 }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleExport = async () => {
    if (!originalImageB64 || selections.length === 0) return;

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/export", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          original_b64: originalImageB64,
          selections: selections,
          final_b64: finalImageB64 || null
        })
      });

      const data = await response.json();

      if (response.ok) {
        const blob = new Blob([data.html], { type: 'text/html' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'kitchen-spec-sheet.html';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } else {
        setError(data.detail || "Failed to generate spec sheet");
      }
    } catch (err) {
      setError("Network error occurred");
      console.error("Error generating spec sheet:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
      <h3 className="font-display font-semibold text-xl text-ink-100 mb-4">Export Spec Sheet</h3>

      <p className="text-sm text-ink-500 mb-4">
        Generate a printable spec sheet from your A/B previews. Run an A/B comparison first,
        then download the result to hand to a contractor.
      </p>

      {selections.length > 0 ? (
        <div className="mb-4">
          <label className="block text-sm font-semibold text-ink-300 mb-2">Previews to export</label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
            {selections.map((selection, index) => (
              <div key={index} className="bg-raised border border-hairline rounded-tile p-2.5 shadow-control">
                <img
                  src={`data:image/png;base64,${selection.image_b64}`}
                  alt={selection.label}
                  className="w-full rounded-lg mb-1.5"
                />
                <p className="text-xs font-semibold text-ink-300 px-0.5">{selection.label}</p>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <p className="text-sm text-ink-500 mb-4">
          No previews yet — generate an A/B comparison to populate the spec sheet.
        </p>
      )}

      <button
        onClick={handleExport}
        disabled={!originalImageB64 || selections.length === 0 || loading}
        className="bg-copper-400 hover:bg-copper-300 text-[#1a130c] font-semibold rounded-control
          px-5 py-3 shadow-cta transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-copper-400/40
          disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Generating..." : "Download Spec Sheet"}
      </button>

      {error && (
        <div className="mt-3 flex gap-3 bg-red-950/40 border border-red-500/30 rounded-control p-3.5 text-sm leading-relaxed text-red-300">
          {error}
        </div>
      )}
    </div>
  );
}
