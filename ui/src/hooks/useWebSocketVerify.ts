import { useState, useCallback, useRef } from "react";

export interface VerificationEvent {
  event: "start" | "iteration" | "waveform" | "complete" | "error";
  message?: string;
  iteration?: number;
  action?: string;
  success?: boolean;
  pass_rate?: number;
  stdout?: string;
  wavedrom?: any;
  summary?: string;
}

export function useWebSocketVerify() {
  const [isRunning, setIsRunning] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const [wavedromData, setWavedromData] = useState<any>(null);
  const [resultSummary, setResultSummary] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [retryCount, setRetryCount] = useState(0);


    

  const startVerification = useCallback((rtlCode: string, moduleName: string, maxRetries = 3) => {
    setIsRunning(true);
    setLogs(["[EDA-AGENT] Initializing verification session..."]);
    setWavedromData(null);
    setResultSummary(null);

    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host || "localhost:8000";
    const ws = new WebSocket(`${proto}//${host}/ws/verify`);
    const handleRetry = () => {
      if (retryCount < maxRetries) {
        setRetryCount((prev) => prev + 1);
      }
    };
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({
        rtl_code: rtlCode,
        module_name: moduleName,
        max_retries: maxRetries,
      }));
    };

    ws.onmessage = (event) => {
      const data: VerificationEvent = JSON.parse(event.data);
      if (data.event === "start") {
        setLogs((prev) => [...prev, `⚡ ${data.message}`]);
      } else if (data.event === "iteration") {
        setLogs((prev) => [
          ...prev,
          `[ITERATION ${data.iteration}] ${data.action} | Pass Rate: ${data.pass_rate}%`,
          data.stdout || "",
        ]);
      } else if (data.event === "waveform") {
        setWavedromData(data.wavedrom);
      } else if (data.event === "complete") {
        setIsRunning(false);
        setResultSummary(data.summary || "Complete");
        setLogs((prev) => [...prev, `🏆 ${data.summary}`]);
      } else if (data.event === "error") {
        setIsRunning(false);
        setLogs((prev) => [...prev, `❌ Error: ${data.message}`]);
      }
    };

    ws.onerror = () => {
      setIsRunning(false);
      setLogs((prev) => [...prev, "[ERROR] WebSocket connection failed."]);
    };
  }, []);

  return {
    isRunning,
    logs,
    wavedromData,
    resultSummary,
    startVerification,
  };
}
