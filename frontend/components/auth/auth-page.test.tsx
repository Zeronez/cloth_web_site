import { fireEvent, render, waitFor } from "@testing-library/react";

import { fetchMe, loginUser, registerUser } from "../../lib/api";
import { useUserStore } from "../../stores/user-store";
import { AuthPage } from "./auth-page";

const replace = jest.fn();
const refresh = jest.fn();

jest.mock("next/navigation", () => ({
  useRouter: () => ({
    replace,
    refresh
  })
}));

jest.mock("../../lib/api", () => ({
  ApiError: class ApiError extends Error {
    status: number;
    payload: unknown;

    constructor(message: string, status: number, payload: unknown) {
      super(message);
      this.status = status;
      this.payload = payload;
    }
  },
  fetchMe: jest.fn(),
  loginUser: jest.fn(),
  registerUser: jest.fn()
}));

describe("AuthPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
  });

  it("logs in, stores the session, and navigates to the account page", async () => {
    jest.mocked(loginUser).mockResolvedValue({
      access: "access-token",
      refresh: "refresh-token"
    });
    jest.mocked(fetchMe).mockResolvedValue({
      id: 7,
      username: "shopper",
      email: "shopper@example.com",
      first_name: "QA",
      last_name: "Shopper",
      phone: "+15551234567"
    });

    const { container } = render(<AuthPage mode="login" />);

    fireEvent.change(container.querySelector('input[name="username"]')!, {
      target: { value: "shopper" }
    });
    fireEvent.change(container.querySelector('input[name="password"]')!, {
      target: { value: "GhibliMerch!2026" }
    });
    fireEvent.submit(container.querySelector("form")!);

    await waitFor(() => {
      expect(loginUser).toHaveBeenCalledWith({
        username: "shopper",
        password: "GhibliMerch!2026"
      });
    });
    expect(fetchMe).toHaveBeenCalledWith("access-token");
    expect(useUserStore.getState()).toMatchObject({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: expect.objectContaining({ username: "shopper" })
    });
    expect(replace).toHaveBeenCalledWith("/account");
    expect(refresh).toHaveBeenCalled();
  });

  it("does not call registration API when password confirmation differs", async () => {
    const { container } = render(<AuthPage mode="register" />);

    fireEvent.change(container.querySelector('input[name="username"]')!, {
      target: { value: "new-shopper" }
    });
    fireEvent.change(container.querySelector('input[name="email"]')!, {
      target: { value: "new-shopper@example.com" }
    });
    fireEvent.change(container.querySelector('input[name="password"]')!, {
      target: { value: "GhibliMerch!2026" }
    });
    fireEvent.change(container.querySelector('input[name="confirmPassword"]')!, {
      target: { value: "DifferentPass!2026" }
    });
    fireEvent.submit(container.querySelector("form")!);

    await waitFor(() => {
      expect(registerUser).not.toHaveBeenCalled();
      expect(loginUser).not.toHaveBeenCalled();
    });
  });
});
