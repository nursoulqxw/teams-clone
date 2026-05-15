import { create } from "zustand";
import type { Team, Channel } from "../types";

interface AppState {
  activeTeam: Team | null;
  activeChannel: Channel | null;
  setActiveTeam: (team: Team | null) => void;
  setActiveChannel: (channel: Channel | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  activeTeam: null,
  activeChannel: null,
  setActiveTeam: (team) => set({ activeTeam: team, activeChannel: null }),
  setActiveChannel: (channel) => set({ activeChannel: channel }),
}));
