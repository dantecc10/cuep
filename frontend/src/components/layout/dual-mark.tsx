import Image from "next/image";

interface DualMarkProps {
  variant?: "light" | "dark";
  size?: "sm" | "md";
  className?: string;
}

const sizes = {
  sm: {
    heartBox: "h-9 w-9",
    fistBox: "-ml-1 h-7 w-7 translate-y-1",
    heart: 24,
    fist: 18,
    heartClass: "h-6 w-6",
    fistClass: "h-4 w-4",
  },
  md: {
    heartBox: "h-12 w-12",
    fistBox: "-ml-1.5 h-9 w-9 translate-y-1.5",
    heart: 32,
    fist: 24,
    heartClass: "h-8 w-8",
    fistClass: "h-6 w-6",
  },
} as const;

export function DualMark({ variant = "light", size = "md", className = "" }: DualMarkProps) {
  const dimensions = sizes[size];
  const heartBorder = variant === "dark" ? "border-yellow" : "border-ink";
  const fistBorder = variant === "dark" ? "border-yellow" : "border-ink";
  const heartShadow = variant === "dark" ? "shadow-[2px_2px_0_#E8B83E]" : "shadow-[2px_2px_0_#171313]";
  const fistShadow = variant === "dark" ? "shadow-[2px_2px_0_#E8B83E]" : "shadow-[2px_2px_0_#E8B83E]";

  return (
    <span
      className={`inline-flex shrink-0 items-end ${className}`}
      role="img"
      aria-label="Corazón y puño levantado, emblemas del CUEP"
    >
      <span
        className={`grid -rotate-3 place-items-center border-[1.5px] bg-primary transition-transform duration-200 hover:rotate-0 ${heartBorder} ${heartShadow} ${dimensions.heartBox}`}
      >
        <Image src="/identity/heart.png" alt="" width={dimensions.heart} height={dimensions.heart} className={`object-contain ${dimensions.heartClass}`} />
      </span>
      <span
        className={`grid rotate-6 place-items-center border-[1.5px] bg-paper transition-transform duration-200 hover:rotate-0 ${fistBorder} ${fistShadow} ${dimensions.fistBox}`}
      >
        <Image src="/identity/fist.svg" alt="" width={dimensions.fist} height={dimensions.fist} className={`object-contain ${dimensions.fistClass}`} unoptimized />
      </span>
    </span>
  );
}
