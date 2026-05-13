import { useCartStore } from "./cart-store";

describe("useCartStore persistence and merge behavior", () => {
  beforeEach(() => {
    localStorage.clear();
    useCartStore.setState({
      items: [],
      isOpen: false
    });
  });

  it("persists guest cart items in localStorage", () => {
    useCartStore.getState().addItem({
      id: "101",
      name: "Sync Tee",
      price: 100,
      size: "M"
    });

    expect(useCartStore.getState().items).toEqual([
      expect.objectContaining({
        id: "101",
        quantity: 1
      })
    ]);

    const persisted = JSON.parse(localStorage.getItem("animeattire-cart") ?? "{}");

    expect(persisted.state.items).toEqual([
      expect.objectContaining({
        id: "101",
        name: "Sync Tee",
        quantity: 1
      })
    ]);
  });

  it("replaces guest items with merged server cart items", () => {
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

    useCartStore.getState().setItems([
      {
        id: "101",
        serverItemId: 501,
        name: "Sync Tee",
        price: 100,
        size: "M",
        quantity: 3
      }
    ]);

    expect(useCartStore.getState().items).toEqual([
      expect.objectContaining({
        id: "101",
        serverItemId: 501,
        quantity: 3
      })
    ]);

    const persisted = JSON.parse(localStorage.getItem("animeattire-cart") ?? "{}");

    expect(persisted.state.items).toEqual([
      expect.objectContaining({
        id: "101",
        serverItemId: 501,
        quantity: 3
      })
    ]);
  });
});
