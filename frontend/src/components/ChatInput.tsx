"use client";

import React, { useRef, useState } from "react";
import { socket } from "@/lib/socket";
import { ImagePlus, Send } from "lucide-react";
import { TextContent, ImageContent, OutgoingMessage } from "@/types";
import Image from "next/image";

export default function ChatInput({
  sessionId,
  convId,
  onSent,
}: {
  sessionId: string;
  convId: string;
  onSent?: () => void;
}) {
  const [text, setText] = useState("");
  const [images, setImages] = useState<string[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);

  function addImageFromFile(file: File) {
    const reader = new FileReader();
    reader.onload = () => setImages((arr) => [...arr, String(reader.result)]);
    reader.readAsDataURL(file);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const content: (TextContent | ImageContent)[] = [];

    if (text.trim()) content.push({ type: "text", text: text.trim() });
    images.forEach((url) =>
      content.push({ type: "image_url", image_url: url })
    );

    const payload: OutgoingMessage = {
      session_id: sessionId,
      conv_id: convId,
      msg_type: "input",
      content,
    };

    socket.emit("chat", payload);
    setText("");
    setImages([]);
    onSent?.();
  }

  return (
    <form
      onSubmit={onSubmit}
      className="w-full rounded-2xl bg-zinc-900 border border-zinc-800 p-4 space-y-3"
    >
      <textarea
        placeholder="Ask to create a web app that..."
        className="w-full bg-transparent outline-none text-zinc-100 resize-none min-h-24"
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      {images.length > 0 && (
        <div className="flex gap-2 flex-wrap">
          {images.map((src, i) => (
            <Image
              key={i}
              src={src}
              alt="preview"
              className="h-16 w-16 object-cover rounded border border-zinc-800"
            />
          ))}
        </div>
      )}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => fileRef.current?.click()}
            className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg bg-zinc-800 text-zinc-100 hover:bg-zinc-700"
          >
            <ImagePlus className="w-4 h-4" /> Attach
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => {
              const f = e.target.files?.[0];
              if (f) addImageFromFile(f);
              e.currentTarget.value = "";
            }}
          />
        </div>
        <button
          type="submit"
          className="inline-flex items-center gap-2 px-4 py-1.5 rounded-lg bg-white text-black hover:bg-zinc-200"
        >
          <Send className="w-4 h-4" /> Send
        </button>
      </div>
    </form>
  );
}
