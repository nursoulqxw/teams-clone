import { createContext, useContext, useState, useCallback } from "react";
import t, { type Lang, type TKey } from "./translations";

interface LangCtx {
  lang: Lang;
  setLang: (l: Lang) => void;
  tr: (key: TKey) => string;
}

const LangContext = createContext<LangCtx>({
  lang: "en",
  setLang: () => {},
  tr: (k) => k,
});

export function LangProvider({ children }: { children: React.ReactNode }) {
  const stored = (localStorage.getItem("lang") as Lang) ?? "en";
  const [lang, setLangState] = useState<Lang>(stored);

  const setLang = useCallback((l: Lang) => {
    localStorage.setItem("lang", l);
    setLangState(l);
  }, []);

  const tr = useCallback((key: TKey) => t[lang][key] as string, [lang]);

  return (
    <LangContext.Provider value={{ lang, setLang, tr }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
