/** 7.3833 -> "7°23′". Rounds to the nearest arcminute and carries 60′ into the degree. */
export function formatDegree(degrees: number): string {
  let d = Math.floor(degrees);
  let m = Math.round((degrees - d) * 60);
  if (m === 60) {
    d += 1;
    m = 0;
  }
  return `${d}°${String(m).padStart(2, "0")}′`;
}

