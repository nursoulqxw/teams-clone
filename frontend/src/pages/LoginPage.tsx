import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../api/auth";
import { useAuthStore } from "../store/authStore";

export default function LoginPage() {
  const navigate = useNavigate();
  const setTokens = useAuthStore((s) => s.setTokens);
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await login(form.email, form.password);
      const tokens = res.data?.data ?? res.data;
      setTokens(tokens.access, tokens.refresh);
      navigate("/");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { errors?: string; detail?: string } } };
      setError(
        axiosErr.response?.data?.errors ??
        axiosErr.response?.data?.detail ??
        "Invalid email or password"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#201f1f]">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-2 mb-2">
            <div className="w-8 h-8 bg-[#6264A7] rounded-md flex items-center justify-center">
              <span className="text-white font-bold text-sm">T</span>
            </div>
            <span className="text-xl font-semibold text-white">Teams</span>
          </div>
          <p className="text-gray-400 text-sm">Sign in to your account</p>
        </div>

        <div className="bg-[#292828] rounded-xl p-8 shadow-2xl">
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-gray-300 mb-1.5">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                placeholder="name@company.com"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-1.5">Password</label>
              <input
                type="password"
                required
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-50 text-white py-2.5 rounded-lg font-medium text-sm transition-colors mt-2"
            >
              {loading ? "Signing in…" : "Sign in"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-400 mt-6">
            Don't have an account?{" "}
            <Link to="/register" className="text-[#8B8CC7] hover:text-[#6264A7] transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
