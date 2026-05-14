import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Hash, Plus, Users, ChevronDown, ChevronRight, UserPlus, X } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { getChannels, createChannel } from "../api/channels";
import { getTeamMembers, addTeamMember, searchUsers } from "../api/teams";
import { useAppStore } from "../store/appStore";
import type { Channel, User } from "../types";

export default function ChannelList() {
  const queryClient = useQueryClient();
  const { activeTeam, activeChannel, setActiveChannel } = useAppStore();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [createError, setCreateError] = useState("");
  const [channelsOpen, setChannelsOpen] = useState(true);
  const [membersOpen, setMembersOpen] = useState(true);

  // Add member state
  const [showAddMember, setShowAddMember] = useState(false);
  const [search, setSearch] = useState("");
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [addError, setAddError] = useState("");
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

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
      setCreateError("");
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { error?: Record<string, string[]> | string } } };
      const d = e.response?.data?.error;
      if (typeof d === "string") setCreateError(d);
      else if (d && typeof d === "object") {
        setCreateError(Object.values(d).flat().join(" "));
      } else {
        setCreateError("Failed to create channel");
      }
    },
  });

  const addMemberMutation = useMutation({
    mutationFn: (userId: number) => addTeamMember(activeTeam!.id, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["members", activeTeam?.id] });
      setShowAddMember(false);
      setSearch("");
      setSearchResults([]);
      setAddError("");
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { error?: string; detail?: string } } };
      setAddError(
        e.response?.data?.error ?? e.response?.data?.detail ?? "Failed to add member"
      );
    },
  });

  // Debounced search
  useEffect(() => {
    if (!search.trim()) { setSearchResults([]); return; }
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(async () => {
      try {
        const res = await searchUsers(search);
        const raw = res.data?.results ?? res.data?.data ?? res.data;
        setSearchResults(Array.isArray(raw) ? (raw as User[]) : []);
      } catch {
        setSearchResults([]);
      }
    }, 300);
    return () => { if (searchTimer.current) clearTimeout(searchTimer.current); };
  }, [search]);

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
        <h2 className="font-semibold text-white text-sm truncate">{activeTeam.name}</h2>
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
                <div className="px-2 py-1 space-y-1">
                  <input
                    autoFocus
                    value={newName}
                    onChange={(e) => { setNewName(e.target.value); setCreateError(""); }}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && newName.trim()) createMutation.mutate(newName.trim());
                      else if (e.key === "Escape") { setShowCreate(false); setNewName(""); }
                    }}
                    className="w-full bg-[#3a3939] text-white text-sm rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#6264A7]"
                    placeholder="channel-name"
                  />
                  {createError && <p className="text-red-400 text-xs px-1">{createError}</p>}
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
          <div className="flex items-center justify-between px-2 py-1">
            <button
              onClick={() => setMembersOpen((v) => !v)}
              className="flex items-center gap-1 text-xs font-semibold text-gray-400 hover:text-white uppercase tracking-wider transition-colors"
            >
              {membersOpen ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
              <Users size={12} className="ml-0.5" />
              Members
            </button>
            <button
              onClick={() => { setShowAddMember((v) => !v); setSearch(""); setSearchResults([]); setAddError(""); }}
              title="Add member"
              className="text-gray-400 hover:text-white transition-colors"
            >
              <UserPlus size={14} />
            </button>
          </div>

          {/* Add member panel */}
          {showAddMember && (
            <div className="px-1 pb-2 space-y-1">
              <div className="flex items-center gap-1">
                <input
                  autoFocus
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setAddError(""); }}
                  placeholder="Search by name or email"
                  className="flex-1 bg-[#3a3939] text-white text-xs rounded px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-[#6264A7] placeholder-gray-500"
                />
                <button
                  onClick={() => { setShowAddMember(false); setSearch(""); setSearchResults([]); }}
                  className="text-gray-500 hover:text-white"
                >
                  <X size={14} />
                </button>
              </div>

              {addError && <p className="text-red-400 text-xs px-1">{addError}</p>}

              {searchResults.length > 0 && (
                <div className="bg-[#3a3939] rounded-lg overflow-hidden">
                  {searchResults.map((u) => {
                    const name = u.first_name
                      ? `${u.first_name} ${u.last_name ?? ""}`.trim()
                      : u.username;
                    return (
                      <button
                        key={u.id}
                        onClick={() => addMemberMutation.mutate(u.id)}
                        disabled={addMemberMutation.isPending}
                        className="flex items-center gap-2 w-full px-3 py-2 text-xs text-gray-300 hover:bg-[#6264A7] hover:text-white transition-colors"
                      >
                        <div className="w-5 h-5 rounded-full bg-[#6264A7] flex items-center justify-center text-white text-xs flex-shrink-0">
                          {name[0]?.toUpperCase()}
                        </div>
                        <div className="text-left">
                          <div className="font-medium">{name}</div>
                          <div className="text-gray-500 text-xs">{u.email}</div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {search.trim() && searchResults.length === 0 && (
                <p className="text-gray-500 text-xs px-1">No users found</p>
              )}
            </div>
          )}

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
