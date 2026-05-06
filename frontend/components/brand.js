"use client";

import React from "react";

export function Brand(props) {
  const { className, alt } = props;
  const cn =
    "object-contain object-left " +
    (className || "h-36 w-[500px] sm:h-40 sm:w-[620px]");

  return React.createElement("img", {
    src: "/LOGOTIPO.png?v=blue4",
    alt: alt || "Syntexa",
    className: cn,
    decoding: "async",
    loading: "eager",
  });
}
