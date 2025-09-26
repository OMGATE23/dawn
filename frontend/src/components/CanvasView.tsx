"use client";

import React, { useState, forwardRef } from "react";
import { RefreshCw, Code } from "lucide-react";

const CanvasView = forwardRef<HTMLIFrameElement>((props, ref) => {
  const [key, setKey] = useState(0);

  const refreshIframe = () => {
    setKey((prevKey) => prevKey + 1);
  };

  return (
    <div className="w-full h-full bg-zinc-900 rounded-xl overflow-hidden border border-zinc-800 flex flex-col">
      <div className="flex items-center justify-between p-2 bg-zinc-800 border-b border-zinc-700">
        <div className="flex items-center gap-2">
          <Code className="w-4 h-4 text-zinc-400" />
          <span className="text-sm text-zinc-400">Canvas</span>
        </div>
        <button
          onClick={refreshIframe}
          className="p-1 rounded-md hover:bg-zinc-700"
        >
          <RefreshCw className="w-4 h-4 text-zinc-400" />
        </button>
      </div>
      <iframe
        key={key}
        ref={ref}
        className="w-full h-full"
        sandbox="allow-scripts allow-forms allow-pointer-lock allow-downloads allow-modals"
      />
    </div>
  );
});

CanvasView.displayName = "CanvasView";

export default CanvasView;
