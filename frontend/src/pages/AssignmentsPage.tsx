import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ClipboardList, Plus, ChevronDown, ChevronRight, Calendar, Check } from "lucide-react";
import { useState } from "react";
import { getAssignments, createAssignment, submitAssignment } from "../api/assignments";
import { getTeams } from "../api/teams";
import type { Assignment, Team } from "../types";

function StatusBadge({ status }: { status?: string }) {
  const s = status ?? "pending";
  const map: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-700",
    submitted: "bg-blue-100 text-blue-700",
    graded: "bg-green-100 text-green-700",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[s] ?? map.pending}`}>
      {s.charAt(0).toUpperCase() + s.slice(1)}
    </span>
  );
}

export default function AssignmentsPage() {
  const queryClient = useQueryClient();
  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [form, setForm] = useState({ title: "", description: "", due_date: "" });

  const { data: teams = [] } = useQuery({
    queryKey: ["teams"],
    queryFn: () => getTeams().then((r) => r.data?.data ?? r.data),
  });

  const { data: assignments = [], isLoading } = useQuery({
    queryKey: ["assignments", selectedTeam],
    queryFn: () =>
      getAssignments(selectedTeam ?? undefined).then(
        (r) => r.data?.data ?? r.data
      ),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createAssignment({
        title: form.title,
        description: form.description || undefined,
        team: selectedTeam!,
        due_date: form.due_date || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      setShowCreate(false);
      setForm({ title: "", description: "", due_date: "" });
    },
  });

  const submitMutation = useMutation({
    mutationFn: (id: number) => submitAssignment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });

  return (
    <div className="flex-1 flex flex-col bg-[#F3F2F1] overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ClipboardList size={20} className="text-[#6264A7]" />
            <h1 className="text-lg font-semibold text-gray-800">Assignments</h1>
          </div>
          {selectedTeam && (
            <button
              onClick={() => setShowCreate(true)}
              className="flex items-center gap-1.5 bg-[#6264A7] hover:bg-[#7274B7] text-white px-3 py-1.5 rounded-lg text-sm transition-colors"
            >
              <Plus size={16} />
              New assignment
            </button>
          )}
        </div>

        {/* Team filter */}
        <div className="flex gap-2 mt-3 flex-wrap">
          <button
            onClick={() => setSelectedTeam(null)}
            className={`px-3 py-1 rounded-full text-sm transition-colors ${
              selectedTeam === null
                ? "bg-[#6264A7] text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            All teams
          </button>
          {(teams as Team[]).map((t) => (
            <button
              key={t.id}
              onClick={() => setSelectedTeam(t.id)}
              className={`px-3 py-1 rounded-full text-sm transition-colors ${
                selectedTeam === t.id
                  ? "bg-[#6264A7] text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {t.name}
            </button>
          ))}
        </div>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <h3 className="font-medium text-gray-800 mb-3">New assignment</h3>
          <div className="space-y-3 max-w-lg">
            <input
              autoFocus
              value={form.title}
              onChange={(e) => setForm({ ...form, title: e.target.value })}
              placeholder="Title"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7] text-gray-800 bg-white"
            />

            <textarea
              value={form.description}
              onChange={(e) => setForm({ ...form, description: e.target.value })}
              placeholder="Description (optional)"
              rows={3}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7] resize-none text-gray-800 bg-white"
            />
            <input
              type="datetime-local"
              value={form.due_date}
              onChange={(e) => setForm({ ...form, due_date: e.target.value })}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7]"
            />
            <div className="flex gap-2">
              <button
                onClick={() => createMutation.mutate()}
                disabled={!form.title.trim() || !selectedTeam || createMutation.isPending}
                className="bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors"
              >
                {createMutation.isPending ? "Creating…" : "Create"}
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="px-4 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-100 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* List */}
      <div className="flex-1 overflow-y-auto p-6">
        {isLoading ? (
          <div className="text-gray-400 text-sm">Loading…</div>
        ) : (assignments as Assignment[]).length === 0 ? (
          <div className="text-center text-gray-400 mt-16">
            <ClipboardList size={40} className="mx-auto mb-3 opacity-30" />
            <p className="text-sm">No assignments yet</p>
          </div>
        ) : (
          <div className="space-y-2 max-w-2xl">
            {(assignments as Assignment[]).map((a) => (
              <div key={a.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <button
                  onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}
                  className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-50 transition-colors"
                >
                  {expandedId === a.id ? (
                    <ChevronDown size={16} className="text-gray-400 flex-shrink-0" />
                  ) : (
                    <ChevronRight size={16} className="text-gray-400 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-gray-800 text-sm">{a.title}</span>
                      <StatusBadge status={a.status} />
                    </div>
                    {a.due_date && (
                      <div className="flex items-center gap-1 mt-0.5 text-xs text-gray-400">
                        <Calendar size={11} />
                        Due{" "}
                        {new Date(a.due_date).toLocaleDateString([], {
                          month: "short",
                          day: "numeric",
                          year: "numeric",
                        })}
                      </div>
                    )}
                  </div>
                </button>

                {expandedId === a.id && (
                  <div className="px-4 pb-4 border-t border-gray-100 pt-3">
                    {a.description && (
                      <p className="text-sm text-gray-600 mb-3">{a.description}</p>
                    )}
                    <button
                      onClick={() => submitMutation.mutate(a.id)}
                      disabled={submitMutation.isPending}
                      className="flex items-center gap-1.5 bg-green-500 hover:bg-green-600 disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-sm transition-colors"
                    >
                      <Check size={15} />
                      Submit assignment
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
