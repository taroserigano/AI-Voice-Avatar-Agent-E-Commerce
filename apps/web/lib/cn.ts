import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

// Teach tailwind-merge the custom theme values from app/globals.css so they merge/override
// correctly (e.g. `text-display` is a font size, not a text color; `shadow-glow` is a shadow).
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      text: ["display"],
      shadow: ["glow", "glow-lg"],
      "inset-shadow": ["highlight", "well"],
      ease: ["smooth", "snappy", "spring"],
      animate: ["fade-in", "fade-up", "scale-in", "slide-down", "pop", "shimmer"],
      tracking: ["eyebrow"],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
