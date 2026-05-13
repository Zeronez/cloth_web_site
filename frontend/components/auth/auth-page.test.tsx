import { fireEvent, render, waitFor } from "@testing-library/react";

import { fetchMe, loginUser, registerUser } from "../../lib/api";
import { mergeGuestCartIntoServer } from "../../lib/cart-sync";
import { useCartStore } from "../../stores/cart-store";
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

jest.mock("../../lib/cart-sync", () => ({
  mergeGuestCartIntoServer: jest.fn()
}));

describe("AuthPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
    useCartStore.setState({
      items: [],
      isOpen: false
    });
  });

  it("logs in, merges the guest cart, stores the session, and navigates to account", async () => {
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
    useCartStore.setState({
      isOpen: false,
      items: [
        {
          id: "101",
          name: "Sync Tee",
          price: 100,
          size: "M",
          quantity: 2
        },
        {
          id: "bad-id",
          name: "Demo Drop",
          price: 1,
          size: "L",
          quantity: 1
        }
      ]
    });
    jest.mocked(mergeGuestCartIntoServer).mockResolvedValue({
      items: [
        {
          id: "101",
          serverItemId: 501,
          name: "Sync Tee",
          price: 100,
          size: "M",
          quantity: 3
        }
      ],
      skippedItems: [
        {
          id: "bad-id",
          name: "Demo Drop",
          price: 1,
          size: "L",
          quantity: 1
        }
      ]
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
    expect(mergeGuestCartIntoServer).toHaveBeenCalledWith("access-token", [
      expect.objectContaining({
        id: "101",
        quantity: 2
      }),
      expect.objectContaining({
        id: "bad-id",
        quantity: 1
      })
    ]);
    expect(useUserStore.getState()).toMatchObject({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: expect.objectContaining({ username: "shopper" })
    });
    expect(useCartStore.getState().items).toEqual([
      expect.objectContaining({
        id: "101",
        serverItemId: 501,
        quantity: 3
      })
    ]);
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
      expect(mergeGuestCartIntoServer).not.toHaveBeenCalled();
    });
  });
});
