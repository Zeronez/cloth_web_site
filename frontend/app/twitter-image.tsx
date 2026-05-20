import { ImageResponse } from "next/og";

export const size = {
  width: 1200,
  height: 600
};

export const contentType = "image/png";

export default function TwitterImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#070A12",
          color: "white",
          fontSize: 56,
          fontWeight: 900,
          letterSpacing: -1,
          textAlign: "center",
          padding: "0 72px"
        }}
      >
        AnimeAttire — аниме‑стритвир
      </div>
    ),
    size
  );
}

