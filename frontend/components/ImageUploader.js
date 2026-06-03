"use client";

import React, { useCallback, useRef, useState } from "react";
import { multimodalAnalyze } from "../lib/api";
import { useLanguage } from "../lib/i18n";

export function ImageUploader({ token, onResult, className }) {
  const { t, locale } = useLanguage();
  const inputRef = useRef(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const run = useCallback(
    async (file) => {
      setBusy(true);
      setErr(null);
      try {
        const data = await multimodalAnalyze(file, { deep: false, token: token || undefined });
        if (onResult) onResult(data);
      } catch (e) {
        setErr(e instanceof Error ? e.message : t("fileUploadFailure", locale));
      } finally {
        setBusy(false);
      }
    },
    [onResult, token]
  );

  return (
    <div className={className}>
      <input
        ref={inputRef}
        type="file"
        accept="image/*,application/pdf,audio/*,.txt,.md,.json"
        className="hidden"
        onChange={(ev) => {
          const f = ev.target.files && ev.target.files[0];
          if (f) void run(f);
        }}
      />
      <button
        type="button"
        disabled={busy}
        className="rounded-lg border border-zinc-600 bg-zinc-900/80 px-3 py-2 text-sm text-zinc-100 hover:bg-zinc-800 disabled:opacity-50"
        onClick={() => inputRef.current && inputRef.current.click()}
      >
        {busy ? t("imageUploadBusyText", locale) : t("imageUploadButtonText", locale)}
      </button>
      {err ? <p className="mt-2 text-sm text-red-400">{err}</p> : null}
    </div>
  );
}
