import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ContentForge',
  description: 'Automated AI content generation pipeline dashboard',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
