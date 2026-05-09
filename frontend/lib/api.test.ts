import { fetchMe, loginUser, refreshTokens } from "./api";

function jsonResponse(body: unknown, init: ResponseInit = {}) {
  const headers = new Map<string, string>(
    Object.entries({
      "content-type": "application/json",
      ...(init.headers ?? {})
    })
  );

  return {
    ok: (init.status ?? 200) >= 200 && (init.status ?? 200) < 300,
    status: init.status ?? 200,
    headers: {
      get: (name: string) => headers.get(name.toLowerCase()) ?? null
    },
    json: async () => body,
    text: async () => JSON.stringify(body)
  } as Response;
}

describe("API auth transport", () => {
  const fetchMock = jest.fn();

  beforeEach(() => {
    fetchMock.mockReset();
    global.fetch = fetchMock;
  });

  it("sends protected requests with bearer authorization and no browser credentials", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        id: 1,
        username: "shopper",
        email: "shopper@example.com"
      })
    );

    await fetchMe("access-token");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/users/me/",
      expect.objectContaining({
        method: "GET",
        headers: expect.objectContaining({
          Authorization: "Bearer access-token"
        })
      })
    );
    expect(fetchMock.mock.calls[0][1]).not.toHaveProperty("credentials");
  });

  it("does not attach authorization to login requests", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        access: "access-token",
        refresh: "refresh-token"
      })
    );

    await loginUser({
      username: "shopper",
      password: "GhibliMerch!2026"
    });

    const [, options] = fetchMock.mock.calls[0];
    expect(fetchMock.mock.calls[0][0]).toBe(
      "http://localhost:8000/api/v1/auth/token/"
    );
    expect(options.headers).not.toHaveProperty("Authorization");
    expect(options).not.toHaveProperty("credentials");
  });

  it("refreshes tokens through the bearer JSON contract without cookies", async () => {
    fetchMock.mockResolvedValueOnce(
      jsonResponse({
        access: "new-access-token",
        refresh: "new-refresh-token"
      })
    );

    await expect(refreshTokens("refresh-token")).resolves.toEqual({
      access: "new-access-token",
      refresh: "new-refresh-token"
    });

    const [, options] = fetchMock.mock.calls[0];
    expect(fetchMock.mock.calls[0][0]).toBe(
      "http://localhost:8000/api/v1/auth/token/refresh/"
    );
    expect(options).toMatchObject({
      method: "POST",
      body: JSON.stringify({ refresh: "refresh-token" })
    });
    expect(options.headers).not.toHaveProperty("Authorization");
    expect(options).not.toHaveProperty("credentials");
  });
});
