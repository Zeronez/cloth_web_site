type ProductImagePlaceholderProps = {
  label?: string;
  variant?: "jacket" | "hoodie" | "pants" | "cart";
  className?: string;
};

const variantAccent = {
  jacket: "from-neon-crimson/30 via-white/5 to-neon-teal/25",
  hoodie: "from-neon-teal/25 via-white/5 to-neon-amber/25",
  pants: "from-neon-amber/25 via-white/5 to-neon-crimson/25",
  cart: "from-neon-crimson/20 via-white/5 to-neon-teal/20"
};

export function ProductImagePlaceholder({
  label = "AnimeAttire",
  variant = "jacket",
  className = ""
}: ProductImagePlaceholderProps) {
  const isPants = variant === "pants";
  const isCart = variant === "cart";

  return (
    <div
      className={`relative isolate overflow-hidden bg-ink-900 ${className}`}
      role="img"
      aria-label={`Плейсхолдер изображения товара ${label}`}
    >
      <div
        className={`absolute inset-0 bg-gradient-to-br ${variantAccent[variant]}`}
      />
      <div className="absolute inset-0 opacity-[0.22] [background-image:linear-gradient(rgba(255,255,255,0.2)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.14)_1px,transparent_1px)] [background-size:28px_28px]" />
      <div className="absolute left-4 top-4 z-10 border border-white/15 bg-ink-950/80 px-3 py-2 text-xs font-black uppercase text-white">
        {label}
      </div>

      {isCart ? (
        <div className="absolute inset-3 grid place-items-center border border-white/10 bg-black/15">
          <span className="text-lg font-black text-white">AA</span>
        </div>
      ) : isPants ? (
        <>
          <div className="absolute bottom-[10%] left-[28%] h-[72%] w-[18%] -skew-x-6 bg-[linear-gradient(180deg,#1f2937,#070910)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.14)]" />
          <div className="absolute bottom-[10%] right-[28%] h-[72%] w-[18%] skew-x-6 bg-[linear-gradient(180deg,#1f2937,#070910)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.14)]" />
          <div className="absolute left-[29%] right-[29%] top-[20%] h-8 border border-neon-teal/50 bg-neon-teal/10 shadow-neon-teal" />
          <div className="absolute left-[36%] top-[38%] h-[40%] w-1 bg-neon-crimson shadow-neon-crimson" />
        </>
      ) : (
        <>
          <div className="absolute bottom-[9%] left-1/2 h-[72%] w-[52%] -translate-x-1/2 bg-[linear-gradient(150deg,#1f2937,#070910_58%,#111827)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.16),0_22px_70px_rgba(0,0,0,0.42)]" />
          <div className="absolute bottom-[12%] left-[13%] h-[52%] w-[22%] -skew-y-6 bg-[linear-gradient(155deg,#111827,#0b1020)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]" />
          <div className="absolute bottom-[12%] right-[13%] h-[52%] w-[22%] skew-y-6 bg-[linear-gradient(205deg,#111827,#0b1020)] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.1)]" />
          <div className="absolute left-1/2 top-[28%] h-[54%] w-1 -translate-x-1/2 bg-neon-crimson shadow-neon-crimson" />
          <div className="absolute left-[29%] top-[45%] h-1 w-[42%] bg-neon-teal shadow-neon-teal" />
          <div className="absolute left-[34%] top-[55%] h-14 w-[32%] border border-neon-crimson/70 bg-neon-crimson/10" />
          {variant === "hoodie" ? (
            <div className="absolute left-1/2 top-[16%] h-[24%] w-[32%] -translate-x-1/2 rounded-t-full border border-white/15 bg-white/10" />
          ) : null}
        </>
      )}

      <div className="absolute bottom-4 right-4 z-10 border border-white/15 bg-white/10 px-3 py-2 text-xs font-bold text-white">
        Скоро фото
      </div>
    </div>
  );
}
