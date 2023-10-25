import './globals.css'
import { Providers } from './providers'

import TopNav from "@/app/components/topNav";
import dynamic from "next/dynamic";

dynamic(() => import('@/prism/prism.css'));

export const metadata = {
  title: 'MystBin',
  description: 'Share code and text.',
}


export default function RootLayout({ children }) {
  return (
      <html suppressHydrationWarning>
        <head />
        <body>
          <Providers><TopNav />{children}</Providers>
        </body>
      </html>
  )
}
