import React, { useState } from "react";

export default function Upload({ onImageUpload }) {
  const [isDragging, setIsDragging] = useState(false);
  const [previewUrl, setPreviewUrl] = useState(null);

  const handleFileUpload = (file) => {
    if (file && file.type.startsWith("image/")) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setPreviewUrl(e.target.result);
        const base64 = e.target.result.split(',')[1];
        onImageUpload(base64);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files && files[0]) {
      handleFileUpload(files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
  };

  return (
    <div className="bg-panel border border-hairline rounded-panel shadow-panel p-7 mb-6 text-center">
      <h3 className="font-display font-semibold text-xl text-ink-100 mb-2">Upload Kitchen Photo</h3>
      <p className="text-sm text-ink-500 mb-4">Drag & drop or click to select an image</p>

      {previewUrl ? (
        <div className="mb-4">
          <img
            src={previewUrl}
            alt="Preview"
            className="mx-auto max-h-64 rounded-lg object-contain"
          />
        </div>
      ) : (
        <div
          className={`border-2 border-dashed rounded-tile p-8 mb-4 transition-colors duration-200 ${
            isDragging
              ? 'border-copper-400 bg-copper-400/[0.05]'
              : 'border-hairline-2'
          }`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <div className="text-ink-500 mb-2">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828-0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
          <p className="text-sm text-ink-500">Click or drag to upload</p>
        </div>
      )}

      <input
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        className="hidden"
        id="file-upload"
      />
      <label
        htmlFor="file-upload"
        className="inline-block bg-raised hover:bg-raised-hi text-ink-100 font-semibold rounded-control
          px-5 py-3 border border-hairline-2 shadow-control transition-colors duration-200 cursor-pointer"
      >
        Choose File
      </label>
    </div>
  );
}
