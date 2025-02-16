import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Blacksmith UI',
  description: 'UI Interface for Blacksmith Python Package',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
