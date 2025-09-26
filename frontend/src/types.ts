export type RoleTypes = "system" | "user" | "assistant" | "tool";
export type MsgStatus = "progress" | "success" | "error";
export type MsgType = "input" | "output";

export type ToolStatus = "success" | "error" | "progress";

export type TextContent = { type: "text"; text: string };
export type ImageContent = { type: "image_url"; image_url: string };

export type TaskStatus = "pending" | "in_progress" | "completed" | "failed";
export type TaskContent = { type: "task"; task: string; status: TaskStatus };
export type TaskListContent = {
  type: "task_list";
  title: string;
  task_list: TaskContent[];
};

export type ToolContent = {
  type: "tool";
  tool_name: string;
  tool_args: Record<string, unknown>;
  tool_response: unknown;
  tool_status: ToolStatus;
};

export type CanvasSVGOutput = { type: "svg"; code: string };
export type CanvasStaticWebsiteOutput = {
  type: "static_website";
  html: string;
  css: string;
  js: string;
};
export interface CanvasContent {
  type: "canvas";
  content: CanvasSVGOutput | CanvasStaticWebsiteOutput;
}

export type AnyContent =
  | TextContent
  | ImageContent
  | TaskListContent
  | ToolContent
  | CanvasContent
  | Record<string, unknown>;

export type ChatMessage = {
  session_id: string;
  conv_id: string;
  msg_type: MsgType;
  content: AnyContent[];
  status: MsgStatus;
  msg_id: string;
  actions?: string[];
  tools?: string[];
};

export type OutgoingMessage = {
  session_id: string;
  conv_id: string;
  msg_type: "input";
  content: Array<TextContent | ImageContent>;
};

export type SocketServerEvent = "chat";
