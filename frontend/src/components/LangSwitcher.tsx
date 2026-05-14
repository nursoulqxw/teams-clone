import { useLang } from "../i18n/LangContext";
import { LANG_LABELS, type Lang } from "../i18n/translations";

const LANGS: Lang[] = ["en", "ru", "kz"];

export default function LangSwitcher() {
  const { lang, setLang } = useLang();

  return (
    <div className="flex gap-0.5 bg-[#3a3939] rounded-lg p-0.5">
      {LANGS.map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          className={`px-2 py-1 rounded-md text-xs font-medium transition-colors ${
            lang === l
              ? "bg-[#6264A7] text-white"
              : "text-gray-400 hover:text-white"
          }`}
        >
          {l.toUpperCase()}
        </button>
      ))}
    </div>
  );
}
