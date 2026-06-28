import React, { useState, useEffect } from "react";

function prettify(key) {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

export default function ReferenceTab({ imageB64 }) {
  const [presets, setPresets] = useState({});
  const [error, setError] = useState(null);

  const [finishRef, setFinishRef] = useState(null);
  const [finishTarget, setFinishTarget] = useState("");
  const [finishNote, setFinishNote] = useState("");
  const [finishResult, setFinishResult] = useState(null);
  const [finishLoading, setFinishLoading] = useState(false);

  const [objectRef, setObjectRef] = useState(null);
  const [objectTarget, setObjectTarget] = useState("");
  const [objectNote, setObjectNote] = useState("");
  const [objectResult, setObjectResult] = useState(null);
  const [objectLoading, setObjectLoading] = useState(false);

  useEffect(() => {
    fetch("/api/reference-presets")
      .then((r) => r.json())
      .then(setPresets)
      .catch(() => setPresets({}));
  }, []);

  const finishTargets = Object.keys(presets.finish_reference_templates || {});
  const objectTargets = Object.keys(presets.object_reference_templates || {});
  const caveats = presets.caveats || {};

  const readRef = (file, setter) => {
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => setter(e.target.result.split(",")[1]);
      reader.readAsDataURL(file);
    }
  };

  const run = async (endpoint, body, setResult, setLoading) => {
    setLoading(true);
    setError(null);
    setResult(null);
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

  const inputClass = `w-full bg-raised border border-hairline rounded-control px-3.5 py-2.5
    text-sm text-ink-100 placeholder-ink-500 shadow-control transition
    focus:outline-none focus:border-copper-500 focus:ring-2 focus:ring-copper-400/25`;

  const btnSecondary = `bg-raised hover:bg-raised-hi text-ink-100 font-semibold rounded-control
    px-5 py-3 border border-hairline-2 shadow-control transition-colors duration-200
    disabled:opacity-50 whitespace-nowrap`;

  return (
    <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6">
      <h3 className="font-display font-semibold text-xl text-ink-100 mb-4">Reference-based Edits</h3>

      {error && (
        <div className="flex gap-3 bg-red-950/40 border border-red-500/30 rounded-control p-3.5 text-sm leading-relaxed text-red-300 mb-4">
          {error}
        </div>
      )}

      {/* Base kitchen reminder */}
      {imageB64 ? (
        <div className="flex items-center gap-3 mb-5 text-sm text-ink-500">
          <img
            src={`data:image/png;base64,${imageB64}`}
            alt="Your kitchen"
            className="h-12 w-12 rounded-lg object-cover border border-hairline flex-shrink-0"
          />
          <span>
            Edits apply to <span className="text-ink-100">your kitchen photo</span> (uploaded
            at the top). Attach an <em>example</em> below to copy a look onto it.
          </span>
        </div>
      ) : (
        <p className="text-sm text-ink-500 mb-5">
          Upload your kitchen photo at the top first — then attach examples here.
        </p>
      )}

      {/* Tier A — finish from a photo */}
      <div className="mb-6">
        <h4 className="block text-sm font-semibold text-ink-300 mb-1">Finish from a photo</h4>
        <p className="text-sm text-ink-500 mb-3">
          Attach an example (a cabinet style, a countertop look) and apply it to that surface.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-2">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => readRef(e.target.files[0], setFinishRef)}
            className={inputClass}
          />
          <div className="relative">
            <select
              value={finishTarget}
              onChange={(e) => setFinishTarget(e.target.value)}
              className={inputClass + " appearance-none pr-9 cursor-pointer"}
            >
              <option value="">Surface…</option>
              {finishTargets.map((t) => (
                <option key={t} value={t}>{prettify(t)}</option>
              ))}
            </select>
            <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-ink-500 text-xs">▼</span>
          </div>
          <button
            onClick={() =>
              run(
                "reference_finish",
                { reference_b64: finishRef, target: finishTarget, note: finishNote },
                setFinishResult,
                setFinishLoading
              )
            }
            disabled={!imageB64 || !finishRef || !finishTarget || finishLoading}
            className={btnSecondary}
          >
            {finishLoading ? "Generating…" : "Apply"}
          </button>
        </div>
        <input
          type="text"
          value={finishNote}
          onChange={(e) => setFinishNote(e.target.value)}
          placeholder="Optional — what exactly? e.g. just the countertop color, a flat matte black"
          className={inputClass + " mb-2"}
        />
        {finishResult && (
          <div className="mt-2">
            <div className="bg-raised border border-hairline rounded-tile p-2.5 shadow-control mb-2">
              <img
                src={`data:image/png;base64,${finishResult}`}
                alt="Finish reference result"
                className="w-full rounded-lg"
              />
            </div>
            <div className="flex gap-3 bg-copper-400/[0.07] border border-copper-400/25 rounded-control p-3.5 text-sm leading-relaxed text-copper-300">
              {caveats.finish_reference ||
                "Color and material are guided by your photo; exact pattern may differ."}
            </div>
          </div>
        )}
      </div>

      {/* Tier B — replace an appliance */}
      <div>
        <h4 className="block text-sm font-semibold text-ink-300 mb-1">Replace an appliance</h4>
        <p className="text-sm text-ink-500 mb-3">
          Attach a specific appliance (e.g. a fridge) and swap yours for one matching it.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2 mb-2">
          <input
            type="file"
            accept="image/*"
            onChange={(e) => readRef(e.target.files[0], setObjectRef)}
            className={inputClass}
          />
          <div className="relative">
            <select
              value={objectTarget}
              onChange={(e) => setObjectTarget(e.target.value)}
              className={inputClass + " appearance-none pr-9 cursor-pointer"}
            >
              <option value="">Appliance…</option>
              {objectTargets.map((t) => (
                <option key={t} value={t}>{prettify(t)}</option>
              ))}
            </select>
            <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-ink-500 text-xs">▼</span>
          </div>
          <button
            onClick={() =>
              run(
                "reference_object",
                { reference_b64: objectRef, target: objectTarget, note: objectNote },
                setObjectResult,
                setObjectLoading
              )
            }
            disabled={!imageB64 || !objectRef || !objectTarget || objectLoading}
            className={btnSecondary}
          >
            {objectLoading ? "Generating…" : "Replace"}
          </button>
        </div>
        <input
          type="text"
          value={objectNote}
          onChange={(e) => setObjectNote(e.target.value)}
          placeholder="Optional — what exactly? e.g. match only the handle style, keep stainless"
          className={inputClass + " mb-2"}
        />
        {objectResult && (
          <div className="mt-2">
            <div className="bg-raised border border-hairline rounded-tile p-2.5 shadow-control mb-2">
              <img
                src={`data:image/png;base64,${objectResult}`}
                alt="Object reference result"
                className="w-full rounded-lg"
              />
            </div>
            <div className="flex gap-3 bg-copper-400/[0.07] border border-copper-400/25 rounded-control p-3.5 text-sm leading-relaxed text-copper-300">
              ⚠️ {caveats.object_reference ||
                "Shows an appliance in this style — not a guarantee of the exact model or fit. Confirm measurements before buying."}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
