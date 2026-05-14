import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Hash, Plus, Users, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { getChannels, createChannel } from "../api/channels";
import { getTeamMembers } from "../api/teams";
import { useAppStore } from "../store/appStore";
import type { Channel } from "../types";

export default function ChannelList() {
  const queryClient = useQueryClient();
  const { activeTeam, activeChannel, setActiveChannel } = useAppStore();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [channelsOpen, setChannelsOpen] = useState(true);
  const [membersOpen, setMembersOpen] = useState(true);

  const { data: channels = [] } = useQuery({
    queryKey: ["channels", activeTeam?.id],
    queryFn: () =>
      getChannels(activeTeam!.id).then((r) => r.data?.data ?? r.data),
    enabled: !!activeTeam,
  });

  const { data: members = [] } = useQuery({
    queryKey: ["members", activeTeam?.id],
    queryFn: () =>
      getTeamMembers(activeTeam!.id).then((r) => r.data?.data ?? r.data),
    enabled: !!activeTeam,
  });

  const createMutation = useMutation({
    mutationFn: (name: string) => createChannel({ name, team: activeTeam!.id }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channels", activeTeam?.id] });
      setShowCreate(false);
      setNewName("");
    },
  });

  if (!activeTeam) {
    return (
      <div className="w-64 bg-[#292828] flex items-center justify-center text-gray-500 text-sm">
        Select a team
      </div>
    );
  }

  return (
    <div className="w-64 bg-[#292828] flex flex-col">
      <div className="px-4 py-3 border-b border-[#3a3939]">
        <h2 className="font-semibold text-white text-sm truncate">
          {activeTeam.name}
        </h2>
        <p className="text-xs text-gray-400 mt-0.5">
          {(members as unknown[]).length} member{(members as unknown[]).length !== 1 ? "s" : ""}
        </p>
      </div>

      <div className="flex-1 overflow-y-auto py-2 space-y-1">
        {/* Channels */}
        <div className="px-2">
          <button
            onClick={() => setChannelsOpen((v) => !v)}
            className="flex items-center gap-1 w-full text-xs font-semibold text-gray-400 hover:text-white uppercase tracking-wider px-2 py-1 rounded transition-colors"
          >
            {channelsOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            Channels
          </button>

          {channelsOpen && (
            <div className="mt-0.5 space-y-0.5">
              {(channels as Channel[]).map((ch) => (
                <button
                  key={ch.id}
                  onClick={() => setActiveChannel(ch)}
                  className={`flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-sm transition-colors ${
                    activeChannel?.id === ch.id
                      ? "bg-[#6264A7] text-white"
                      : "text-gray-300 hover:bg-[#3a3939] hover:text-white"
                  }`}
                >
                  <Hash size={15} className="flex-shrink-0 opacity-70" />
                  <span className="truncate">{ch.name}</span>
                </button>
              ))}

              {showCreate ? (
                <div className="px-2 py-1">
                  <input
                    autoFocus
                    value={newName}
                    onChange={(e) => setNewName(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newName.trim()) {
                        createMutation.mutate(newName.trim());
                      } else if (e.key === "Escape") {
                        setShowCreate(false);
                        setNewName("");
                      }
                    }}
                    className="w-full bg-[#3a3939] text-white text-sm rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#6264A7]"
                    placeholder="channel-name"
                  />
                </div>
              ) : (
                <button
                  onClick={() => setShowCreate(true)}
                  className="flex items-center gap-2 w-full px-2 py-1.5 rounded-lg text-sm text-gray-400 hover:bg-[#3a3939] hover:text-white transition-colors"
                >
                  <Plus size={15} />
                  Add channel
                </button>
              )}
            </div>
          )}
        </div>

        {/* Members */}
        <div className="px-2 mt-3">
          <button
            onClick={() => setMembersOpen((v) => !v)}
            className="flex items-center gap-1 w-full text-xs font-semibold text-gray-400 hover:text-white uppercase tracking-wider px-2 py-1 rounded transition-colors"
          >
            {membersOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
            <Users size={12} className="ml-0.5" />
            Members
          </button>

          {membersOpen && (
            <div className="mt-0.5 space-y-0.5">
              {(members as { id: number; user?: { username?: string; first_name?: string; last_name?: string }; username?: string }[]).map((m) => {
                const u = (m.user ?? m) as { username?: string; first_name?: string; last_name?: string };
                const name = u.first_name
                  ? `${u.first_name} ${u.last_name ?? ""}`.trim()
                  : u.username ?? "Unknown";
                return (
                  <div key={m.id} className="flex items-center gap-2 px-2 py-1.5 text-sm text-gray-400">
                    <div className="w-5 h-5 rounded-full bg-[#6264A7] flex items-center justify-center text-white text-xs flex-shrink-0">
                      {name[0]?.toUpperCase()}
                    </div>
                    <span className="truncate">{name}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
