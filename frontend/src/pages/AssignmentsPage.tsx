// frontend/src/pages/AssignmentsPage.tsx
// DEBUG нұсқасы — owner detection логтайды

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ClipboardList, Plus, ChevronDown, ChevronRight,
  Calendar, Check, Users, Star, Pencil, X, Save, Upload, FileText,
} from "lucide-react";
import { useState, useRef } from "react";
import {
  getAssignments, createAssignment, updateAssignment,
  submitAssignment, getSubmissions, gradeSubmission,
} from "../api/assignments";
import { getTeams, getTeamMembers } from "../api/teams";
import { useAuthStore } from "../store/authStore";
import type { Assignment, AssignmentSubmission, Team } from "../types";

// ─── StatusBadge ──────────────────────────────────────────────────────────────
function StatusBadge({ status }: { status?: string }) {
  const s = status ?? "upcoming";
  const map: Record<string, string> = {
    upcoming:       "bg-yellow-100 text-yellow-700",
    overdue:        "bg-red-100 text-red-700",
    completed:      "bg-green-100 text-green-700",
    completed_late: "bg-orange-100 text-orange-700",
  };
  const labels: Record<string, string> = {
    upcoming: "Upcoming", overdue: "Overdue",
    completed: "Completed", completed_late: "Submitted late",
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${map[s] ?? map.upcoming}`}>
      {labels[s] ?? s}
    </span>
  );
}

// ─── SubmitModal ──────────────────────────────────────────────────────────────
function SubmitModal({ assignment, onClose, onSuccess }:
  { assignment: Assignment; onClose: () => void; onSuccess: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const submitMutation = useMutation({
    mutationFn: () => {
      const formData = new FormData();
      formData.append("submitted", "true");
      if (file) formData.append("file", file);
      return submitAssignment(assignment.id, formData);
    },
    onSuccess: () => { onSuccess(); onClose(); },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: { errors?: string; error?: string } } };
      setError(e.response?.data?.errors ?? e.response?.data?.error ?? "Failed to submit.");
    },
  });

  const alreadyDone = assignment.status === "completed" || assignment.status === "completed_late";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <FileText size={18} className="text-[#6264A7]" />
            <h2 className="font-semibold text-gray-800">Submit Assignment</h2>
          </div>
          <button onClick={onClose} className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg">
            <X size={18} />
          </button>
        </div>
        <div className="px-6 py-5 space-y-4">
          <div className="bg-gray-50 rounded-xl p-4 space-y-1">
            <p className="font-medium text-gray-800">{assignment.title}</p>
            {assignment.description && <p className="text-sm text-gray-500">{assignment.description}</p>}
            <div className="flex items-center gap-3 mt-2 flex-wrap">
              {assignment.due_data && (
                <span className="flex items-center gap-1 text-xs text-gray-400">
                  <Calendar size={12} />
                  Due {new Date(assignment.due_data).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}
                </span>
              )}
              {assignment.max_points && <span className="text-xs text-gray-400">{assignment.max_points} pts</span>}
              <StatusBadge status={assignment.status} />
            </div>
          </div>
          {alreadyDone ? (
            <div className="flex items-center gap-2 p-3 bg-green-50 rounded-xl border border-green-200">
              <Check size={18} className="text-green-600" />
              <p className="text-sm text-green-700 font-medium">Already submitted.</p>
            </div>
          ) : (
            <>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">
                  Attach file <span className="text-gray-400 font-normal">(optional)</span>
                </label>
                <input ref={fileRef} type="file" className="hidden" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                <div onClick={() => fileRef.current?.click()}
                  className={`flex items-center gap-3 border-2 border-dashed rounded-xl px-4 py-4 cursor-pointer ${file ? "border-[#6264A7] bg-purple-50" : "border-gray-200 hover:border-[#6264A7]"}`}>
                  <Upload size={20} className={file ? "text-[#6264A7]" : "text-gray-400"} />
                  {file ? (
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-[#6264A7] truncate">{file.name}</p>
                      <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  ) : (
                    <p className="text-sm text-gray-500">Click to upload (optional)</p>
                  )}
                  {file && (
                    <button onClick={(e) => { e.stopPropagation(); setFile(null); if (fileRef.current) fileRef.current.value = ""; }}
                      className="p-1 text-gray-400 hover:text-red-500"><X size={14} /></button>
                  )}
                </div>
              </div>
              {error && <p className="text-sm text-red-500 bg-red-50 rounded-lg px-3 py-2">{error}</p>}
            </>
          )}
        </div>
        <div className="flex justify-end gap-2 px-6 py-4 border-t border-gray-100 bg-gray-50">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-gray-600 hover:bg-gray-100">
            {alreadyDone ? "Close" : "Cancel"}
          </button>
          {!alreadyDone && (
            <button onClick={() => submitMutation.mutate()} disabled={submitMutation.isPending}
              className="flex items-center gap-2 bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-50 text-white px-5 py-2 rounded-xl text-sm font-medium">
              <Check size={16} />
              {submitMutation.isPending ? "Submitting…" : "Submit"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── SubmissionsPanel ─────────────────────────────────────────────────────────
function SubmissionsPanel({ assignmentId, maxPoints }: { assignmentId: number; maxPoints?: number }) {
  const queryClient = useQueryClient();
  const [gradingId, setGradingId] = useState<number | null>(null);
  const [gradeVal, setGradeVal] = useState(0);

  const { data: submissions = [], isLoading } = useQuery({
    queryKey: ["submissions", assignmentId],
    queryFn: () => getSubmissions(assignmentId).then((r) => {
      const raw = (r as { data?: unknown }).data ?? r;
      return Array.isArray(raw) ? raw : [];
    }),
  });

  const gradeMutation = useMutation({
    mutationFn: ({ subId, pts }: { subId: number; pts: number }) =>
      gradeSubmission(assignmentId, subId, pts),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submissions", assignmentId] });
      setGradingId(null);
    },
  });

  if (isLoading) return <p className="text-xs text-gray-400 py-2">Loading submissions…</p>;
  type SubmissionItem = AssignmentSubmission & { id: number; student_email?: string };
  const list = submissions as SubmissionItem[];
  if (list.length === 0)
    return (
      <div className="text-center py-4">
        <Users size={24} className="mx-auto text-gray-300 mb-1" />
        <p className="text-xs text-gray-400">No submissions yet.</p>
      </div>
    );

  return (
    <div className="mt-1 space-y-2">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide flex items-center gap-1">
        <Users size={11} /> Submissions ({list.length})
      </p>
      {list.map((sub) => {
        const email = (sub as { student_email?: string }).student_email
          ?? sub.student_info?.email ?? "Unknown";
        const pts = sub.points_awarded ?? (sub as { points_awarded?: number }).points_awarded;

        return (
          <div key={sub.id} className="flex items-center justify-between bg-gray-50 rounded-xl px-3 py-2.5">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-7 h-7 rounded-full bg-[#6264A7] flex items-center justify-center text-white text-xs font-medium flex-shrink-0">
                {email[0]?.toUpperCase()}
              </div>
              <div className="min-w-0">
                <p className="text-sm text-gray-700 truncate">{email}</p>
                {sub.submitted_at && (
                  <p className="text-xs text-gray-400">
                    {new Date(sub.submitted_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                  </p>
                )}
              </div>
              {sub.submitted
                ? <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full flex-shrink-0">Submitted</span>
                : <span className="text-xs bg-gray-100 text-gray-400 px-1.5 py-0.5 rounded-full flex-shrink-0">Pending</span>}
            </div>
            <div className="flex items-center gap-2 flex-shrink-0 ml-2">
              {typeof pts === "number" && pts > 0 && (
                <span className="text-xs font-semibold text-[#6264A7]">{pts}/{maxPoints ?? "?"}</span>
              )}
              {gradingId === sub.id ? (
                <div className="flex items-center gap-1">
                  <input type="number" min={0} max={maxPoints} value={gradeVal}
                    onChange={(e) => setGradeVal(Number(e.target.value))}
                    className="w-16 border border-gray-300 rounded-lg px-1.5 py-0.5 text-xs focus:outline-none focus:border-[#6264A7]" autoFocus />
                  <button onClick={() => gradeMutation.mutate({ subId: sub.id, pts: gradeVal })}
                    disabled={gradeMutation.isPending} className="text-green-500 hover:text-green-700">
                    <Check size={14} />
                  </button>
                  <button onClick={() => setGradingId(null)} className="text-gray-400 hover:text-gray-600">
                    <X size={14} />
                  </button>
                </div>
              ) : (
                sub.submitted && (
                  <button onClick={() => { setGradingId(sub.id); setGradeVal(typeof pts === "number" ? pts : 0); }}
                    className="flex items-center gap-1 text-xs text-[#6264A7] hover:text-[#7274B7]">
                    <Star size={12} /> Grade
                  </button>
                )
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── EditForm ─────────────────────────────────────────────────────────────────
function EditForm({ assignment, onClose }: { assignment: Assignment; onClose: () => void }) {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ max_points: assignment.max_points ?? 100, due_data: assignment.due_data ?? "" });

  const updateMutation = useMutation({
    mutationFn: () => updateAssignment(assignment.id, { max_points: form.max_points, due_data: form.due_data || undefined }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["assignments"] }); onClose(); },
  });

  return (
    <div className="mt-3 p-4 bg-blue-50 rounded-xl border border-blue-100 space-y-3">
      <p className="text-xs font-semibold text-blue-700 uppercase tracking-wide">Edit assignment</p>
      <div className="flex gap-3 flex-wrap">
        <div>
          <label className="block text-xs text-gray-500 mb-1">Due date</label>
          <input type="date" value={form.due_data} onChange={(e) => setForm({ ...form, due_data: e.target.value })}
            className="border border-gray-200 rounded-lg px-2 py-1.5 text-sm text-gray-800 bg-white focus:outline-none focus:border-[#6264A7]" />
        </div>
        <div>
          <label className="block text-xs text-gray-500 mb-1">Max points</label>
          <input type="number" min={0} value={form.max_points}
            onChange={(e) => setForm({ ...form, max_points: Number(e.target.value) })}
            className="w-24 border border-gray-200 rounded-lg px-2 py-1.5 text-sm text-gray-800 bg-white focus:outline-none focus:border-[#6264A7]" />
        </div>
      </div>
      <div className="flex gap-2">
        <button onClick={() => updateMutation.mutate()} disabled={updateMutation.isPending}
          className="flex items-center gap-1.5 bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-50 text-white px-3 py-1.5 rounded-lg text-sm">
          <Save size={14} /> {updateMutation.isPending ? "Saving…" : "Save"}
        </button>
        <button onClick={onClose} className="px-3 py-1.5 rounded-lg text-sm text-gray-600 hover:bg-blue-100">Cancel</button>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function AssignmentsPage() {
  const queryClient = useQueryClient();
  const { user } = useAuthStore();

  const [selectedTeam, setSelectedTeam] = useState<number | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [showSubmissionsId, setShowSubmissionsId] = useState<number | null>(null);
  const [submitModalAssignment, setSubmitModalAssignment] = useState<Assignment | null>(null);
  const [createForm, setCreateForm] = useState({ title: "", description: "", due_data: "", max_points: 100 });

  // ── Teams ──────────────────────────────────────────────────────────────────
  const { data: teamsRaw } = useQuery({
    queryKey: ["teams"],
    queryFn: () => getTeams().then((r) => {
      // Backend: { message, count, data: [...] }
      // r.data — axios body
      // r.data.data — массив
      const result = r.data?.data ?? r.data ?? [];
      console.log("[DEBUG] raw teams response:", r.data);
      console.log("[DEBUG] teams array:", result);
      return Array.isArray(result) ? result : [];
    }),
  });
  const teams: Team[] = (teamsRaw as Team[]) ?? [];

  // ── Owner detection ────────────────────────────────────────────────────────
  const selectedTeamObj = teams.find((t) => t.id === selectedTeam);

  // Барлық мүмкін форматты тексерейік
  const isOwner = (() => {
    if (!selectedTeamObj || !user) return false;

    const rawOwner = selectedTeamObj.owner;
    const userId = user.id;

    console.log("[DEBUG] selectedTeamObj:", selectedTeamObj);
    console.log("[DEBUG] rawOwner:", rawOwner, "type:", typeof rawOwner);
    console.log("[DEBUG] user.id:", userId, "type:", typeof userId);

    // 1. owner — тікелей number (FK id)
    if (typeof rawOwner === "number") {
      const result = rawOwner === userId;
      console.log("[DEBUG] owner is number, match:", result);
      return result;
    }

    // 2. owner — object {id, first_name, ...} (owner_info сияқты)
    if (typeof rawOwner === "object" && rawOwner !== null) {
      const ownerId = (rawOwner as { id?: number }).id;
      const result = ownerId === userId;
      console.log("[DEBUG] owner is object, ownerId:", ownerId, "match:", result);
      return result;
    }

    // 3. owner — string (кейде API string қайтарады)
    if (typeof rawOwner === "string") {
      const result = Number(rawOwner) === userId;
      console.log("[DEBUG] owner is string, match:", result);
      return result;
    }

    console.log("[DEBUG] owner format unknown, returning false");
    return false;
  })();

  // ── Members ────────────────────────────────────────────────────────────────
  const { data: membersRaw = [] } = useQuery({
    queryKey: ["members", selectedTeam],
    queryFn: () => getTeamMembers(selectedTeam!).then((r) => {
      const result = r.data?.data ?? r.data ?? [];
      console.log("[DEBUG] members:", result);
      return Array.isArray(result) ? result : [];
    }),
    enabled: !!selectedTeam,
  });

  const isMember = (membersRaw as { user?: { id?: number }; id?: number }[])
    .some((m) => (m.user?.id ?? m.id) === user?.id);

  // ── Assignments ────────────────────────────────────────────────────────────
  const { data: assignments = [], isLoading } = useQuery({
    queryKey: ["assignments", selectedTeam],
    queryFn: () => getAssignments(selectedTeam ?? undefined).then((r) => {
      const result = r.data?.data ?? r.data ?? [];
      return Array.isArray(result) ? result : [];
    }),
  });

  // ── Create ─────────────────────────────────────────────────────────────────
  const createMutation = useMutation({
    mutationFn: () =>
      createAssignment({
        title: createForm.title,
        description: createForm.description || undefined,
        team_id: selectedTeam!,
        due_data: createForm.due_data || undefined,
        max_points: createForm.max_points || undefined,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
      setShowCreate(false);
      setCreateForm({ title: "", description: "", due_data: "", max_points: 100 });
    },
    onError: (err: unknown) => {
      const e = err as { response?: { data?: unknown } };
      console.error("[DEBUG] createAssignment error:", e.response?.data);
      alert("Create failed: " + JSON.stringify(e.response?.data));
    },
  });

  const handleTeamSelect = (id: number | null) => {
    setSelectedTeam(id);
    setShowCreate(false);
    setExpandedId(null);
    setEditingId(null);
    setShowSubmissionsId(null);
  };

  return (
    <>
      {submitModalAssignment && (
        <SubmitModal
          assignment={submitModalAssignment}
          onClose={() => setSubmitModalAssignment(null)}
          onSuccess={() => queryClient.invalidateQueries({ queryKey: ["assignments"] })}
        />
      )}

      <div className="flex-1 flex flex-col bg-[#F3F2F1] overflow-hidden">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <ClipboardList size={20} className="text-[#6264A7]" />
              <h1 className="text-lg font-semibold text-gray-800">Assignments</h1>
            </div>
            {selectedTeam && isOwner && (
              <button onClick={() => setShowCreate((v) => !v)}
                className="flex items-center gap-1.5 bg-[#6264A7] hover:bg-[#7274B7] text-white px-3 py-1.5 rounded-lg text-sm">
                <Plus size={16} /> New assignment
              </button>
            )}
          </div>

          {/* Role badge */}
          {selectedTeam && (
            <div className="mt-2">
              {isOwner ? (
                <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium">
                  👑 Owner — create · edit · view submissions · grade
                </span>
              ) : isMember ? (
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                  👤 Member — submit assignments
                </span>
              ) : (
                <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full font-medium">
                  👁 Not a member of this team
                </span>
              )}
            </div>
          )}

          {/* Team tabs */}
          <div className="flex gap-2 mt-3 flex-wrap">
            <button onClick={() => handleTeamSelect(null)}
              className={`px-3 py-1 rounded-full text-sm ${selectedTeam === null ? "bg-[#6264A7] text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
              All teams
            </button>
            {teams.map((t) => (
              <button key={t.id} onClick={() => handleTeamSelect(t.id)}
                className={`px-3 py-1 rounded-full text-sm ${selectedTeam === t.id ? "bg-[#6264A7] text-white" : "bg-gray-100 text-gray-600 hover:bg-gray-200"}`}>
                {t.name}
              </button>
            ))}
          </div>
        </div>

        {/* Create form */}
        {showCreate && isOwner && (
          <div className="bg-white border-b border-gray-200 px-6 py-4">
            <h3 className="font-medium text-gray-800 mb-3">New assignment</h3>
            <div className="space-y-3 max-w-lg">
              <input autoFocus value={createForm.title}
                onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
                placeholder="Title *"
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7] text-gray-800 bg-white" />
              <textarea value={createForm.description}
                onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                placeholder="Description (optional)" rows={3}
                className="w-full border border-gray-200 rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7] resize-none text-gray-800 bg-white" />
              <div className="flex gap-4 flex-wrap">
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-gray-500 font-medium">Due date</label>
                  <input type="date" value={createForm.due_data}
                    onChange={(e) => setCreateForm({ ...createForm, due_data: e.target.value })}
                    min={new Date().toISOString().split("T")[0]}
                    className="border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-800 bg-white focus:outline-none focus:border-[#6264A7]" />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs text-gray-500 font-medium">Max points</label>
                  <input type="number" min={0} value={createForm.max_points}
                    onChange={(e) => setCreateForm({ ...createForm, max_points: Number(e.target.value) })}
                    className="w-24 border border-gray-200 rounded-xl px-3 py-2 text-sm text-gray-800 bg-white focus:outline-none focus:border-[#6264A7]" />
                </div>
              </div>
              <div className="flex gap-2">
                <button onClick={() => createMutation.mutate()}
                  disabled={!createForm.title.trim() || !selectedTeam || createMutation.isPending}
                  className="bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-50 text-white px-4 py-2 rounded-xl text-sm">
                  {createMutation.isPending ? "Creating…" : "Create"}
                </button>
                <button onClick={() => setShowCreate(false)}
                  className="px-4 py-2 rounded-xl text-sm text-gray-600 hover:bg-gray-100">Cancel</button>
              </div>
            </div>
          </div>
        )}

        {/* Assignment list */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="text-gray-400 text-sm">Loading…</div>
          ) : (assignments as Assignment[]).length === 0 ? (
            <div className="text-center text-gray-400 mt-16">
              <ClipboardList size={40} className="mx-auto mb-3 opacity-30" />
              <p className="text-sm">No assignments yet</p>
              {isOwner && <p className="text-xs mt-1 text-gray-300">Click "New assignment" to create one</p>}
            </div>
          ) : (
            <div className="space-y-2 max-w-2xl">
              {(assignments as Assignment[]).map((a) => (
                <div key={a.id} className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-3">
                    <button onClick={() => setExpandedId(expandedId === a.id ? null : a.id)}
                      className="flex-1 flex items-center gap-3 text-left">
                      {expandedId === a.id
                        ? <ChevronDown size={16} className="text-gray-400 flex-shrink-0" />
                        : <ChevronRight size={16} className="text-gray-400 flex-shrink-0" />}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-gray-800 text-sm">{a.title}</span>
                          <StatusBadge status={a.status} />
                          {a.max_points != null && <span className="text-xs text-gray-400">{a.max_points} pts</span>}
                        </div>
                        {a.due_data && (
                          <div className="flex items-center gap-1 mt-0.5 text-xs text-gray-400">
                            <Calendar size={11} />
                            Due {new Date(a.due_data).toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })}
                          </div>
                        )}
                      </div>
                    </button>

                    {isOwner && (
                      <div className="flex gap-1 flex-shrink-0">
                        <button onClick={() => setEditingId(editingId === a.id ? null : a.id)} title="Edit"
                          className={`p-1.5 rounded-lg ${editingId === a.id ? "bg-blue-100 text-blue-600" : "text-gray-400 hover:bg-gray-100"}`}>
                          <Pencil size={14} />
                        </button>
                        <button onClick={() => setShowSubmissionsId(showSubmissionsId === a.id ? null : a.id)} title="Submissions"
                          className={`p-1.5 rounded-lg ${showSubmissionsId === a.id ? "bg-purple-100 text-purple-600" : "text-gray-400 hover:bg-gray-100"}`}>
                          <Users size={14} />
                        </button>
                      </div>
                    )}

                    {!isOwner && isMember && (
                      <button onClick={() => setSubmitModalAssignment(a)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium flex-shrink-0 ${
                          a.status === "completed" || a.status === "completed_late"
                            ? "bg-green-100 text-green-700 cursor-default"
                            : "bg-[#6264A7] hover:bg-[#7274B7] text-white"
                        }`}>
                        <Check size={14} />
                        {a.status === "completed" || a.status === "completed_late" ? "Submitted" : "Submit"}
                      </button>
                    )}
                  </div>

                  {expandedId === a.id && (
                    <div className="px-4 pb-4 border-t border-gray-100 pt-3 space-y-2">
                      {a.description && <p className="text-sm text-gray-600">{a.description}</p>}
                      {isOwner && editingId === a.id && <EditForm assignment={a} onClose={() => setEditingId(null)} />}
                      {isOwner && showSubmissionsId === a.id && <SubmissionsPanel assignmentId={a.id} maxPoints={a.max_points} />}
                      {!isOwner && isMember && (
                        <button onClick={() => setSubmitModalAssignment(a)}
                          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium ${
                            a.status === "completed" || a.status === "completed_late"
                              ? "bg-green-100 text-green-700" : "bg-[#6264A7] hover:bg-[#7274B7] text-white"
                          }`}>
                          <Check size={14} />
                          {a.status === "completed" || a.status === "completed_late" ? "Already submitted" : "Submit assignment"}
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}