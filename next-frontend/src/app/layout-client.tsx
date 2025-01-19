'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MantineProvider } from '@mantine/core'
import { useState } from 'react'
import '@mantine/core/styles.css'
import './globals.css'
import MatrixBackground from '../components/MatrixBackground'

export default function RootLayoutClient({
  children,
}: {
  children: React.ReactNode
}) {
  const [queryClient] = useState(() => new QueryClient())

  return (
    <body>
      <MatrixBackground />
      <QueryClientProvider client={queryClient}>
        <MantineProvider>
          {children}
        </MantineProvider>
      </QueryClientProvider>
    </body>
  )
} 