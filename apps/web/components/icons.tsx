/**
 * Larkspur icon set: original inline SVGs on a 24px grid, 1.75px round strokes, `currentColor`.
 *
 * - Decorative by default (`aria-hidden`). Pass `title` to make an icon a labelled image
 *   (only when the icon is the sole content of something meaningful and there's no other label).
 * - Default size is 20px (`size-5`); override with `className="size-4"` / `size-6` etc.
 * - Server-Component safe (no hooks, no client code).
 */
import { cn } from "@/lib/cn";
import type { ReactNode, SVGProps } from "react";

export type IconProps = Omit<SVGProps<SVGSVGElement>, "children"> & {
  className?: string;
  /** Accessible name. Omit for decorative icons (the default). */
  title?: string;
};

export type Icon = ((props: IconProps) => ReactNode) & { displayName?: string };

function createIcon(name: string, content: ReactNode, { solid = false }: { solid?: boolean } = {}): Icon {
  function IconComponent({ className, title, strokeWidth = 1.75, ...rest }: IconProps) {
    return (
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        width={24}
        height={24}
        fill={solid ? "currentColor" : "none"}
        stroke={solid ? "none" : "currentColor"}
        strokeWidth={solid ? undefined : strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        focusable="false"
        aria-hidden={title ? undefined : true}
        role={title ? "img" : undefined}
        className={cn("size-5 shrink-0", className)}
        {...rest}
      >
        {title ? <title>{title}</title> : null}
        {content}
      </svg>
    );
  }
  IconComponent.displayName = name;
  return IconComponent;
}

const dot = (cx: number, cy: number) => <circle cx={cx} cy={cy} r={1.1} fill="currentColor" stroke="none" />;

const STAR_PATH =
  "M12 3.4l2.62 5.3 5.85.86-4.23 4.12 1 5.82L12 16.75 6.76 19.5l1-5.82L3.53 9.56l5.85-.86L12 3.4Z";

/* ---------- Commerce & navigation ---------- */
export const SearchIcon = createIcon(
  "SearchIcon",
  <>
    <circle cx="11" cy="11" r="6.75" />
    <path d="m20 20-4.2-4.2" />
  </>,
);
export const BagIcon = createIcon(
  "BagIcon",
  <>
    <path d="M5.2 8h13.6l-.9 11.1a1.5 1.5 0 0 1-1.5 1.4H7.6a1.5 1.5 0 0 1-1.5-1.4L5.2 8Z" />
    <path d="M9 10.5V7a3 3 0 0 1 6 0v3.5" />
  </>,
);
export const CartIcon = createIcon(
  "CartIcon",
  <>
    <path d="M3 4h2l2.4 11.2a2 2 0 0 0 2 1.6h7.7a2 2 0 0 0 1.95-1.5L20.8 8H6.2" />
    <circle cx="10" cy="20" r="1.25" />
    <circle cx="17" cy="20" r="1.25" />
  </>,
);
export const UserIcon = createIcon(
  "UserIcon",
  <>
    <circle cx="12" cy="8" r="4" />
    <path d="M4.5 20.5a7.5 7.5 0 0 1 15 0" />
  </>,
);
export const ChevronRightIcon = createIcon("ChevronRightIcon", <path d="m9.5 6 6 6-6 6" />);
export const ChevronLeftIcon = createIcon("ChevronLeftIcon", <path d="m14.5 6-6 6 6 6" />);
export const ChevronDownIcon = createIcon("ChevronDownIcon", <path d="m6 9.5 6 6 6-6" />);
export const ChevronUpIcon = createIcon("ChevronUpIcon", <path d="m18 14.5-6-6-6 6" />);
export const ArrowRightIcon = createIcon("ArrowRightIcon", <path d="M4.5 12h15m-6-6 6 6-6 6" />);
export const ArrowLeftIcon = createIcon("ArrowLeftIcon", <path d="M19.5 12h-15m6-6-6 6 6 6" />);
export const ExternalLinkIcon = createIcon(
  "ExternalLinkIcon",
  <>
    <path d="M14 4.5h5.5V10M19.5 4.5 11 13" />
    <path d="M17.5 14v4.5a1.5 1.5 0 0 1-1.5 1.5H6a1.5 1.5 0 0 1-1.5-1.5V8A1.5 1.5 0 0 1 6 6.5h4.5" />
  </>,
);
export const MenuIcon = createIcon("MenuIcon", <path d="M4 7h16M4 12h16M4 17h16" />);
export const CloseIcon = createIcon("CloseIcon", <path d="M6.5 6.5l11 11m0-11-11 11" />);
/** Alias for CloseIcon. */
export const XIcon = CloseIcon;
export const CheckIcon = createIcon("CheckIcon", <path d="m5 12.5 4.5 4.5L19 7.5" />);
export const PlusIcon = createIcon("PlusIcon", <path d="M12 5v14M5 12h14" />);
export const MinusIcon = createIcon("MinusIcon", <path d="M5 12h14" />);
export const SlidersIcon = createIcon(
  "SlidersIcon",
  <>
    <path d="M4 6.5h9m4 0h3M4 12h3m4 0h9M4 17.5h11m4 0h1" />
    <circle cx="15" cy="6.5" r="2" />
    <circle cx="9" cy="12" r="2" />
    <circle cx="17" cy="17.5" r="2" />
  </>,
);
/** Alias for SlidersIcon. */
export const FilterIcon = SlidersIcon;
export const HomeIcon = createIcon(
  "HomeIcon",
  <>
    <path d="M3.5 10.5 12 3.5l8.5 7" />
    <path d="M5.5 9v10.5a1 1 0 0 0 1 1H10v-6h4v6h3.5a1 1 0 0 0 1-1V9" />
  </>,
);
export const GridIcon = createIcon(
  "GridIcon",
  <>
    <rect x="4" y="4" width="6.5" height="6.5" rx="1.5" />
    <rect x="13.5" y="4" width="6.5" height="6.5" rx="1.5" />
    <rect x="4" y="13.5" width="6.5" height="6.5" rx="1.5" />
    <rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.5" />
  </>,
);
export const SitemapIcon = createIcon(
  "SitemapIcon",
  <>
    <rect x="9" y="3" width="6" height="5" rx="1.25" />
    <rect x="3" y="16" width="6" height="5" rx="1.25" />
    <rect x="15" y="16" width="6" height="5" rx="1.25" />
    <path d="M12 8v4M6 16v-2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v2" />
  </>,
);
export const MapIcon = createIcon(
  "MapIcon",
  <>
    <path d="M9 4.5 3.5 6.5v13L9 17.5l6 2 5.5-2v-13L15 6.5l-6-2Z" />
    <path d="M9 4.5v13M15 6.5v13" />
  </>,
);

/* ---------- Ratings & favorites ---------- */
export const StarIcon = createIcon("StarIcon", <path d={STAR_PATH} />);
export const StarFilledIcon = createIcon("StarFilledIcon", <path d={STAR_PATH} />, { solid: true });
export const StarHalfIcon = createIcon(
  "StarHalfIcon",
  <>
    <path d={STAR_PATH} />
    <path d="M12 3.4v13.35L6.76 19.5l1-5.82L3.53 9.56l5.85-.86L12 3.4Z" fill="currentColor" />
  </>,
);
export const HeartIcon = createIcon(
  "HeartIcon",
  <path d="M12 20s-7.3-4.4-8.9-9.1C2 7.5 4.2 4.5 7.4 4.5c2 0 3.5 1.1 4.6 2.8 1.1-1.7 2.6-2.8 4.6-2.8 3.2 0 5.4 3 4.3 6.4C19.3 15.6 12 20 12 20Z" />,
);

/* ---------- Service & trust ---------- */
export const TruckIcon = createIcon(
  "TruckIcon",
  <>
    <path d="M14 16.5V6a1 1 0 0 0-1-1H3.5a1 1 0 0 0-1 1v9.5a1 1 0 0 0 1 1h1.75" />
    <path d="M14 8.5h3.6a1 1 0 0 1 .8.4l2.4 3.2a1 1 0 0 1 .2.6v2.8a1 1 0 0 1-1 1h-1.25" />
    <path d="M9.25 16.5h5.5" />
    <circle cx="7.25" cy="16.75" r="2" />
    <circle cx="16.75" cy="16.75" r="2" />
  </>,
);
export const ReturnIcon = createIcon(
  "ReturnIcon",
  <>
    <path d="M9 14 4 9l5-5" />
    <path d="M4 9h10.5a5.5 5.5 0 0 1 0 11H11" />
  </>,
);
export const RefreshIcon = createIcon(
  "RefreshIcon",
  <>
    <path d="M19.5 11A7.5 7.5 0 0 0 6.1 6.6L4.5 8.5" />
    <path d="M4.5 4.5v4h4" />
    <path d="M4.5 13a7.5 7.5 0 0 0 13.4 4.4l1.6-1.9" />
    <path d="M19.5 19.5v-4h-4" />
  </>,
);
export const ShieldCheckIcon = createIcon(
  "ShieldCheckIcon",
  <>
    <path d="M12 3 5 5.8v5.6c0 4.4 3 8.2 7 9.6 4-1.4 7-5.2 7-9.6V5.8L12 3Z" />
    <path d="m9 12 2.2 2.2 4.3-4.4" />
  </>,
);
export const SparklesIcon = createIcon(
  "SparklesIcon",
  <>
    <path d="M11 4.5l1.55 4.2a2 2 0 0 0 1.2 1.2L18 11.5l-4.25 1.6a2 2 0 0 0-1.2 1.2L11 18.5l-1.55-4.2a2 2 0 0 0-1.2-1.2L4 11.5l4.25-1.6a2 2 0 0 0 1.2-1.2L11 4.5Z" />
    <path d="M18.5 3v3.5M16.75 4.75h3.5M18 17v3M16.5 18.5h3" />
  </>,
);
export const PackageIcon = createIcon(
  "PackageIcon",
  <>
    <path d="M12 3 20 7.5v9L12 21l-8-4.5v-9L12 3Z" />
    <path d="M4.3 7.7 12 12l7.7-4.3M12 12v8.8M8 5.25l8 4.5" />
  </>,
);
export const GiftIcon = createIcon(
  "GiftIcon",
  <>
    <rect x="3.5" y="8" width="17" height="4" rx="1" />
    <path d="M5 12v7.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V12M12 8v12.5" />
    <path d="M12 8S11 3.75 8.4 3.75a2.13 2.13 0 0 0 0 4.25H12Zm0 0s1-4.25 3.6-4.25a2.13 2.13 0 0 1 0 4.25H12Z" />
  </>,
);
export const TagIcon = createIcon(
  "TagIcon",
  <>
    <path d="M3.5 12.1V4.5a1 1 0 0 1 1-1h7.6a1 1 0 0 1 .7.3l7.9 7.9a1 1 0 0 1 0 1.4l-7.6 7.6a1 1 0 0 1-1.4 0l-7.9-7.9a1 1 0 0 1-.3-.7Z" />
    <circle cx="8" cy="8" r="1.5" />
  </>,
);
export const CreditCardIcon = createIcon(
  "CreditCardIcon",
  <>
    <rect x="2.5" y="5" width="19" height="14" rx="2" />
    <path d="M2.5 9.5h19M6 15h4" />
  </>,
);
export const ClockIcon = createIcon(
  "ClockIcon",
  <>
    <circle cx="12" cy="12" r="8.5" />
    <path d="M12 7.5V12l3 2" />
  </>,
);

/* ---------- Assistant ---------- */
export const MicIcon = createIcon(
  "MicIcon",
  <>
    <rect x="9" y="3" width="6" height="11" rx="3" />
    <path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M9 21h6" />
  </>,
);
export const ChatIcon = createIcon(
  "ChatIcon",
  <path d="M20 11.5a8 8 0 0 1-11.6 7.2L4 20l1.3-4.1A8 8 0 1 1 20 11.5Z" />,
);

/* ---------- Editing & account ---------- */
export const TrashIcon = createIcon(
  "TrashIcon",
  <>
    <path d="M4 7h16M10 11v6M14 11v6" />
    <path d="m6 7 .8 12.1a2 2 0 0 0 2 1.9h6.4a2 2 0 0 0 2-1.9L18 7" />
    <path d="M9 7V4.5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1V7" />
  </>,
);
export const PencilIcon = createIcon(
  "PencilIcon",
  <>
    <path d="M16.3 3.7a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4L16.3 3.7Z" />
    <path d="m14.5 5.5 3 3" />
  </>,
);
export const SignOutIcon = createIcon(
  "SignOutIcon",
  <>
    <path d="M9.5 20.5h-4A1.5 1.5 0 0 1 4 19V5a1.5 1.5 0 0 1 1.5-1.5h4" />
    <path d="m15.5 16.5 4.5-4.5-4.5-4.5M20 12H9.5" />
  </>,
);
export const MailIcon = createIcon(
  "MailIcon",
  <>
    <rect x="3" y="5" width="18" height="14" rx="2" />
    <path d="m3.5 7 8.5 6 8.5-6" />
  </>,
);
export const LockIcon = createIcon(
  "LockIcon",
  <>
    <rect x="4.5" y="10.5" width="15" height="10" rx="2" />
    <path d="M8 10.5v-3a4 4 0 0 1 8 0v3" />
  </>,
);
export const EyeIcon = createIcon(
  "EyeIcon",
  <>
    <path d="M2.5 12S6 5 12 5s9.5 7 9.5 7-3.5 7-9.5 7-9.5-7-9.5-7Z" />
    <circle cx="12" cy="12" r="3" />
  </>,
);
export const EyeOffIcon = createIcon(
  "EyeOffIcon",
  <>
    <path d="M10.6 5.1A9.6 9.6 0 0 1 12 5c6 0 9.5 7 9.5 7a16.8 16.8 0 0 1-2.4 3.3M6.6 6.6C3.9 8.4 2.5 12 2.5 12S6 19 12 19a9.3 9.3 0 0 0 5.4-1.6" />
    <path d="M9.9 9.9a3 3 0 0 0 4.2 4.2M3 3l18 18" />
  </>,
);

/* ---------- Status ---------- */
export const InfoIcon = createIcon(
  "InfoIcon",
  <>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 11v5.5" />
    {dot(12, 7.75)}
  </>,
);
export const AlertTriangleIcon = createIcon(
  "AlertTriangleIcon",
  <>
    <path d="M10.3 4.1 2.8 17.2A2 2 0 0 0 4.5 20h15a2 2 0 0 0 1.7-2.8L13.7 4.1a2 2 0 0 0-3.4 0Z" />
    <path d="M12 9.5v4" />
    {dot(12, 16.75)}
  </>,
);
export const AlertCircleIcon = createIcon(
  "AlertCircleIcon",
  <>
    <circle cx="12" cy="12" r="9" />
    <path d="M12 7.5v5.25" />
    {dot(12, 16.25)}
  </>,
);
export const CheckCircleIcon = createIcon(
  "CheckCircleIcon",
  <>
    <circle cx="12" cy="12" r="9" />
    <path d="m8.5 12.2 2.4 2.4 4.6-4.9" />
  </>,
);

/* ---------- Department glyphs ---------- */
export const HeadphonesIcon = createIcon(
  "HeadphonesIcon",
  <>
    <path d="M4 15.5V12a8 8 0 0 1 16 0v3.5" />
    <rect x="3.5" y="14" width="4.5" height="6.5" rx="1.5" />
    <rect x="16" y="14" width="4.5" height="6.5" rx="1.5" />
  </>,
);
export const PotIcon = createIcon(
  "PotIcon",
  <>
    <path d="M4.5 10.5h15v6a3.5 3.5 0 0 1-3.5 3.5H8a3.5 3.5 0 0 1-3.5-3.5v-6Z" />
    <path d="M2.5 12.5h2m15 0h2M3.5 10.5h17" />
    <path d="M10 7.75a2 2 0 0 1 4 0" />
  </>,
);
export const ShirtIcon = createIcon(
  "ShirtIcon",
  <path d="M9 3.5 4 5.5 2.5 10.5 6 11.6v8.9h12v-8.9l3.5-1.1L20 5.5l-5-2a3 3 0 0 1-6 0Z" />,
);
export const MountainIcon = createIcon(
  "MountainIcon",
  <>
    <path d="m2.5 19.5 6.75-11.5 4.25 7 2.25-3.5 5.75 8H2.5Z" />
    <circle cx="17" cy="6" r="1.75" />
  </>,
);
export const DumbbellIcon = createIcon(
  "DumbbellIcon",
  <>
    <rect x="4.5" y="7" width="3" height="10" rx="1" />
    <rect x="16.5" y="7" width="3" height="10" rx="1" />
    <path d="M7.5 12h9M2.5 10v4M21.5 10v4" />
  </>,
);
export const BlocksIcon = createIcon(
  "BlocksIcon",
  <>
    <rect x="3.5" y="12.5" width="8" height="8" rx="1.5" />
    <rect x="12.5" y="12.5" width="8" height="8" rx="1.5" />
    <rect x="8" y="3.5" width="8" height="8" rx="1.5" />
  </>,
);
export const DropletIcon = createIcon(
  "DropletIcon",
  <>
    <path d="M12 3.5s6 6.4 6 11a6 6 0 0 1-12 0c0-4.6 6-11 6-11Z" />
    <path d="M9.5 15a2.5 2.5 0 0 0 2.5 2.5" />
  </>,
);
export const NotebookIcon = createIcon(
  "NotebookIcon",
  <>
    <rect x="5" y="3.5" width="14" height="17" rx="2" />
    <path d="M9 3.5v17M12.5 8H16M12.5 11.5H16" />
  </>,
);
export const BasketIcon = createIcon(
  "BasketIcon",
  <>
    <path d="M3.5 10h17l-1.6 8.3a2 2 0 0 1-2 1.7H7.1a2 2 0 0 1-2-1.7L3.5 10Z" />
    <path d="m8 10 3-6m5 6-3-6M9.5 13.5V16.5M14.5 13.5V16.5" />
  </>,
);

/* Grocery and everyday departments */
export const MilkIcon = createIcon(
  "MilkIcon",
  <>
    <path d="M8.5 3.5h7v3l2 3.5v9.5a1 1 0 0 1-1 1h-9a1 1 0 0 1-1-1V10l2-3.5v-3Z" />
    <path d="M6.5 10h11M9.5 14h5" />
  </>,
);
export const AppleIcon = createIcon(
  "AppleIcon",
  <>
    <path d="M12 7.5c-1.5-1-5.5-1.6-6.8 1.9-1.1 3 .6 7.6 2.6 9.6 1.3 1.3 2.6 1 4.2.3 1.6.7 2.9 1 4.2-.3 2-2 3.7-6.6 2.6-9.6C17.5 5.9 13.5 6.5 12 7.5Z" />
    <path d="M12 7.5c0-2 .8-3.3 2.5-4" />
  </>,
);
export const FishIcon = createIcon(
  "FishIcon",
  <>
    <path d="M3.5 12c2.7-3.8 6.3-5.5 10-5 2.6.4 4.6 2.2 5.5 5-.9 2.8-2.9 4.6-5.5 5-3.7.5-7.3-1.2-10-5Z" />
    <path d="M19 12l2-3v6l-2-3ZM8 11.5v1" />
  </>,
);
export const BreadIcon = createIcon(
  "BreadIcon",
  <>
    <path d="M5 11.5a3.5 3.5 0 0 1 1-6.5h12a3.5 3.5 0 0 1 1 6.5V19a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-7.5Z" />
    <path d="M9.5 9.5l-1 3M13 9.5l-1 3M16.5 9.5l-1 3" />
  </>,
);
export const SnowflakeIcon = createIcon(
  "SnowflakeIcon",
  <path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5 12 7l2.5-2.5M9.5 19.5 12 17l2.5 2.5" />,
);
export const JarIcon = createIcon(
  "JarIcon",
  <>
    <path d="M8 3.5h8v3H8zM7 6.5h10l1 2.5v10a1.5 1.5 0 0 1-1.5 1.5h-9A1.5 1.5 0 0 1 6 19V9l1-2.5Z" />
    <path d="M9 12h6v4H9z" />
  </>,
);
export const SnackIcon = createIcon(
  "SnackIcon",
  <>
    <path d="M6.5 3.5h11l-1 3 1 3-1 3 1 3-1 3 1 2h-11l1-2-1-3 1-3-1-3 1-3-1-3Z" />
    <path d="M10 10.5h4" />
  </>,
);
export const BottleIcon = createIcon(
  "BottleIcon",
  <>
    <path d="M10 3.5h4v3c2 1.2 3 2.8 3 5v8a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1v-8c0-2.2 1-3.8 3-5v-3Z" />
    <path d="M7 13h10M7 17h10" />
  </>,
);
export const SprayIcon = createIcon(
  "SprayIcon",
  <>
    <path d="M9 8h5l1.5 3v8.5a1 1 0 0 1-1 1h-7a1 1 0 0 1-1-1V11L9 8Z" />
    <path d="M10 8V5.5h5l2.5 1.5M18.5 4v.01M20 6.5v.01M18.5 9v.01" />
  </>,
);
export const PillIcon = createIcon(
  "PillIcon",
  <>
    <path d="M10.5 20.5a4.95 4.95 0 0 1-7-7l6-6a4.95 4.95 0 0 1 7 7l-6 6Z" />
    <path d="m7.5 10.5 6 6" />
  </>,
);
export const BabyBottleIcon = createIcon(
  "BabyBottleIcon",
  <>
    <path d="M10.5 2.5h3l.5 3h-4l.5-3ZM9 5.5h6v2.5l1 2v9.5a1 1 0 0 1-1 1H9a1 1 0 0 1-1-1V10l1-2V5.5Z" />
    <path d="M8 12.5h3M8 15.5h3" />
  </>,
);
export const PawIcon = createIcon(
  "PawIcon",
  <>
    <path d="M12 12.5c-2.8 0-5 2.6-5 4.8 0 1.6 1.2 2.2 2.5 2.2 1 0 1.6-.5 2.5-.5s1.5.5 2.5.5c1.3 0 2.5-.6 2.5-2.2 0-2.2-2.2-4.8-5-4.8Z" />
    <circle cx="6" cy="10.5" r="1.6" />
    <circle cx="18" cy="10.5" r="1.6" />
    <circle cx="9.5" cy="6.5" r="1.6" />
    <circle cx="14.5" cy="6.5" r="1.6" />
  </>,
);

const departmentIcons: Record<string, Icon> = {
  "dairy-eggs": MilkIcon,
  produce: AppleIcon,
  "meat-seafood": FishIcon,
  bakery: BreadIcon,
  frozen: SnowflakeIcon,
  pantry: JarIcon,
  snacks: SnackIcon,
  beverages: BottleIcon,
  household: SprayIcon,
  "health-wellness": PillIcon,
  baby: BabyBottleIcon,
  pet: PawIcon,
  electronics: HeadphonesIcon,
  "home-kitchen": PotIcon,
  "clothing-shoes": ShirtIcon,
  outdoor: MountainIcon,
  sports: DumbbellIcon,
  toys: BlocksIcon,
  beauty: DropletIcon,
  office: NotebookIcon,
  "gift-cards": GiftIcon,
  grocery: BasketIcon,
  groceries: BasketIcon,
};

/** Glyph for a category slug (falls back to a grid). Decorative unless `title` is passed. */
export function DepartmentIcon({ slug, ...props }: IconProps & { slug: string }) {
  const Glyph = departmentIcons[slug] ?? GridIcon;
  return <Glyph {...props} />;
}
