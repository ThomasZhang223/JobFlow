"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";

export default function Home() {
  const socketRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<"connecting" | "open" | "closed">(
    "connecting"
  );
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<string[]>([]);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8080/ws/scrape");
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus("open");

      // Initial handshake
      socket.send(
        JSON.stringify({
          type: "handshake",
          payload: "client-connected",
        })
      );
    };

    socket.onmessage = (event) => {
      setMessages((prev) => [...prev, event.data]);
    };

    socket.onerror = (err) => {
      console.error("WebSocket error:", err);
    };

    socket.onclose = () => {
      setStatus("closed");
    };

    return () => {
      socket.close();
    };
  }, []);

  const sendMessage = () => {
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      return;
    }

    socketRef.current.send(input);
    setInput("");
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">
        <Image
          className="dark:invert"
          src="/next.svg"
          alt="Next.js logo"
          width={100}
          height={20}
          priority
        />
  
        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">
          <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">
            WebSocket starter
          </h1>
          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            Status: <span className="font-medium">{status}</span>
          </p>
        </div>
  
        <div className="mt-8 flex w-full flex-col gap-4">
          <div className="h-40 w-full overflow-y-auto rounded border border-zinc-300 dark:border-zinc-700 p-3 text-sm">
            {messages.length === 0 && (
              <p className="text-zinc-500">No messages yet</p>
            )}
            {messages.map((msg, i) => (
              <p key={i} className="text-black dark:text-zinc-100">
                {msg}
              </p>
            ))}
          </div>
  
          <div className="flex gap-2">
            <input
              className="flex-1 rounded border border-zinc-300 dark:border-zinc-700 bg-transparent px-3 py-2 outline-none text-black dark:text-white"
              placeholder="Type a message…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") sendMessage();
              }}
            />
            <button
              className="rounded bg-black px-4 py-2 text-white disabled:opacity-50 dark:bg-white dark:text-black"
              onClick={sendMessage}
              disabled={status !== "open"}
            >
              Send
            </button>
          </div>
        </div>
      </main>
    </div>
  );