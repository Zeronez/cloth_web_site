export function GET() {
  const payload = {
    ok: true,
    service: "animeattire-frontend",
    timestamp: new Date().toISOString()
  };

  return Response.json(payload, {
    status: 200,
    headers: {
      "Cache-Control": "no-store"
    }
  });
}

