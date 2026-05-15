import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../api/auth";
import { useLang } from "../i18n/LangContext";
import LangSwitcher from "../components/LangSwitcher";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { tr } = useLang();
  const [form, setForm] = useState({
    email: "",
    password: "",
    password2: "",
    first_name: "",
    last_name: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(false);

  const set = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setForm((prev) => ({ ...prev, [field]: e.target.value }));
    setErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const handleSubmit = async (e: { preventDefault(): void }) => {
    e.preventDefault();
    setErrors({});

    if (form.password !== form.password2) {
      setErrors({ password2: tr("passwordMismatch") });
      return;
    }

    setLoading(true);
    try {
      await register({
        email: form.email,
        password: form.password,
        password2: form.password2,
        first_name: form.first_name,
        last_name: form.last_name,
      });
      navigate("/login");
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: Record<string, string | string[]> } };
      const data = axiosErr.response?.data;
      if (data && typeof data === "object") {
        const mapped: Record<string, string> = {};
        for (const [k, v] of Object.entries(data)) {
          mapped[k] = Array.isArray(v) ? v.join(" ") : String(v);
        }
        setErrors(mapped);
      } else {
        setErrors({ non_field_errors: tr("registrationFailed") });
      }
    } finally {
      setLoading(false);
    }
  };

  const fieldError = (f: string) =>
    errors[f] ? (
      <p className="text-red-400 text-xs mt-1">{errors[f]}</p>
    ) : null;

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
          <p className="text-gray-400 text-sm">{tr("createAccountDesc")}</p>
          <div className="flex justify-center mt-3">
            <LangSwitcher direction="horizontal" />
          </div>
        </div>

        <div className="bg-[#292828] rounded-xl p-8 shadow-2xl">
          {errors.non_field_errors && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {errors.non_field_errors}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-sm text-gray-300 mb-1.5">{tr("firstName")}</label>
                <input
                  type="text"
                  value={form.first_name}
                  onChange={set("first_name")}
                  className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                  placeholder="John"
                />
                {fieldError("first_name")}
              </div>
              <div>
                <label className="block text-sm text-gray-300 mb-1.5">{tr("lastName")}</label>
                <input
                  type="text"
                  value={form.last_name}
                  onChange={set("last_name")}
                  className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                  placeholder="Doe"
                />
                {fieldError("last_name")}
              </div>
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-1.5">{tr("email")}</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={set("email")}
                className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                placeholder="name@company.com"
              />
              {fieldError("email")}
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-1.5">{tr("password")}</label>
              <input
                type="password"
                required
                value={form.password}
                onChange={set("password")}
                className="w-full bg-[#3d3c3c] border border-[#505050] rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none focus:border-[#6264A7] transition-colors text-sm"
                placeholder="••••••••"
              />
              {fieldError("password")}
            </div>

            <div>
              <label className="block text-sm text-gray-300 mb-1.5">{tr("confirmPassword")}</label>
              <input
                type="password"
                required
                value={form.password2}
                onChange={set("password2")}
                className={`w-full bg-[#3d3c3c] border rounded-lg px-3 py-2.5 text-white placeholder-gray-500 focus:outline-none transition-colors text-sm ${
                  errors.password2 ? "border-red-500/60 focus:border-red-500" : "border-[#505050] focus:border-[#6264A7]"
                }`}
                placeholder="••••••••"
              />
              {fieldError("password2")}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-[#6264A7] hover:bg-[#7274B7] disabled:opacity-50 text-white py-2.5 rounded-lg font-medium text-sm transition-colors mt-1"
            >
              {loading ? tr("creatingAccount") : tr("createAccount")}
            </button>
          </form>

          <p className="text-center text-sm text-gray-400 mt-6">
            {tr("alreadyHaveAccount")}{" "}
            <Link to="/login" className="text-[#8B8CC7] hover:text-[#6264A7] transition-colors">
              {tr("signIn")}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
