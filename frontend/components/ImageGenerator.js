"use client";

import React, { useState } from "react";
import { generateImage } from "../lib/api";
import { describeGeneratedImageMeta } from "../lib/puter-image";
import { useLanguage } from "../lib/i18n";

export function ImageGenerator({ token, onImage, className }) {
  const { t, locale } = useLanguage();
  const [prompt, setPrompt] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  return (
    <div className={className}>
      <input
        className="mb-2 w-full rounded border border-zinc-600 bg-zinc-950 px-3 py-2 text-sm"
        placeholder={t("imageGeneratorPlaceholder", locale)}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      />
      <button
        type="button"
        disabled={busy || !prompt.trim()}
        className="rounded-lg bg-violet-700 px-4 py-2 text-sm font-medium text-white hover:bg-violet-600 disabled:opacity-50"
        onClick={async () => {
          setBusy(true);
          setErr(null);
          try {
            const data = await generateImage(prompt, token || undefined);
            if (data && data.image_base64) {
              describeGeneratedImageMeta(prompt, data.mime, data.image_base64.length);
            }
            if (onImage) onImage(data);
          } catch (e) {
            setErr(e instanceof Error ? e.message : t("error", locale));
          } finally {
            setBusy(false);
          }
        }}
      >
        {busy ? t("imageGeneratorLoading", locale) : t("imageGeneratorButton", locale)}
      </button>
      {err ? <p className="mt-2 text-sm text-red-400">{err}</p> : null}
    </div>
  );
}
