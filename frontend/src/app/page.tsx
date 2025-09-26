"use client";

import React, { useEffect, useMemo, useRef } from "react";
import { v4 as uuidv4 } from "uuid";
import { socket } from "@/lib/socket";
import { useAppContext } from "@/contexts/AppContext";
import CanvasView from "@/components/CanvasView";
import ChatInput from "@/components/ChatInput";
import MessageList from "@/components/MessageList";
import {
  ChatMessage,
  CanvasSVGOutput,
  CanvasStaticWebsiteOutput,
} from "@/types";

export default function Page() {
  const { messages, setMessages, isChatStarted, setIsChatStarted } =
    useAppContext();
  const iframeRef = useRef<HTMLIFrameElement>(null);

  const sessionId = useMemo(() => uuidv4(), []);
  const convId = useMemo(() => uuidv4(), []);

  const render = (
    payload:
      | { type: "svg"; code: string }
      | { type: "static_website"; html: string; css: string; js: string }
  ) => {
    const buildSrcDoc = (
      payload: CanvasSVGOutput | CanvasStaticWebsiteOutput
    ) => {
      if (payload.type === "svg") {
        const safe = payload.code || "";
        return `<!DOCTYPE html><html><head><meta charset="utf-8" /></head><body style="margin:0;display:grid;place-items:center;background:#0b0b0f;color:white;">${safe}</body></html>`;
      }
      const html = payload.html || "";
      const css = payload.css || "";
      const js = payload.js || "";
      return `<!DOCTYPE html>
  <html lang="en">
  <head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>${css}</style>
  </head>
  <body>
  ${html}
  <script>(function(){${js}})();</script>
  </body>
  </html>`;
    };
    const doc = buildSrcDoc(payload);
    if (iframeRef.current) {
      iframeRef.current.srcdoc = doc;
    }
  };

  const takeScreenshot = async (id: string) => {
    const socketURL =
      process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:8000";
    if (iframeRef.current) {
      await fetch(`${socketURL}/screenshot`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          html_content: iframeRef.current.srcdoc,
          image_id: id,
        }),
      });
    }
  };

  useEffect(() => {
    socket.connect();

    function onConnect() {
      console.log("connected to socket");
    }

    function onDisconnect() {
      console.log("disconnected from socket");
    }

    const onChat = async (msg: ChatMessage | { error: string }) => {
      if ("error" in msg) {
        console.error("socket error", msg.error);
        return;
      }

      setMessages((prevMessages) => {
        const existingMsgIndex = prevMessages.findIndex(
          (m) => m.msg_id === msg.msg_id
        );
        if (existingMsgIndex !== -1) {
          const newMessages = [...prevMessages];
          newMessages[existingMsgIndex] = msg;
          return newMessages;
        } else {
          return [...prevMessages, msg];
        }
      });

      if (!isChatStarted) {
        setIsChatStarted(true);
      }

      const specials: { screenshot?: string } = {};
      for (const c of msg.content) {
        if (
          c.type === "text" &&
          typeof c.text === "string" &&
          c.text.startsWith("take_screenshot::")
        ) {
          specials.screenshot = c.text.split("take_screenshot::")[1]?.trim();
        }
        if (c.type === "canvas" && "content" in c && c.content) {
          const content = c.content as
            | CanvasSVGOutput
            | CanvasStaticWebsiteOutput;
          if (content.type === "svg") {
            render({ type: "svg", code: content.code });
          } else if (content.type === "static_website") {
            render({
              type: "static_website",
              html: content.html,
              css: content.css,
              js: content.js,
            });
          }
        }
      }

      if (specials.screenshot) {
        try {
          await takeScreenshot(specials.screenshot);
        } catch (e) {
          console.error("screenshot failed", e);
        }
      }
    };

    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("chat", onChat);

    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("chat", onChat);
      socket.disconnect();
    };
  }, [setMessages, isChatStarted, setIsChatStarted]);

  const handleSend = () => {
    if (!isChatStarted) {
      setIsChatStarted(true);
    }
  };

  if (!isChatStarted) {
    return (
      <div className="min-h-screen grid place-items-center p-6 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900 via-zinc-900 to-black">
        <div className="max-w-3xl w-full">
          <div className="text-center mb-8">
            <h1 className="text-5xl font-extrabold tracking-tight text-white">
              Build something <span className="text-pink-400">Lovable</span>
            </h1>
            <p className="text-zinc-400 mt-3">
              Create apps and websites by chatting with AI
            </p>
          </div>
          <ChatInput
            sessionId={sessionId}
            convId={convId}
            onSent={handleSend}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen grid grid-cols-12 gap-5 p-5 bg-zinc-950">
      <div className="col-span-5 flex flex-col gap-4">
        <div className="rounded-xl border border-zinc-800 p-4 bg-zinc-900/60 backdrop-blur h-[calc(100vh-10rem)] overflow-y-auto">
          <MessageList messages={messages} />
        </div>
        <ChatInput sessionId={sessionId} convId={convId} onSent={handleSend} />
      </div>
      <div className="col-span-7">
        <CanvasView ref={iframeRef} />
      </div>
    </div>
  );
}
