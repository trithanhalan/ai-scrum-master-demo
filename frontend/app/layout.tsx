import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AI Scrum Master',
  description: 'Intelligent Agile Automation Platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50">{children}</body>
    </html>
  )
}