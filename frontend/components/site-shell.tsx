import { ReactNode } from "react";
import { CartDrawer } from "./cart-drawer";
import { Footer } from "./footer";
import { Header } from "./header";

export function SiteShell({ children }: { children: ReactNode }) {
  return (
    <>
      <Header />
      {children}
      <Footer />
      <CartDrawer />
    </>
  );
}
