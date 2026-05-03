import { fireEvent, render, screen, waitFor } from "@testing-library/react";

import { ApiError, createContactRequest } from "../../lib/api";
import { ContactPage } from "./contact-page";

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
  createContactRequest: jest.fn()
}));

describe("ContactPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("submits the contact form and shows a success message", async () => {
    const deferred = createDeferred<{ status: "new" }>();
    jest.mocked(createContactRequest).mockReturnValueOnce(deferred.promise);

    const { container } = render(<ContactPage />);

    fireEvent.change(container.querySelector('input[name="name"]')!, {
      target: { value: "Анна Покупатель" }
    });
    fireEvent.change(container.querySelector('input[name="email"]')!, {
      target: { value: "anna@example.com" }
    });
    fireEvent.change(container.querySelector('input[name="phone"]')!, {
      target: { value: "+79991234567" }
    });
    fireEvent.change(container.querySelector('select[name="topic"]')!, {
      target: { value: "delivery" }
    });
    fireEvent.change(container.querySelector('input[name="order_number"]')!, {
      target: { value: "AA-1001" }
    });
    fireEvent.change(container.querySelector('textarea[name="message"]')!, {
      target: { value: "Подскажите, когда заказ будет передан в доставку?" }
    });

    fireEvent.click(container.querySelector('button[type="submit"]')!);

    expect(screen.getByRole("button", { name: "Отправляем..." })).toBeDisabled();

    await waitFor(() => {
      expect(createContactRequest).toHaveBeenCalledWith({
        name: "Анна Покупатель",
        email: "anna@example.com",
        phone: "+79991234567",
        topic: "delivery",
        order_number: "AA-1001",
        message: "Подскажите, когда заказ будет передан в доставку?"
      });
    });

    deferred.resolve({ status: "new" });

    expect(await screen.findByRole("status")).toHaveTextContent(
      "Спасибо. Сообщение отправлено, мы ответим по указанным контактам."
    );
    expect(container.querySelector('input[name="name"]')).toHaveValue("");
    expect(container.querySelector('input[name="email"]')).toHaveValue("");
  });

  it("shows an error message when the API rejects the request", async () => {
    jest.mocked(createContactRequest).mockRejectedValueOnce(
      new ApiError("Сервер временно недоступен.", 503, {})
    );

    const { container } = render(<ContactPage />);

    fireEvent.change(container.querySelector('input[name="name"]')!, {
      target: { value: "Анна Покупатель" }
    });
    fireEvent.change(container.querySelector('input[name="email"]')!, {
      target: { value: "anna@example.com" }
    });
    fireEvent.change(container.querySelector('textarea[name="message"]')!, {
      target: { value: "Нужна помощь с возвратом заказа." }
    });

    fireEvent.click(container.querySelector('button[type="submit"]')!);

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Сервер временно недоступен."
    );
  });
});

function createDeferred<T>() {
  let resolve!: (value: T | PromiseLike<T>) => void;
  let reject!: (reason?: unknown) => void;

  const promise = new Promise<T>((promiseResolve, promiseReject) => {
    resolve = promiseResolve;
    reject = promiseReject;
  });

  return { promise, resolve, reject };
}
