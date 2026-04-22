import { render, screen } from "@testing-library/react";

import { LegalPage } from "./legal-page";

describe("LegalPage", () => {
  it("renders structured legal content", () => {
    render(
      <LegalPage
        eyebrow="Правила"
        title="Тестовая страница"
        intro="Проверяем общий шаблон для юридических страниц."
        updatedAt="Обновлено: 22 апреля 2026"
        sections={[
          {
            title: "Раздел",
            paragraphs: ["Первый абзац."],
            bullets: ["Пункт 1", "Пункт 2"],
            note: "Требует настройки."
          }
        ]}
        sidebarTitle="Контакты"
        sidebarItems={[{ label: "Email", value: "support@example.com" }]}
      />
    );

    expect(screen.getByRole("heading", { name: "Тестовая страница" })).toBeInTheDocument();
    expect(screen.getByText("Первый абзац.")).toBeInTheDocument();
    expect(screen.getByText("Требует настройки.")).toBeInTheDocument();
    expect(screen.getByText("support@example.com")).toBeInTheDocument();
  });
});
