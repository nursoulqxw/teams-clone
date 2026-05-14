import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/auth";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await register(form);
      navigate("/login");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, unknown> } };
      const data = axiosErr.response?.data;
      if (data) {
        const msg = Object.values(data).flat().join(" ");
        setError(msg || "Registration failed");
      } else {
        setError("Registration failed");
      }
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
          <p className="text-gray-400 text-sm">Create your account</p>
        </div>

        <div className="bg-[#292828] rounded-xl p-8 shadow-2xl">
          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-300 mb-1.5">First name</label>
                <input
                  type="text"
                  value={form.first_name}
                  onChange={set("first_name")}
                  className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                  placeholder="John"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-300 mb-1.5">Last name</label>
                <input
                  type="text"
                  value={form.last_name}
                  onChange={set("last_name")}
                  className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                  placeholder="Doe"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-1.5">Username</label>
              <input
                type="text"
                required
                value={form.username}
                onChange={set("username")}
                className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                placeholder="johndoe"
              />
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-1.5">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={set("email")}
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
                onChange={set("password")}
                className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                placeholder="••••••••"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-50 text-white py-2.5 rounded-lg font-medium text-sm transition-colors mt-1"
            >
              {loading ? "Creating account…" : "Create account"}
            </button>
          </form>

          <p className="text-center text-sm text-gray-400 mt-6">
            Already have an account?{" "}
            <Link to="/login" className="text-[#8B8CC7] hover:text-[#6264A7] transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
