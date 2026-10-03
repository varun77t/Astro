import { describe, expect, it } from "vitest";
import { formatDegree } from "./format";

describe("formatDegree", () => {
  it.each([
    [7.3833, "7°23′"],
    [29.68, "29°41′"],
    [0, "0°00′"],
    [11.9999, "12°00′"],
  ])("%d -> %s", (deg, text) => {
    expect(formatDegree(deg)).toBe(text);
  });
});
