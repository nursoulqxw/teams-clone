import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, LogOut, User, ClipboardList } from "lucide-react";
import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { getTeams, createTeam, addTeamMember } from "../api/teams";
import { logout } from "../api/auth";
import { useAuthStore } from "../store/authStore";
import { useAppStore } from "../store/appStore";
import { useLang } from "../i18n/LangContext";
import LangSwitcher from "./LangSwitcher";
import type { Team } from "../types";

export default function TeamsSidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const { user, logout: storeLogout } = useAuthStore();
  const { activeTeam, setActiveTeam } = useAppStore();
  const [showCreate, setShowCreate] = useState(false);
  const [newTeamName, setNewTeamName] = useState("");

  const { data } = useQuery({
    queryKey: ["teams"],
    queryFn: () => getTeams().then((r) => r.data?.data ?? r.data),
  });

  const createMutation = useMutation({
    mutationFn: async (name: string) => {
      const res = await createTeam({ name });
      const team: Team = res.data?.data ?? res.data;
      // Backend doesn't auto-add the owner to members — do it now so
      // channel creation (which checks team.members) works immediately.
      if (user?.id) {
        try {
          await addTeamMember(team.id, user.id);
        } catch {
          // ignore if already a member or endpoint unavailable
        }
      }
      return team;
    },
    onSuccess: (team) => {
      queryClient.invalidateQueries({ queryKey: ["teams"] });
      setShowCreate(false);
      setNewTeamName("");
      setActiveTeam(team);
    },
  });

  const handleLogout = async () => {
    const refresh = localStorage.getItem("refresh_token");
    if (refresh) {
      try {
        await logout(refresh);
      } catch {
        // ignore
      }
    }
    storeLogout();
    navigate("/login");
  };

  const { tr } = useLang();
  const teams: Team[] = data ?? [];

  return (
    <div className="w-[72px] bg-[#201f1f] flex flex-col items-center py-3 gap-1 border-r border-[#3a3939] flex-shrink-0">
      {/* App icon — click returns to main chat */}
      <button
        onClick={() => navigate("/")}
        className="w-10 h-10 bg-[#6264A7] hover:bg-[#7274B7] rounded-xl flex items-center justify-center mb-3 flex-shrink-0 transition-colors"
        title={tr("goToChat")}
      >
        <span className="text-white font-bold text-lg">T</span>
      </button>

      {/* Teams */}
      <div className="flex flex-col gap-1 items-center w-full px-2 overflow-y-auto flex-1">
        {teams.map((team) => (
          <button
            key={team.id}
            onClick={() => { setActiveTeam(team); navigate("/"); }}
            title={team.name}
            className={`w-10 h-10 rounded-xl flex items-center justify-center text-xs font-bold transition-all flex-shrink-0 ${
              activeTeam?.id === team.id && location.pathname === "/"
                ? "bg-white text-[#6264A7] rounded-2xl"
                : "bg-[#3a3939] text-gray-300 hover:bg-[#6264A7] hover:text-white hover:rounded-2xl"
            }`}
          >
            {team.name.slice(0, 2).toUpperCase()}
          </button>
        ))}

        {/* Create team */}
        {showCreate ? (
          <div className="w-full px-1">
            <input
              autoFocus
              value={newTeamName}
              onChange={(e) => setNewTeamName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && newTeamName.trim()) {
                  createMutation.mutate(newTeamName.trim());
                } else if (e.key === "Escape") {
                  setShowCreate(false);
                  setNewTeamName("");
                }
              }}
              className="w-full bg-[#3a3939] text-white text-xs rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-[#6264A7]"
              placeholder="Name…"
            />
          </div>
        ) : (
          <button
            onClick={() => setShowCreate(true)}
            title="Add team"
            className="w-10 h-10 rounded-xl bg-[#3a3939] text-gray-400 hover:bg-[#6264A7] hover:text-white hover:rounded-2xl flex items-center justify-center transition-all flex-shrink-0"
          >
            <Plus size={18} />
          </button>
        )}
      </div>

      {/* Bottom actions */}
      <div className="flex flex-col gap-1 items-center pb-1">
        {/* Language switcher */}
        <div className="mb-1">
          <LangSwitcher />
        </div>
        <button
          onClick={() => navigate("/assignments")}
          title={tr("assignments")}
          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
            location.pathname === "/assignments"
              ? "bg-[#6264A7] text-white"
              : "text-gray-400 hover:bg-[#3a3939] hover:text-white"
          }`}
        >
          <ClipboardList size={20} />
        </button>
        <button
          onClick={() => navigate("/profile")}
          title={tr("profile")}
          className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
            location.pathname === "/profile"
              ? "bg-[#6264A7] text-white"
              : "text-gray-400 hover:bg-[#3a3939] hover:text-white"
          }`}
        >
          <User size={20} />
        </button>
        <button
          onClick={handleLogout}
          title={tr("signOut")}
          className="w-10 h-10 rounded-xl text-gray-400 hover:bg-red-500/20 hover:text-red-400 flex items-center justify-center transition-all"
        >
          <LogOut size={20} />
        </button>
      </div>
    </div>
  );
}
