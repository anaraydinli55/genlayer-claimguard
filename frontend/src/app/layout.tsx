import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "@rainbow-me/rainbowkit/styles.css"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { WalletProvider } from "@/components/wallet-provider"
import { Navbar } from "@/components/navbar"

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" })

export const metadata: Metadata = {
  title: "ClaimGuard | AI-Powered On-Chain Verification",
  description: "A GenLayer primitive for verifying real-world claims through web evidence and LLM consensus.",
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider attribute="class" defaultTheme="dark" enableSystem>
          <WalletProvider>
            <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-violet-50 dark:from-slate-950 dark:via-slate-900 dark:to-violet-950/20">
              <Navbar />
              <main className="pt-16">{children}</main>
            </div>
          </WalletProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
