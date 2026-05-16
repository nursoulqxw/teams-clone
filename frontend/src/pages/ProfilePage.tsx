import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { User, Save } from "lucide-react";
import { useState, useEffect } from "react";
import { getMe, updateMe } from "../api/auth";
import { useAuthStore } from "../store/authStore";

export default function ProfilePage() {
  const queryClient = useQueryClient();
  const setUser = useAuthStore((s) => s.setUser);
  const [form, setForm] = useState({
    first_name: "",
    last_name: "",
    username: "",
    email: "",
  });
  const [saved, setSaved] = useState(false);

  const { data: meData, isLoading } = useQuery({
    queryKey: ["me"],
    queryFn: () => getMe().then((r) => r.data?.data ?? r.data),
  });

  useEffect(() => {
    if (meData) {
      const u = meData as { first_name?: string; last_name?: string; username?: string; email?: string };
      setForm({
        first_name: u.first_name ?? "",
        last_name: u.last_name ?? "",
        username: u.username ?? "",
        email: u.email ?? "",
      });
    }
  }, [meData]);

  const updateMutation = useMutation({
    mutationFn: () => updateMe(form),
    onSuccess: (res) => {
      const updated = res.data?.data ?? res.data;
      setUser(updated);
      queryClient.invalidateQueries({ queryKey: ["me"] });
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    },
  });

  if (isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center bg-[#F3F2F1] text-gray-400 text-sm">
        Loading…
      </div>
    );
  }

  const initials = (
    (form.first_name?.[0] ?? "") + (form.last_name?.[0] ?? "")
  ).toUpperCase() || form.username?.[0]?.toUpperCase() || "U";

  return (
    <div className="flex-1 bg-[#F3F2F1] overflow-y-auto">
      <div className="max-w-lg mx-auto py-10 px-6">
        <div className="flex items-center gap-2 mb-8">
          <User size={20} className="text-[#6264A7]" />
          <h1 className="text-lg font-semibold text-gray-800">Profile</h1>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 p-6">
          {/* Avatar */}
          <div className="flex items-center gap-4 mb-6 pb-6 border-b border-gray-100">
            <div className="w-16 h-16 rounded-full bg-[#6264A7] flex items-center justify-center text-white text-2xl font-semibold">
              {initials}
            </div>
            <div>
              <p className="font-semibold text-gray-800">
                {form.first_name || form.last_name
                  ? `${form.first_name} ${form.last_name}`.trim()
                  : form.username}
              </p>
              <p className="text-sm text-gray-400">{form.email}</p>
            </div>
          </div>

          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wide">
                  First name
                </label>
                <input
                  value={form.first_name}
                  onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7] transition-colors"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wide">
                  Last name
                </label>
                <input
                  value={form.last_name}
                  onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7] transition-colors"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wide">
                Username
              </label>
              <input
                value={form.username}
                onChange={(e) => setForm({ ...form, username: e.target.value })}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7] transition-colors"
              />
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wide">
                Email
              </label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-[#6264A7] transition-colors"
              />
            </div>

            <button
              onClick={() => updateMutation.mutate()}
              disabled={updateMutation.isPending}
              className="flex items-center gap-2 bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm transition-colors mt-2"
            >
              <Save size={15} />
              {saved ? "Saved!" : updateMutation.isPending ? "Saving…" : "Save changes"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
