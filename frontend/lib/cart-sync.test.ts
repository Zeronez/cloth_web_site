import {
  addCartItem,
  fetchCart,
  updateCartItemQuantity
} from "./api";
import { mergeGuestCartIntoServer } from "./cart-sync";

jest.mock("./api", () => ({
  ...jest.requireActual("./api"),
  addCartItem: jest.fn(),
  fetchCart: jest.fn(),
  updateCartItemQuantity: jest.fn()
}));

describe("mergeGuestCartIntoServer", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("merges guest quantities into the server cart and skips invalid ids", async () => {
    jest
      .mocked(fetchCart)
      .mockResolvedValueOnce({
        id: 1,
        items: [
          {
            id: 501,
            variant: {
              id: 101,
              sku: "SYNC-TEE-M",
              size: "M",
              color: "Black",
              stock_quantity: 8,
              price_delta: "0.00",
              price: "100.00",
              is_active: true
            },
            product: {
              id: 11,
              name: "Sync Tee",
              slug: "sync-tee",
              base_price: "100.00",
              is_active: true
            },
            quantity: 1,
            unit_price: "100.00",
            line_total: "100.00",
            created_at: "2026-05-13T10:00:00Z",
            updated_at: "2026-05-13T10:00:00Z"
          }
        ],
        total_amount: "100.00",
        subtotal_amount: "100.00",
        total_quantity: 1,
        created_at: "2026-05-13T10:00:00Z",
        updated_at: "2026-05-13T10:00:00Z"
      })
      .mockResolvedValueOnce({
        id: 1,
        items: [
          {
            id: 501,
            variant: {
              id: 101,
              sku: "SYNC-TEE-M",
              size: "M",
              color: "Black",
              stock_quantity: 8,
              price_delta: "0.00",
              price: "100.00",
              is_active: true
            },
            product: {
              id: 11,
              name: "Sync Tee",
              slug: "sync-tee",
              base_price: "100.00",
              is_active: true
            },
            quantity: 4,
            unit_price: "100.00",
            line_total: "400.00",
            created_at: "2026-05-13T10:00:00Z",
            updated_at: "2026-05-13T10:05:00Z"
          },
          {
            id: 601,
            variant: {
              id: 202,
              sku: "EVA-HOODIE-L",
              size: "L",
              color: "Purple",
              stock_quantity: 4,
              price_delta: "0.00",
              price: "150.00",
              is_active: true
            },
            product: {
              id: 12,
              name: "Eva Hoodie",
              slug: "eva-hoodie",
              base_price: "150.00",
              is_active: true
            },
            quantity: 1,
            unit_price: "150.00",
            line_total: "150.00",
            created_at: "2026-05-13T10:05:00Z",
            updated_at: "2026-05-13T10:05:00Z"
          }
        ],
        total_amount: "550.00",
        subtotal_amount: "550.00",
        total_quantity: 5,
        created_at: "2026-05-13T10:00:00Z",
        updated_at: "2026-05-13T10:05:00Z"
      });

    const result = await mergeGuestCartIntoServer("access-token", [
      {
        id: "101",
        name: "Sync Tee",
        price: 100,
        size: "M",
        quantity: 2
      },
      {
        id: "101",
        name: "Sync Tee",
        price: 100,
        size: "M",
        quantity: 1
      },
      {
        id: "202",
        name: "Eva Hoodie",
        price: 150,
        size: "L",
        quantity: 1
      },
      {
        id: "bad-id",
        name: "Demo Drop",
        price: 1,
        size: "L",
        quantity: 1
      }
    ]);

    expect(updateCartItemQuantity).toHaveBeenCalledWith("access-token", 501, 4);
    expect(addCartItem).toHaveBeenCalledWith("access-token", 202, 1);
    expect(result.skippedItems).toEqual([
      expect.objectContaining({
        id: "bad-id",
        quantity: 1
      })
    ]);
    expect(result.items).toEqual([
      expect.objectContaining({
        id: "101",
        serverItemId: 501,
        quantity: 4
      }),
      expect.objectContaining({
        id: "202",
        serverItemId: 601,
        quantity: 1
      })
    ]);
  });
});
