import RootLayoutClient from './layout-client'
import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Fleatronics - Find Used Electronics & Music Equipment Across Europe',
  description: 'Search for used electronics, music instruments, and audio equipment across multiple European marketplaces. Find the best deals on second-hand gear.',
  keywords: 'used electronics, second hand, music equipment, audio gear, musical instruments, European marketplaces, used synthesizers, audio equipment, music gear',
  openGraph: {
    title: 'Fleatronics - Used Electronics & Music Equipment Finder',
    description: 'Search across European marketplaces for used electronics and music equipment. Compare prices and find the best deals.',
    type: 'website',
  },
  robots: 'index, follow',
  alternates: {
    canonical: 'https://fleatronics.com'
  },
  other: {
    'google-adsense-account': 'ca-pub-4841275450464973'
  }
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <script 
          async 
          src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-4841275450464973"
          crossOrigin="anonymous"
        />
      </head>
      <RootLayoutClient>
        {children}
      </RootLayoutClient>
    </html>
  )
}
