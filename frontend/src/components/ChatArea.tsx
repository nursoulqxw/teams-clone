import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Send, Hash, Pencil, Trash2, Check, X } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { getMessages, sendMessage, editMessage, deleteMessage } from "../api/messages";
import { useWebSocket } from "../hooks/useWebSocket";
import { useAuthStore } from "../store/authStore";
import { useAppStore } from "../store/appStore";
import type { Message } from "../types";

function formatTime(dt: string) {
  return new Date(dt).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function formatDate(dt: string) {
  const d = new Date(dt);
  const today = new Date();
  if (d.toDateString() === today.toDateString()) return "Today";
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
  return d.toLocaleDateString([], { weekday: "long", month: "long", day: "numeric" });
}

export default function ChatArea() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();
  const { activeChannel } = useAppStore();
  const [text, setText] = useState("");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editText, setEditText] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data: httpMessages = [] } = useQuery({
    queryKey: ["messages", activeChannel?.id],
    queryFn: () =>
      getMessages(activeChannel!.id).then((r) => r.data?.data ?? r.data),
    enabled: !!activeChannel,
    refetchInterval: 5000,
  });

  const { messages: wsMessages, send: wsSend, connected } = useWebSocket(
    activeChannel?.id ?? null
  );

  const sendMutation = useMutation({
    mutationFn: (content: string) =>
      sendMessage({ channel: activeChannel!.id, content }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", activeChannel?.id] });
    },
  });

  const editMutation = useMutation({
    mutationFn: ({ id, content }: { id: number; content: string }) =>
      editMessage(id, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", activeChannel?.id] });
      setEditingId(null);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteMessage(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["messages", activeChannel?.id] });
    },
  });

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [httpMessages, wsMessages]);

  const handleSend = () => {
    const content = text.trim();
    if (!content || !activeChannel) return;
    if (connected) {
      wsSend(content);
    } else {
      sendMutation.mutate(content);
    }
    setText("");
  };

  if (!activeChannel) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#F3F2F1] text-gray-500">
        <div className="text-center">
          <Hash size={40} className="mx-auto mb-3 opacity-30" />
          <p className="text-sm">Select a channel to start chatting</p>
        </div>
      </div>
    );
  }

  const messages = httpMessages as Message[];

  const grouped: { date: string; msgs: Message[] }[] = [];
  for (const msg of messages) {
    const dateStr = formatDate(msg.created_at);
    const last = grouped[grouped.length - 1];
    if (last?.date === dateStr) {
      last.msgs.push(msg);
    } else {
      grouped.push({ date: dateStr, msgs: [msg] });
    }
  }

  return (
    <div className="flex-1 flex flex-col bg-white min-w-0">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-gray-200 bg-white">
        <Hash size={18} className="text-gray-500" />
        <span className="font-semibold text-gray-800">{activeChannel.name}</span>
        {activeChannel.description && (
          <>
            <span className="text-gray-300 mx-1">|</span>
            <span className="text-sm text-gray-500">{activeChannel.description}</span>
          </>
        )}
        <div className="ml-auto flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-gray-400"}`} />
          <span className="text-xs text-gray-400">{connected ? "Live" : "Polling"}</span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
        {grouped.map(({ date, msgs }) => (
          <div key={date}>
            <div className="flex items-center gap-3 mb-4">
              <div className="flex-1 h-px bg-gray-200" />
              <span className="text-xs text-gray-400 font-medium px-2">{date}</span>
              <div className="flex-1 h-px bg-gray-200" />
            </div>
            <div className="space-y-1">
              {msgs.map((msg, i) => {
                const showAvatar =
                  i === 0 || msgs[i - 1].sender.id !== msg.sender.id;
                const isOwn = msg.sender.id === user?.id;
                const name = msg.sender.first_name
                  ? `${msg.sender.first_name} ${msg.sender.last_name ?? ""}`.trim()
                  : msg.sender.username;

                return (
                  <div key={msg.id} className={`group flex gap-3 ${showAvatar ? "mt-3" : ""}`}>
                    <div className="w-9 flex-shrink-0">
                      {showAvatar && (
                        <div className="w-9 h-9 rounded-full bg-[#6264A7] flex items-center justify-center text-white text-sm font-medium">
                          {name[0]?.toUpperCase()}
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      {showAvatar && (
                        <div className="flex items-baseline gap-2 mb-0.5">
                          <span className="text-sm font-semibold text-gray-800">{name}</span>
                          <span className="text-xs text-gray-400">{formatTime(msg.created_at)}</span>
                          {msg.is_edited && (
                            <span className="text-xs text-gray-400">(edited)</span>
                          )}
                        </div>
                      )}

                      {editingId === msg.id ? (
                        <div className="flex items-center gap-2">
                          <input
                            autoFocus
                            value={editText}
                            onChange={(e) => setEditText(e.target.value)}
                            onKeyDown={(e) => {
                              if (e.key === "Enter")
                                editMutation.mutate({ id: msg.id, content: editText });
                              if (e.key === "Escape") setEditingId(null);
                            }}
                            className="flex-1 border border-[#6264A7] rounded px-2 py-1 text-sm focus:outline-none"
                          />
                          <button
                            onClick={() =>
                              editMutation.mutate({ id: msg.id, content: editText })
                            }
                            className="text-green-500 hover:text-green-600"
                          >
                            <Check size={16} />
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <X size={16} />
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-start gap-2">
                          <p className="text-sm text-gray-700 leading-relaxed break-words flex-1">
                            {msg.content}
                          </p>
                          {isOwn && (
                            <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0">
                              <button
                                onClick={() => {
                                  setEditingId(msg.id);
                                  setEditText(msg.content);
                                }}
                                className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded"
                              >
                                <Pencil size={13} />
                              </button>
                              <button
                                onClick={() => deleteMutation.mutate(msg.id)}
                                className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                              >
                                <Trash2 size={13} />
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ))}

        {/* Live WS messages (before next poll) */}
        {wsMessages.length > 0 && (
          <div className="space-y-1">
            {wsMessages.map((msg, i) => (
              <div key={i} className="flex gap-3 mt-3">
                <div className="w-9 h-9 rounded-full bg-[#6264A7] flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                  {(msg.sender ?? "?")[0]?.toUpperCase()}
                </div>
                <div>
                  <div className="flex items-baseline gap-2 mb-0.5">
                    <span className="text-sm font-semibold text-gray-800">
                      {msg.sender ?? "Unknown"}
                    </span>
                    <span className="text-xs text-gray-400">
                      {msg.timestamp ? formatTime(msg.timestamp) : "now"}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700">{msg.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="px-4 py-3 border-t border-gray-200 bg-white">
        <div className="flex items-center gap-2 bg-gray-100 rounded-xl px-4 py-2.5">
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder={`Message #${activeChannel.name}`}
            className="flex-1 bg-transparent text-gray-800 text-sm placeholder-gray-400 focus:outline-none"
          />
          <button
            onClick={handleSend}
            disabled={!text.trim()}
            className="p-1.5 bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-40 text-white rounded-lg transition-colors"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
