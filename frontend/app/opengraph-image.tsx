import { ImageResponse } from "next/og";

export const size = {
  width: 1200,
  height: 630
};

export const contentType = "image/png";

export default function OpenGraphImage() {
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
          fontSize: 64,
          fontWeight: 900,
          letterSpacing: -1
        }}
      >
        AnimeAttire
      </div>
    ),
    size
  );
}

