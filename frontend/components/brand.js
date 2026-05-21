"use client";

import React from "react";

export function Brand(props) {
  const { className, alt } = props;
  const cn =
    "object-contain object-left max-w-full " +
    (className || "h-36 w-auto sm:h-40");

  var _s = React.useState("/LOGOTIPO.png");
  var src = _s[0];
  var setSrc = _s[1];
  return React.createElement("img", {
    src: src,
    alt: alt || "Syntexa",
    className: cn,
    decoding: "async",
    loading: "eager",
    draggable: false,
    onError: function () {
      if (src !== "/icon.svg") setSrc("/icon.svg");
    },
  });
}
