import api from "./client";
import type { Channel } from "../types";

export const getChannels = (teamId: number) =>
  api.get<{ data: Channel[] }>(`/channels/?team_id=${teamId}`);

export const createChannel = (data: {
  name: string;
  description?: string;
  team: number;
}) => api.post<{ data: Channel }>("/channels/", data);

export const updateChannel = (id: number, data: Partial<Channel>) =>
  api.patch<{ data: Channel }>(`/channels/${id}/`, data);

export const deleteChannel = (id: number) => api.delete(`/channels/${id}/`);
