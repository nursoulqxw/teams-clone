import { useEffect, useRef, useState, useCallback } from "react";
import type { WSMessage } from "../types";

export function useWebSocket(channelId: number | null) {
  const ws = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [connected, setConnected] = useState(false);

  const send = useCallback((content: string) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ message: content }));
    }
  }, []);

  useEffect(() => {
    if (!channelId) return;

    const token = localStorage.getItem("access_token");
    const url = `ws://${window.location.host}/ws/chat/${channelId}/?token=${token}`;
    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);

    socket.onmessage = (event) => {
      try {
        const data: WSMessage = JSON.parse(event.data);
        setMessages((prev) => [...prev, data]);
      } catch {
        // ignore malformed frames
      }
    };

    return () => {
      socket.close();
      setMessages([]);
      setConnected(false);
    };
  }, [channelId]);

  return { messages, send, connected };
}
