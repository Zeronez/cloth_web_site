import { fireEvent, render, waitFor } from "@testing-library/react";

import { ApiError, fetchMe, loginUser, registerUser } from "../../lib/api";
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
    const consentCheckboxes = container.querySelectorAll('input[type="checkbox"]');
    fireEvent.click(consentCheckboxes[0]!);
    fireEvent.click(consentCheckboxes[1]!);
    fireEvent.submit(container.querySelector("form")!);

    await waitFor(() => {
      expect(registerUser).not.toHaveBeenCalled();
      expect(loginUser).not.toHaveBeenCalled();
      expect(mergeGuestCartIntoServer).not.toHaveBeenCalled();
    });
  });

  it("sends required consents and optional marketing flag during registration", async () => {
    jest.mocked(registerUser).mockResolvedValue({
      id: 8,
      username: "new-shopper",
      email: "new-shopper@example.com"
    });
    jest.mocked(loginUser).mockResolvedValue({
      access: "register-access-token",
      refresh: "register-refresh-token"
    });
    jest.mocked(fetchMe).mockResolvedValue({
      id: 8,
      username: "new-shopper",
      email: "new-shopper@example.com",
      is_marketing_subscribed: true
    });
    jest.mocked(mergeGuestCartIntoServer).mockResolvedValue({
      items: [],
      skippedItems: []
    });

    const { container } = render(<AuthPage mode="register" />);

    fireEvent.change(container.querySelector('input[name="username"]')!, {
      target: { value: "new-shopper" }
    });
    fireEvent.change(container.querySelector('input[name="email"]')!, {
      target: { value: "new-shopper@example.com" }
    });
    fireEvent.change(container.querySelector('input[name="first_name"]')!, {
      target: { value: "New" }
    });
    fireEvent.change(container.querySelector('input[name="last_name"]')!, {
      target: { value: "Shopper" }
    });
    fireEvent.change(container.querySelector('input[name="phone"]')!, {
      target: { value: "89991234567" }
    });
    fireEvent.change(container.querySelector('input[name="password"]')!, {
      target: { value: "GhibliMerch!2026" }
    });
    fireEvent.change(container.querySelector('input[name="confirmPassword"]')!, {
      target: { value: "GhibliMerch!2026" }
    });

    const consentCheckboxes = container.querySelectorAll('input[type="checkbox"]');
    fireEvent.click(consentCheckboxes[0]!);
    fireEvent.click(consentCheckboxes[1]!);
    fireEvent.click(consentCheckboxes[2]!);
    fireEvent.submit(container.querySelector("form")!);

    await waitFor(() => {
      expect(registerUser).toHaveBeenCalledWith({
        username: "new-shopper",
        email: "new-shopper@example.com",
        password: "GhibliMerch!2026",
        first_name: "New",
        last_name: "Shopper",
        phone: "+79991234567",
        privacy_policy_accepted: true,
        offer_agreement_accepted: true,
        marketing_opt_in: true
      });
    });
  });

  it("formats Russian phone input and hides register eyebrow in form card", () => {
    const { container, queryByText } = render(<AuthPage mode="register" />);

    const phoneInput = container.querySelector('input[name="phone"]') as HTMLInputElement;
    fireEvent.change(phoneInput, {
      target: { value: "9991234567" }
    });

    expect(phoneInput.value).toBe("+7 (999) 123-45-67");
    expect(phoneInput.placeholder).toBe("+7 (___) ___-__-__");
    expect(queryByText("Создание аккаунта")).not.toBeInTheDocument();
  });

  it("deletes previous phone digit when backspacing over mask characters", () => {
    const { container } = render(<AuthPage mode="register" />);

    const phoneInput = container.querySelector('input[name="phone"]') as HTMLInputElement;
    fireEvent.change(phoneInput, {
      target: { value: "332" }
    });

    phoneInput.setSelectionRange(8, 8);
    fireEvent.keyDown(phoneInput, { key: "Backspace" });

    expect(phoneInput.value).toBe("+7 (33");
  });

  it("shows field-level validation for a short password before submit", async () => {
    const { container, findByText } = render(<AuthPage mode="register" />);

    fireEvent.change(container.querySelector('input[name="username"]')!, {
      target: { value: "senko" }
    });
    fireEvent.change(container.querySelector('input[name="email"]')!, {
      target: { value: "senko@example.com" }
    });
    fireEvent.change(container.querySelector('input[name="first_name"]')!, {
      target: { value: "Senko" }
    });
    fireEvent.change(container.querySelector('input[name="last_name"]')!, {
      target: { value: "Fox" }
    });
    fireEvent.change(container.querySelector('input[name="phone"]')!, {
      target: { value: "89991234567" }
    });
    fireEvent.change(container.querySelector('input[name="password"]')!, {
      target: { value: "1234567" }
    });
    fireEvent.change(container.querySelector('input[name="confirmPassword"]')!, {
      target: { value: "1234567" }
    });

    const consentCheckboxes = container.querySelectorAll('input[type="checkbox"]');
    fireEvent.click(consentCheckboxes[0]!);
    fireEvent.click(consentCheckboxes[1]!);
    fireEvent.submit(container.querySelector("form")!);

    expect(registerUser).not.toHaveBeenCalled();
    expect(
      await findByText("Пароль должен содержать минимум 8 символов.")
    ).toBeInTheDocument();
  });

  it("shows duplicate field errors returned by the API", async () => {
    jest.mocked(registerUser).mockRejectedValue(
      new ApiError("Проверьте введенные данные.", 400, {
        error: {
          message: "Проверьте введенные данные.",
          details: {
            username: [{ message: "Этот логин уже используется." }],
            email: [{ message: "Этот email уже используется." }],
            phone: [{ message: "Этот телефон уже используется." }]
          }
        }
      })
    );

    const { container, findByText, queryByText } = render(<AuthPage mode="register" />);

    fireEvent.change(container.querySelector('input[name="username"]')!, {
      target: { value: "senko" }
    });
    fireEvent.change(container.querySelector('input[name="email"]')!, {
      target: { value: "senko@example.com" }
    });
    fireEvent.change(container.querySelector('input[name="first_name"]')!, {
      target: { value: "Senko" }
    });
    fireEvent.change(container.querySelector('input[name="last_name"]')!, {
      target: { value: "Fox" }
    });
    fireEvent.change(container.querySelector('input[name="phone"]')!, {
      target: { value: "89991234567" }
    });
    fireEvent.change(container.querySelector('input[name="password"]')!, {
      target: { value: "12345678" }
    });
    fireEvent.change(container.querySelector('input[name="confirmPassword"]')!, {
      target: { value: "12345678" }
    });

    const consentCheckboxes = container.querySelectorAll('input[type="checkbox"]');
    fireEvent.click(consentCheckboxes[0]!);
    fireEvent.click(consentCheckboxes[1]!);
    fireEvent.submit(container.querySelector("form")!);

    expect(await findByText("Этот логин уже используется.")).toBeInTheDocument();
    expect(await findByText("Этот email уже используется.")).toBeInTheDocument();
    expect(await findByText("Этот телефон уже используется.")).toBeInTheDocument();
    expect(queryByText("Проверьте введенные данные.")).not.toBeInTheDocument();
  });
});
