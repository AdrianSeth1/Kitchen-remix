import React, { useState, useEffect } from "react";

export default function StructuralTab({ imageB64 }) {
  const [removeTarget, setRemoveTarget] = useState("");
  const [moveTarget, setMoveTarget] = useState("");
  const [moveDestination, setMoveDestination] = useState("");
  const [openWallDescription, setOpenWallDescription] = useState("");

  const [loading, setLoading] = useState(false);
  const [removeResult, setRemoveResult] = useState(null);
  const [moveResult, setMoveResult] = useState(null);
  const [openWallResult, setOpenWallResult] = useState(null);
  const [error, setError] = useState(null);
  const [caveats, setCaveats] = useState({});

  useEffect(() => {
    fetch("/api/structural-presets")
      .then((r) => r.json())
      .then((data) => setCaveats(data.caveats || {}))
      .catch(() => setCaveats({}));
  }, []);

  const resetResults = () => {
    setRemoveResult(null);
    setMoveResult(null);
    setOpenWallResult(null);
    setError(null);
  };

  const runStructural = async (endpoint, body, setResult) => {
    if (!imageB64) return;
    resetResults();
    setLoading(true);
    try {
      const response = await fetch(`/api/${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_b64: imageB64, seed: 42, ...body }),
      });
      const data = await response.json();
      if (response.ok) {
        setResult(data.image_b64);
      } else {
        setError(data.detail || "Request failed");
      }
    } catch (err) {
      setError("Network error occurred");
    } finally {
      setLoading(false);
    }
  };

  const handleRemove = () =>
    runStructural("remove", { target: removeTarget }, setRemoveResult);
  const handleMove = () =>
    runStructural(
      "move",
      { target: moveTarget, destination: moveDestination },
      setMoveResult
    );
  const handleOpenWall = () =>
    runStructural(
      "open_wall",
      { wall_description: openWallDescription },
      setOpenWallResult
    );

  const inputClass = `w-full bg-raised border border-hairline rounded-control px-3.5 py-2.5
    text-sm text-ink-100 placeholder-ink-500 shadow-control transition
    focus:outline-none focus:border-copper-500 focus:ring-2 focus:ring-copper-400/25`;

  const btnSecondary = `bg-raised hover:bg-raised-hi text-ink-100 font-semibold rounded-control
    px-5 py-3 border border-hairline-2 shadow-control transition-colors duration-200
    disabled:opacity-50`;

  return (
    <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
      <h3 className="font-display font-semibold text-xl text-ink-100 mb-4">Structural Experiments</h3>

      {/* Remove Object */}
      <div className="mb-5">
        <label className="block text-sm font-semibold text-ink-300 mb-2">Remove Object</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={removeTarget}
            onChange={(e) => setRemoveTarget(e.target.value)}
            placeholder="Object to remove (e.g. 'cabinet', 'wall', 'sink')"
            className={inputClass}
          />
          <button
            onClick={handleRemove}
            disabled={!imageB64 || !removeTarget || loading}
            className={btnSecondary + " flex-shrink-0"}
          >
            Remove
          </button>
        </div>
      </div>

      {/* Move Object */}
      <div className="mb-5">
        <label className="block text-sm font-semibold text-ink-300 mb-2">Move Object</label>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <input
            type="text"
            value={moveTarget}
            onChange={(e) => setMoveTarget(e.target.value)}
            placeholder="Object to move"
            className={inputClass}
          />
          <input
            type="text"
            value={moveDestination}
            onChange={(e) => setMoveDestination(e.target.value)}
            placeholder="New location (e.g. 'next to stove', 'in corner')"
            className={inputClass}
          />
          <button
            onClick={handleMove}
            disabled={!imageB64 || !moveTarget || !moveDestination || loading}
            className={btnSecondary}
          >
            Move
          </button>
        </div>
      </div>

      {/* Open Wall */}
      <div className="mb-5">
        <label className="block text-sm font-semibold text-ink-300 mb-2">Open Wall</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={openWallDescription}
            onChange={(e) => setOpenWallDescription(e.target.value)}
            placeholder="Wall to open (e.g. 'left wall', 'between island and stove')"
            className={inputClass}
          />
          <button
            onClick={handleOpenWall}
            disabled={!imageB64 || !openWallDescription || loading}
            className={btnSecondary + " flex-shrink-0"}
          >
            Open Wall
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="mt-6 space-y-4">
        {error && (
          <div className="flex gap-3 bg-red-950/40 border border-red-500/30 rounded-control p-3.5 text-sm leading-relaxed text-red-300">
            {error}
          </div>
        )}

        {removeResult && (
          <div>
            <p className="text-sm font-semibold text-ink-100 mb-2">Remove Result</p>
            <div className="bg-raised border border-hairline rounded-tile p-2.5 shadow-control">
              <img
                src={`data:image/png;base64,${removeResult}`}
                alt="Remove result"
                className="w-full rounded-lg"
              />
            </div>
          </div>
        )}

        {moveResult && (
          <div>
            <p className="text-sm font-semibold text-ink-100 mb-2">Move Result</p>
            <div className="bg-raised border border-hairline rounded-tile p-2.5 shadow-control mb-2">
              <img
                src={`data:image/png;base64,${moveResult}`}
                alt="Move result"
                className="w-full rounded-lg"
              />
            </div>
            <div className="flex gap-3 bg-copper-400/[0.07] border border-copper-400/25 rounded-control p-3.5 text-sm leading-relaxed text-copper-300">
              ⚠️ {caveats.move || "Placement and scale are approximate. Use for visual feel, not accurate measurements."}
            </div>
          </div>
        )}

        {openWallResult && (
          <div>
            <p className="text-sm font-semibold text-ink-100 mb-2">Open Wall Result</p>
            <div className="bg-raised border border-hairline rounded-tile p-2.5 shadow-control mb-2">
              <img
                src={`data:image/png;base64,${openWallResult}`}
                alt="Open wall result"
                className="w-full rounded-lg"
              />
            </div>
            <div className="flex gap-3 bg-copper-400/[0.07] border border-copper-400/25 rounded-control p-3.5 text-sm leading-relaxed text-copper-300">
              ⚠️ {caveats.open_wall || "The space beyond the wall is invented — not the real adjacent room. Use for visual inspiration only."}
            </div>
          </div>
        )}
      </div>

      <div className="flex gap-3 bg-copper-400/[0.07] border border-copper-400/25 rounded-control p-3.5 text-sm leading-relaxed text-copper-300 mt-6">
        ℹ️ Structural edits are experimental and may produce approximate results. The UI will show appropriate caveats when applicable.
      </div>
    </div>
  );
}
