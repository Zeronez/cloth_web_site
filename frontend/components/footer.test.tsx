import { render, screen } from "@testing-library/react";

import { Footer } from "./footer";

describe("Footer", () => {
  it("renders the brand and commerce links", () => {
    render(<Footer />);

    expect(screen.getByAltText("AnimeAttire")).toBeInTheDocument();
    expect(screen.getByText("Доставка")).toBeInTheDocument();
    expect(screen.getByText("Возврат")).toBeInTheDocument();
  });
});
