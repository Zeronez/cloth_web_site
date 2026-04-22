import { render, screen } from "@testing-library/react";

import { Footer } from "./footer";

describe("Footer", () => {
  it("renders the brand and legal links", () => {
    render(<Footer />);

    expect(screen.getByAltText("AnimeAttire")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Доставка" })).toHaveAttribute(
      "href",
      "/delivery"
    );
    expect(screen.getByRole("link", { name: "Возврат" })).toHaveAttribute(
      "href",
      "/returns"
    );
    expect(screen.getByRole("link", { name: "Оферта" })).toHaveAttribute(
      "href",
      "/offer"
    );
    expect(
      screen.getByRole("link", { name: "Конфиденциальность" })
    ).toHaveAttribute("href", "/privacy");
    expect(screen.getByRole("link", { name: "Контакты" })).toHaveAttribute(
      "href",
      "/contacts"
    );
  });
});
