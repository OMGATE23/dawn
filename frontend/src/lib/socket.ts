"use client";

import { io } from "socket.io-client";

const URL = process.env.NEXT_PUBLIC_SOCKET_URL || "http://localhost:8000";

export const socket = io(`${URL}/chat`, {
  path: "/socket.io",
  transports: ["websocket"],
  autoConnect: false,
});
