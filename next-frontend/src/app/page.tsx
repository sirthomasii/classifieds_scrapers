"use client";

import React, { useState } from 'react';
import { MainLayout } from '@/components/MainLayout';

export default function Home() {
  const [selectedMarketplace, setSelectedMarketplace] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState(null);

  return (
    <MainLayout
      initialMarketplace={selectedMarketplace}
      initialCategory={selectedCategory}
    >
      {<></>}
    </MainLayout>
  );
}