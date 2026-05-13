import type { ReactNode } from "react";

import { fireEvent, render, screen } from "@testing-library/react";

import { useCartStore } from "../stores/cart-store";
import { useUserStore } from "../stores/user-store";
import { Header } from "./header";

jest.mock("next/link", () => {
  return function MockLink({
    children,
    href,
    ...props
  }: {
    children: ReactNode;
    href: string;
  }) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

jest.mock("next/image", () => {
  return function MockImage(props: Record<string, unknown>) {
    const { priority: _priority, ...rest } = props;
    // eslint-disable-next-line @next/next/no-img-element
    return <img {...rest} alt={String(rest.alt ?? "")} />;
  };
});

describe("Header", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    useCartStore.setState({
      items: [],
      isOpen: false,
    });
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null,
    });
  });

  it("renders Russian navigation and guest account/cart controls", () => {
    render(<Header />);

    expect(
      screen.getByRole("navigation", { name: "Основная навигация" })
    ).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Каталог" })).toHaveAttribute(
      "href",
      "/catalog"
    );
    expect(screen.getByRole("link", { name: "Лукбук" })).toHaveAttribute(
      "href",
      "/#lookbook"
    );
    expect(screen.getByRole("link", { name: "Крой" })).toHaveAttribute(
      "href",
      "/#craft"
    );
    expect(screen.getByRole("link", { name: "Войти" })).toHaveAttribute(
      "href",
      "/login"
    );
    expect(
      screen.getByRole("button", { name: "Открыть корзину, товаров: 0" })
    ).toBeInTheDocument();
    expect(screen.queryByText("2")).not.toBeInTheDocument();
  });

  it("renders authenticated account link, cart badge, and opens cart on click", () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: {
        id: 7,
        username: "akira",
        email: "akira@example.com",
        first_name: "Акира",
        last_name: "Танака",
      },
    });
    useCartStore.setState({
      items: [
        {
          id: "101",
          name: "Neo Tokyo Hoodie",
          price: 8900,
          size: "L",
          quantity: 2,
        },
      ],
      isOpen: false,
    });

    render(<Header />);

    expect(screen.getByRole("link", { name: "Открыть аккаунт" })).toHaveAttribute(
      "href",
      "/account"
    );
    const cartButton = screen.getByRole("button", {
      name: "Открыть корзину, товаров: 2",
    });
    expect(cartButton).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();

    fireEvent.click(cartButton);

    expect(useCartStore.getState().isOpen).toBe(true);
  });
});
