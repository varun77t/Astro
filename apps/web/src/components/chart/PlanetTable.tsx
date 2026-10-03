import { formatDegree } from "@/lib/format";
import type { ChartPlanet, Dignity } from "@/lib/types";

const PILL: Partial<Record<Dignity, string>> = {
  exalted: "bg-green-bg text-green",
  moolatrikona: "bg-blue-bg text-blue",
  own: "bg-blue-bg text-blue",
  debilitated: "bg-pen-bg text-pen",
};

function Dignity({ value }: { value: Dignity | null }) {
  if (!value) return <span className="text-rule-strong">–</span>;
  const pill = PILL[value];
  return pill ? <span className={`pill ${pill}`}>{value}</span> : <span className="text-sm text-muted">{value}</span>;
}

type Props = {
  planets: ChartPlanet[];
  /** Count houses from the Moon instead of the Lagna (when the birth time is uncertain). */
  fromMoon?: boolean;
};

/** One row per graha on the ruling pitch, tabular numerals, no boxes. */
export function PlanetTable({ planets, fromMoon = false }: Props) {
  return (
    <div className="-mx-1 overflow-x-auto px-1">
      <table className="w-full min-w-[21rem] border-collapse text-left text-sm">
        <caption className="sr-only">Planet positions</caption>
        <thead>
          <tr className="h-[var(--line)] border-b border-rule-strong font-mono text-[0.7rem] tracking-[0.06em] text-muted uppercase">
            <th scope="col" className="py-0 pr-3 font-medium">
              Graha
            </th>
            <th scope="col" className="py-0 pr-3 font-medium">
              Sign
            </th>
            <th scope="col" className="py-0 pr-3 text-right font-medium">
              Degree
            </th>
            <th scope="col" className="py-0 pr-3 text-right font-medium">
              <abbr title={fromMoon ? "House counted from the Moon" : "House counted from the Lagna"} className="no-underline">
                {fromMoon ? "From Moon" : "House"}
              </abbr>
            </th>
            <th scope="col" className="hidden py-0 pr-3 font-medium sm:table-cell">
              Nakshatra
            </th>
            <th scope="col" className="py-0 font-medium">
              Status
            </th>
          </tr>
        </thead>
        <tbody>
          {planets.map((p) => {
            const node = p.name === "Rahu" || p.name === "Ketu";
            return (
              <tr key={p.name} data-row className="h-[var(--line)]">
                <th scope="row" className="py-0 pr-3 font-medium text-ink">
                  {p.name}
                  {p.retrograde && !node && (
                    <abbr title="Retrograde" className="ml-1.5 font-mono text-[0.7rem] text-blue no-underline">
                      R
                    </abbr>
                  )}
                  {p.combust && (
                    <abbr title="Combust (close to the Sun)" className="ml-1 font-mono text-[0.7rem] text-amber no-underline">
                      C
                    </abbr>
                  )}
                </th>
                <td className="py-0 pr-3">{p.sign}</td>
                <td className="py-0 pr-3 text-right font-mono text-[0.8rem]">{formatDegree(p.degree_in_sign)}</td>
                <td className="py-0 pr-3 text-right font-mono text-[0.8rem]">{fromMoon ? p.house_from_moon : p.house}</td>
                <td className="hidden py-0 pr-3 sm:table-cell">
                  {p.nakshatra} <span className="font-mono text-[0.75rem] text-muted">p{p.pada}</span>
                </td>
                <td className="py-0">
                  <Dignity value={p.dignity} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
