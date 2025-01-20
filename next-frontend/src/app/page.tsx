"use client";

import React, { useState } from 'react';
import { MainLayout } from '@/components/MainLayout';
import { Viewport } from './viewport/viewport';
import { useQuery } from '@tanstack/react-query';

export default function Home() {
  const [buffer, setBuffer] = useState(1000);
  const { data: marketplaceData } = useQuery({
    queryKey: ['listings', buffer],
    queryFn: async () => {
      const response = await fetch(`/api/listings?limit=${buffer}`);
      const data = await response.json();
      return {
        items: data.items,
        total: data.total,
        currentBuffer: buffer
      };
    }
  });

  const handleLoadMore = (newBuffer: number) => {
    setBuffer(newBuffer);
  };

  return (
    <MainLayout
      initialMarketplace="all"
      initialCategory={null}
    >
      <div></div>
    </MainLayout>
  );
}