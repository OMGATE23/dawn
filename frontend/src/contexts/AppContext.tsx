"use client";

import React, { createContext, useContext, useState, ReactNode } from "react";
import { ChatMessage } from "@/types";

interface AppContextType {
  messages: ChatMessage[];
  setMessages: React.Dispatch<React.SetStateAction<ChatMessage[]>>;
  isChatStarted: boolean;
  setIsChatStarted: React.Dispatch<React.SetStateAction<boolean>>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider = ({ children }: { children: ReactNode }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isChatStarted, setIsChatStarted] = useState(false);

  return (
    <AppContext.Provider
      value={{
        messages,
        setMessages,
        isChatStarted,
        setIsChatStarted,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error("useAppContext must be used within an AppProvider");
  }
  return context;
};
