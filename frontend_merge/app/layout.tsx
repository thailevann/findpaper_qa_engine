import type { Metadata } from 'next'
import { GeistSans } from 'geist/font/sans'
import { GeistMono } from 'geist/font/mono'
import "../styles/globals.css";

export const metadata: Metadata = {
  title: 'FindPaper - AI Research Intelligence',
  description: 'Accelerate your research with AI-powered paper discovery and analysis',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`font-sans ${GeistSans.variable} ${GeistMono.variable} bg-background min-h-screen`}>
        {children}
      </body>
    </html>
  )
}
