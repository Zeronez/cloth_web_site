import type { ReactNode } from "react";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ApiError } from "../lib/api";
import {
  fetchServerCartItems,
  removeServerCartVariant,
  updateServerCartVariantQuantity
} from "../lib/cart-sync";
import { useCartStore } from "../stores/cart-store";
import { useUserStore } from "../stores/user-store";
import { CartDrawer } from "./cart-drawer";

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

jest.mock("framer-motion", () => {
  const React = require("react");

  const passthrough = (tag: keyof JSX.IntrinsicElements) =>
    React.forwardRef(function MotionTag({ children, ...props }: any, ref: any) {
      return React.createElement(tag, { ref, ...props }, children);
    });

  return {
    AnimatePresence: ({ children }: { children: ReactNode }) => <>{children}</>,
    motion: {
      aside: passthrough("aside"),
      button: passthrough("button")
    }
  };
});

jest.mock("./product-image-placeholder", () => ({
  ProductImagePlaceholder: () => <div data-testid="product-image-placeholder" />
}));

jest.mock("../lib/cart-sync", () => ({
  ...jest.requireActual("../lib/cart-sync"),
  fetchServerCartItems: jest.fn(),
  removeServerCartVariant: jest.fn(),
  updateServerCartVariantQuantity: jest.fn()
}));

const subtotalText = (value: number) =>
  new Intl.NumberFormat("ru-RU", {
    currency: "RUB",
    style: "currency"
  }).format(value);

const normalizeWhitespace = (value: string) => value.replace(/\s+/g, " ").trim();

const expectCartTotal = (value: number) => {
  expect(
    normalizeWhitespace(screen.getByText("Итого").parentElement?.textContent ?? "")
  ).toContain(normalizeWhitespace(subtotalText(value)));
};

const expectLinePrice = (value: number) => {
  expect(
    screen.getByText((_, element) => {
      if (!element || element.tagName.toLowerCase() !== "p") {
        return false;
      }

      return (
        normalizeWhitespace(element.textContent ?? "") ===
        normalizeWhitespace(subtotalText(value))
      );
    })
  ).toBeInTheDocument();
};

describe("CartDrawer", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useCartStore.setState({
      items: [],
      isOpen: false
    });
    useUserStore.setState({
      accessToken: null,
      refreshToken: null,
      profile: null
    });
  });

  it("renders the empty checkout state with a disabled CTA", () => {
    useCartStore.getState().openCart();

    render(<CartDrawer />);

    expect(
      screen.getByRole("heading", { name: "Корзина пока пуста" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Оформить заказ" })
    ).toBeDisabled();
    expect(
      screen.queryByRole("button", { name: "Очистить корзину" })
    ).not.toBeInTheDocument();
  });

  it("renders items, subtotal, and checkout actions when the drawer has content", async () => {
    useCartStore.setState({
      isOpen: true,
      items: [
        {
          id: "variant-44",
          name: "Neon Ronin Shell",
          price: 14800,
          size: "M",
          quantity: 2
        }
      ]
    });

    render(<CartDrawer />);

    expect(screen.getByText("Neon Ronin Shell")).toBeInTheDocument();
    expect(screen.getByText("Размер M")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Оформить заказ" })
    ).not.toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Очистить корзину" })
    ).toBeInTheDocument();
    expectCartTotal(29600);

    fireEvent.click(screen.getByRole("button", { name: "Очистить корзину" }));

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Оформить заказ" })
      ).toBeDisabled();
    });
  });

  it("increases item quantity and updates totals", async () => {
    useCartStore.setState({
      isOpen: true,
      items: [
        {
          id: "variant-44",
          name: "Neon Ronin Shell",
          price: 14800,
          size: "M",
          quantity: 2
        }
      ]
    });

    render(<CartDrawer />);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Увеличить количество Neon Ronin Shell"
      })
    );

    await waitFor(() => {
      expect(useCartStore.getState().items).toEqual([
        expect.objectContaining({
          id: "variant-44",
          size: "M",
          quantity: 3
        })
      ]);
    });

    expect(screen.getByText("3")).toBeInTheDocument();
    expectLinePrice(44400);
    expectCartTotal(44400);
  });

  it("decreases item quantity and removes the item when it reaches zero", async () => {
    useCartStore.setState({
      isOpen: true,
      items: [
        {
          id: "variant-44",
          name: "Neon Ronin Shell",
          price: 14800,
          size: "M",
          quantity: 2
        }
      ]
    });

    render(<CartDrawer />);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Уменьшить количество Neon Ronin Shell"
      })
    );

    await waitFor(() => {
      expect(useCartStore.getState().items).toEqual([
        expect.objectContaining({
          id: "variant-44",
          size: "M",
          quantity: 1
        })
      ]);
    });

    expect(screen.getByText("1")).toBeInTheDocument();
    expectLinePrice(14800);
    expectCartTotal(14800);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Удалить Neon Ronin Shell из корзины"
      })
    );

    await waitFor(() => {
      expect(useCartStore.getState().items).toEqual([]);
    });

    expect(
      screen.getByRole("heading", { name: "Корзина пока пуста" })
    ).toBeInTheDocument();
  });

  it("loads the server cart for an authenticated user when the drawer opens empty", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: {
        id: 7,
        username: "shopper",
        email: "shopper@example.com"
      }
    });
    useCartStore.setState({
      items: [],
      isOpen: true
    });
    jest.mocked(fetchServerCartItems).mockResolvedValue([
      {
        id: "101",
        serverItemId: 501,
        name: "Sync Tee",
        price: 100,
        size: "M",
        quantity: 2
      }
    ]);

    render(<CartDrawer />);

    await waitFor(() => {
      expect(fetchServerCartItems).toHaveBeenCalledWith("access-token");
    });
    expect(await screen.findByText("Sync Tee")).toBeInTheDocument();
    expect(screen.getByText("Размер M")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("clears the auth session on a 401 from server-backed cart mutations", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: {
        id: 7,
        username: "shopper",
        email: "shopper@example.com"
      }
    });
    useCartStore.setState({
      isOpen: true,
      items: [
        {
          id: "101",
          serverItemId: 501,
          name: "Sync Tee",
          price: 100,
          size: "M",
          quantity: 1
        }
      ]
    });
    jest
      .mocked(removeServerCartVariant)
      .mockRejectedValue(new ApiError("Unauthorized", 401, {}));

    render(<CartDrawer />);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Удалить"
      })
    );

    await waitFor(() => {
      expect(useUserStore.getState().accessToken).toBeNull();
      expect(useUserStore.getState().profile).toBeNull();
    });
  });

  it("updates server-backed item quantity for authenticated users", async () => {
    useUserStore.setState({
      accessToken: "access-token",
      refreshToken: "refresh-token",
      profile: {
        id: 7,
        username: "shopper",
        email: "shopper@example.com"
      }
    });
    useCartStore.setState({
      isOpen: true,
      items: [
        {
          id: "101",
          serverItemId: 501,
          name: "Sync Tee",
          price: 100,
          size: "M",
          quantity: 1
        }
      ]
    });
    jest.mocked(updateServerCartVariantQuantity).mockResolvedValue([
      {
        id: "101",
        serverItemId: 501,
        name: "Sync Tee",
        price: 100,
        size: "M",
        quantity: 2
      }
    ]);

    render(<CartDrawer />);

    fireEvent.click(
      screen.getByRole("button", {
        name: "Увеличить количество Sync Tee"
      })
    );

    await waitFor(() => {
      expect(updateServerCartVariantQuantity).toHaveBeenCalledWith(
        "access-token",
        501,
        2
      );
    });
    expect(await screen.findByText("2")).toBeInTheDocument();
    expectCartTotal(200);
  });
});
