import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Cube Lab",
  description: "Interactive Rubik's Cube learning workspace",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
