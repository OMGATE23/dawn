"use client";

import React from "react";
import classNames from "classnames";
import { ChatMessage, TaskListContent, ToolContent } from "@/types";
import Image from "next/image";

function TextBlock({ text }: { text: string }) {
  return (
    <p className="whitespace-pre-wrap text-sm leading-6 text-zinc-200">
      {text}
    </p>
  );
}

function TaskList({ taskList }: { taskList: TaskListContent }) {
  return (
    <div className="rounded-lg border border-zinc-800 p-3 bg-zinc-900">
      <div className="font-semibold text-zinc-100 mb-2">{taskList.title}</div>
      <ul className="space-y-1">
        {taskList.task_list.map((t, i) => (
          <li key={i} className="text-sm flex items-center gap-2">
            <span
              className="inline-block w-2 h-2 rounded-full"
              style={{
                background:
                  t.status === "completed"
                    ? "#22c55e"
                    : t.status === "in_progress"
                    ? "#eab308"
                    : "#71717a",
              }}
            />
            <span className="text-zinc-300">{t.task}</span>
            <span className="ml-auto text-xs text-zinc-500">{t.status}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ToolBlock({ tool }: { tool: ToolContent }) {
  return (
    <div className="rounded-lg border border-zinc-800 p-3 bg-zinc-900">
      <div className="text-xs uppercase tracking-wide text-zinc-400 mb-1">
        Tool
      </div>
      <div className="font-medium text-zinc-100">{tool.tool_name}</div>
      <pre className="text-xs mt-2 p-2 rounded bg-zinc-950/60 overflow-auto">
        {JSON.stringify(tool.tool_args, null, 2)}
      </pre>
      {tool.tool_response ? (
        <pre className="text-xs mt-2 p-2 rounded bg-zinc-950/60 overflow-auto">
          {JSON.stringify(tool.tool_response, null, 2)}
        </pre>
      ) : null}
      <div className="text-xs mt-2 text-zinc-400">
        status: {tool.tool_status}
      </div>
    </div>
  );
}

export default function MessageList({ messages }: { messages: ChatMessage[] }) {
  return (
    <div className="space-y-3">
      {messages.map((message) => (
        <div
          key={message.msg_id}
          className={classNames("flex", {
            "justify-end": message.msg_type === "input",
            "justify-start": message.msg_type === "output",
          })}
        >
          <div
            className={classNames("p-4 rounded-lg max-w-lg space-y-3", {
              "bg-blue-600 text-white": message.msg_type === "input",
              "bg-zinc-800 text-zinc-200": message.msg_type === "output",
            })}
          >
            {message.content.map((c, idx) => {
              if (c.type === "text")
                return <TextBlock key={idx} text={c.text as string} />;
              if (c.type === "task_list")
                return <TaskList key={idx} taskList={c as TaskListContent} />;
              if (c.type === "tool")
                return <ToolBlock key={idx} tool={c as ToolContent} />;
              if (c.type === "image_url") {
                return (
                  <div
                    key={idx}
                    className="rounded-lg overflow-hidden border border-zinc-800"
                  >
                    <Image
                      src={c.image_url as string}
                      alt="attachment"
                      className="max-h-48 w-full object-contain bg-zinc-950"
                    />
                  </div>
                );
              }
              if (c.type === "canvas") {
                // We don’t render the code here (that shows in CanvasView). Provide a breadcrumb instead.
                const kind =
                  "content" in c &&
                  c.content &&
                  typeof c.content === "object" &&
                  "type" in c.content
                    ? c.content.type
                    : "unknown";
                return (
                  <div key={idx} className="text-xs text-zinc-400">
                    Canvas updated: {kind as string}
                  </div>
                );
              }
              return (
                <pre
                  key={idx}
                  className="text-xs p-2 rounded bg-zinc-950/60 overflow-auto border border-zinc-800"
                >
                  {JSON.stringify(c, null, 2)}
                </pre>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
