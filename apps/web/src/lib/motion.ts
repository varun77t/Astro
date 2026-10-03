"use client";

import { useGSAP } from "@gsap/react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(useGSAP, ScrollTrigger);

/** Exponential ease-out: fast start, long settle, like ink meeting paper. */
export const EASE_OUT = "expo.out";

/** Every animation is registered under this query, so reduced motion gets a static page. */
export const MOTION_OK = "(prefers-reduced-motion: no-preference)";

/** Reveal a line as if written left to right. */
export const WRITE_FROM = { clipPath: "inset(0 100% 0 0)" };
export const WRITE_TO = { clipPath: "inset(0 0% 0 0)" };

export { gsap, ScrollTrigger, useGSAP };
