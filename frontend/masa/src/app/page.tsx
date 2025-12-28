"use client";

import Image from "next/image";
import { useEffect, useRef, useState } from "react";

interface ScrapeUpdate {
  task_id: string;
  status: "pending" | "running" | "completed" | "failed";
  jobs_found: number;
  error_message?: string;
}

export default function Home() {
  const socketRef = useRef<WebSocket | null>(null);
  const [status, setStatus] = useState<"connecting" | "open" | "closed">(
    "connecting"
  );
  const [updates, setUpdates] = useState<ScrapeUpdate[]>([]);

  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8000/ws/scrape");
    socketRef.current = socket;

    socket.onopen = () => {
      setStatus("open");
      console.log("WebSocket connected");
    };

    socket.onmessage = (event) => {
      try {
        const data: ScrapeUpdate = JSON.parse(event.data);
        setUpdates((prev) => [...prev, data]);
      } catch (e) {
        console.error("Failed to parse message:", event.data);
      }
    };

    socket.onclose = (event) => {
      console.log("WebSocket closed:", event.code, event.reason);
      setStatus("closed");
    };

    socket.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    return () => {
      socket.close();
    };
  }, []);

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
            JobFlow Scraper
          </h1>
          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">
            WebSocket Status: <span className="font-medium">{status}</span>
          </p>
        </div>

        <div className="mt-8 flex w-full flex-col gap-4">
          <div className="h-64 w-full overflow-y-auto rounded border border-zinc-300 dark:border-zinc-700 p-3 text-sm">
            {updates.length === 0 && (
              <p className="text-zinc-500">No messages yet</p>
            )}
            {updates.map((update, i) => (
              <pre
                key={i}
                className="mb-2 p-2 rounded bg-zinc-100 dark:bg-zinc-800 text-black dark:text-zinc-100 overflow-x-auto"
              >
                {JSON.stringify(update, null, 2)}
              </pre>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}