import React, { useEffect, useState } from "react";

export default function App() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  return (
    <div className="min-h-screen bg-stone-950 text-stone-100 flex flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold tracking-tight">Kitchen Remix</h1>
      <p className="text-stone-400 text-lg max-w-md text-center">
        Photorealistic kitchen finish swaps and structural explorations powered
        by FLUX.1 Kontext.
      </p>

      <div className="rounded-lg bg-stone-900 border border-stone-700 px-6 py-4 text-sm font-mono">
        {health === null && <span className="text-stone-500">checking backend…</span>}
        {health?.status === "ok" && (
          <span className="text-emerald-400">
            ✓ backend ok · model loaded: {String(health.model_loaded)}
          </span>
        )}
        {health?.status === "unreachable" && (
          <span className="text-red-400">✗ backend unreachable</span>
        )}
      </div>

      <p className="text-stone-600 text-xs mt-8">Phase 0 scaffold — UI coming in Phase 3</p>
    </div>
  );
}
