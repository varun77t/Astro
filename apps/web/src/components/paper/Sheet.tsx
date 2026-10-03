import Link from "next/link";

/** Shared horizontal frame: content sits right of the margin rule at every width. */
export const SHEET_X = "mx-auto w-full max-w-6xl pr-4 pl-12 sm:pr-6 sm:pl-24";

type Props = {
  children: React.ReactNode;
  action?: React.ReactNode;
};

/** The ruled answer sheet: header, margin rule, ruling, footer. */
export function Sheet({ children, action }: Props) {
  return (
    <div className="ruled relative flex flex-1 flex-col">
      <span aria-hidden className="pointer-events-none absolute inset-y-0 left-8 w-px bg-pen/30 sm:left-[4.5rem]" />

      <header className="sticky top-0 z-30 border-b border-rule bg-bone/90 backdrop-blur">
        <div className={`${SHEET_X} flex items-center justify-between py-3`}>
          <Link href="/" className="font-semibold tracking-tight text-ink">
            Vedic Astro
          </Link>
          {action}
        </div>
      </header>

      <div className="relative flex flex-1 flex-col">{children}</div>

      <footer className="relative border-t border-rule bg-bone">
        <div className={`${SHEET_X} flex flex-wrap justify-between gap-3 py-8 text-xs text-muted`}>
          <p>Guidance from tradition, not science or professional advice.</p>
          <p>
            Open source (AGPL) · Place data ©{" "}
            <a className="link text-muted" href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">
              OpenStreetMap contributors
            </a>
          </p>
        </div>
      </footer>
    </div>
  );
}
