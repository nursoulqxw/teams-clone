import api from "./client";
import type { Message } from "../types";

export const getMessages = (channelId: number) =>
  api.get<{ data: Message[] }>(`/messages/?channel_id=${channelId}`);

export const sendMessage = (data: { channel: number; content: string }) =>
  api.post<{ data: Message }>("/messages/", data);

export const editMessage = (id: number, content: string) =>
  api.patch<{ data: Message }>(`/messages/${id}/`, { content });

export const deleteMessage = (id: number) => api.delete(`/messages/${id}/`);
