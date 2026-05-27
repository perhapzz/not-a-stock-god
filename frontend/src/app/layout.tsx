import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '我不是股神',
  description: '穿越回过去，看看你能不能跑赢大盘',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body className="bg-gray-50 text-gray-900 min-h-screen">{children}</body>
    </html>
  )
}
