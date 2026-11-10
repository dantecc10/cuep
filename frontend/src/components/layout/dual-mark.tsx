import Image from "next/image";

interface DualMarkProps {
  variant?: "light" | "dark";
  size?: "sm" | "md";
  className?: string;
}

const sizes = {
  sm: {
    heartBox: "h-9 w-9",
    emblemBox: "-ml-1 h-7 w-7 translate-y-1",
    heart: 24,
    emblem: 18,
    heartClass: "h-6 w-6",
    emblemClass: "h-5 w-5",
  },
  md: {
    heartBox: "h-12 w-12",
    emblemBox: "-ml-1.5 h-9 w-9 translate-y-1.5",
    heart: 32,
    emblem: 24,
    heartClass: "h-8 w-8",
    emblemClass: "h-7 w-7",
  },
} as const;

export function DualMark({ variant = "light", size = "md", className = "" }: DualMarkProps) {
  const dimensions = sizes[size];
  const heartBorder = variant === "dark" ? "border-yellow" : "border-ink";
  const emblemBorder = variant === "dark" ? "border-yellow" : "border-ink";
  const heartShadow = variant === "dark" ? "shadow-[2px_2px_0_#E8B83E]" : "shadow-[2px_2px_0_#171313]";
  const emblemShadow = variant === "dark" ? "shadow-[2px_2px_0_#E8B83E]" : "shadow-[2px_2px_0_#E8B83E]";

  return (
    <span
      className={`inline-flex shrink-0 items-end ${className}`}
      role="img"
      aria-label="Corazón y emblema del CUEP"
    >
      <span
        className={`grid -rotate-3 place-items-center border-[1.5px] bg-primary transition-transform duration-200 hover:rotate-0 ${heartBorder} ${heartShadow} ${dimensions.heartBox}`}
      >
        <Image src="/identity/heart.png" alt="" width={dimensions.heart} height={dimensions.heart} className={`object-contain ${dimensions.heartClass}`} />
      </span>
      <span
        className={`grid rotate-6 place-items-center border-[1.5px] bg-accent transition-transform duration-200 hover:rotate-0 ${emblemBorder} ${emblemShadow} ${dimensions.emblemBox}`}
      >
        <Image src="/identity/cuep-hd-logo.png" alt="" width={dimensions.emblem} height={dimensions.emblem} className={`object-contain ${dimensions.emblemClass}`} />
      </span>
    </span>
  );
}
