import type { ReactNode } from "react";

import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { useCartStore } from "../stores/cart-store";
import { CartDrawer } from "./cart-drawer";

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

describe("CartDrawer", () => {
  beforeEach(() => {
    useCartStore.setState({
      items: [],
      isOpen: false
    });
  });

  it("renders the empty checkout state with a disabled CTA", () => {
    useCartStore.getState().openCart();

    render(<CartDrawer />);

    expect(screen.getByRole("heading", { name: "Корзина пока пуста" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Оформить заказ" })).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Очистить корзину" })).not.toBeInTheDocument();
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
    expect(screen.getByRole("button", { name: "Оформить заказ" })).not.toBeDisabled();
    expect(screen.getByRole("button", { name: "Очистить корзину" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Очистить корзину" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Оформить заказ" })).toBeDisabled();
    });
  });
});
