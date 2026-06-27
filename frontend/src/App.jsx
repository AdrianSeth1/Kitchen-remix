import React, { useState, useEffect } from "react";
import Upload from "./components/Upload";
import FinishSelector from "./components/FinishSelector";
import AblGrid from "./components/AblGrid";
import LayerEditor from "./components/LayerEditor";
import BeforeAfterSlider from "./components/BeforeAfterSlider";
import StructuralTab from "./components/StructuralTab";
import ReferenceTab from "./components/ReferenceTab";
import ExportSpecSheet from "./components/ExportSpecSheet";

export default function App() {
  const [health, setHealth] = useState(null);
  const [uploadedImageB64, setUploadedImageB64] = useState(null);
  const [baseInstruction, setBaseInstruction] = useState("keep everything else unchanged");
  const [selectedFinish, setSelectedFinish] = useState("");
  const [abResults, setAbResults] = useState([]);
  const [layerResult, setLayerResult] = useState(null);
  const [beforeAfterImageB64, setBeforeAfterImageB64] = useState(null);
  const [selectedFinishes, setSelectedFinishes] = useState([]);

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth({ status: "unreachable" }));
  }, []);

  const handleImageUpload = (base64) => {
    setUploadedImageB64(base64);
    setBeforeAfterImageB64(null);
  };

  const handleFinishSelect = (finishInstruction) => {
    setSelectedFinish(finishInstruction);
  };

  const handleGenerateAB = async (results) => {
    setAbResults(results);
  };

  const handleGenerateLayer = (result) => {
    setLayerResult(result);
  };

  const handleEditWithFinish = async () => {
    if (!uploadedImageB64 || !selectedFinish) return;

    try {
      const response = await fetch("/api/edit", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          image_b64: uploadedImageB64,
          instruction: selectedFinish,
          seed: 42
        })
      });

      const data = await response.json();

      if (response.ok) {
        setBeforeAfterImageB64(data.image_b64);
      } else {
        console.error("Failed to edit image:", data.detail);
      }
    } catch (err) {
      console.error("Error editing image:", err);
    }
  };

  const handleSelectedFinishesChange = (newSelections) => {
    setSelectedFinishes(newSelections);
  };

  const exportSelections = abResults.map((r) => ({
    label: r.label,
    image_b64: r.image_b64,
    category: selectedFinishes.find((f) => f.label === r.label)?.category,
  }));

  return (
    <div className="min-h-screen bg-canvas text-ink-100 font-sans antialiased">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <header className="mb-8 text-center">
          <h1 className="font-display font-semibold text-4xl text-ink-100 tracking-tight">
            Kitchen Remix
          </h1>
          <p className="text-ink-500 mt-2">
            Photorealistic kitchen finish swaps and structural explorations powered by FLUX.1 Kontext
          </p>

          <div className="mt-4 inline-block">
            {health === null && (
              <span className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full font-mono text-sm bg-raised border border-hairline text-ink-500">
                checking backend...
              </span>
            )}
            {health?.status === "ok" && (
              <span className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full font-mono text-sm bg-sage-950/60 border border-sage-400/30 text-sage-300">
                <span className="w-2 h-2 rounded-full bg-sage-400 ring-4 ring-sage-400/20 inline-block" />
                backend ok · model loaded: {String(health.model_loaded)}
              </span>
            )}
            {health?.status === "unreachable" && (
              <span className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full font-mono text-sm bg-red-950/40 border border-red-500/30 text-red-300">
                <span className="w-2 h-2 rounded-full bg-red-400 inline-block" />
                backend unreachable
              </span>
            )}
          </div>
        </header>

        {/* Main Content */}
        <main>
          <Upload onImageUpload={handleImageUpload} />

          {uploadedImageB64 && (
            <>
              <FinishSelector
                onFinishChange={handleFinishSelect}
                onSelectionChange={handleSelectedFinishesChange}
              />

              <ExportSpecSheet
                originalImageB64={uploadedImageB64}
                selections={exportSelections}
              />

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Left Column */}
                <div>
                  <AblGrid
                    imageB64={uploadedImageB64}
                    baseInstruction={baseInstruction}
                    finishes={selectedFinishes.map((f) => f.instruction)}
                    labels={selectedFinishes.map((f) => f.label)}
                    onSelectFinish={handleFinishSelect}
                    onBaseInstructionChange={setBaseInstruction}
                    onGenerateAB={handleGenerateAB}
                  />

                  <LayerEditor
                    imageB64={uploadedImageB64}
                    onGenerateLayer={handleGenerateLayer}
                  />
                </div>

                {/* Right Column */}
                <div>
                  {beforeAfterImageB64 && (
                    <BeforeAfterSlider
                      originalImageB64={uploadedImageB64}
                      editedImageB64={beforeAfterImageB64}
                    />
                  )}

                  <StructuralTab imageB64={uploadedImageB64} />
                  <ReferenceTab imageB64={uploadedImageB64} />
                </div>
              </div>

              {uploadedImageB64 && selectedFinish && (
                <div className="mt-6 text-center">
                  <button
                    onClick={handleEditWithFinish}
                    className="bg-raised hover:bg-raised-hi text-ink-100 font-semibold rounded-control
                      px-5 py-3 border border-hairline-2 shadow-control transition-colors duration-200"
                  >
                    Apply Selected Finish
                  </button>
                </div>
              )}
            </>
          )}
        </main>

        {/* Footer */}
        <footer className="mt-12 pt-8 border-t border-hairline text-center text-sm text-ink-500">
          <p>Phase 3 - Core frontend complete | UI for Kitchen Remix</p>
        </footer>
      </div>
    </div>
  );
}
