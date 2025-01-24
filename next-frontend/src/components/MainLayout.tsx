'use client'

import React, { useState, useEffect, useRef } from 'react';
import { Container, Box } from '@mantine/core';
import classes from './MainLayout.module.css';
import { Viewport } from '@/app/viewport/viewport';
import { Publication } from '@/types/publication';

interface MainLayoutProps {
  children: React.ReactNode;
  initialMarketplace?: string;
  initialCategory?: string | null;
}

interface MarketplaceData {
  [key: string]: Array<{
    title: {
      english: string | null;
    };
    main_image: string | null;
    link: string | null;
    price: {
      eur: string | null;
    };
    timestamp: string | null;
    source: string | null;
  }>;
}

export function MainLayout({
  children,
  initialMarketplace = 'all',
  initialCategory = null,
}: MainLayoutProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [marketplaceData, setMarketplaceData] = useState<{
    blocket: { all: Publication[] };
    gumtree: { all: Publication[] };
    kleinanzeigen: { all: Publication[] };
    olx: { all: Publication[] };
    ricardo: { all: Publication[] };
  } | null>(null);
  const [selectedMarketplace, setSelectedMarketplace] = useState(initialMarketplace);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Cleanup function for ResizeObserver
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // Disconnect any existing ResizeObserver when component unmounts
    return () => {
      const observers = (window as any).__resizeObservers__;
      if (observers) {
        observers.forEach((observer: any) => {
          if (observer.activeTargets.includes(container) || 
              observer.activeTargets.includes(container.parentElement)) {
            observer.unobserve(container);
            observer.unobserve(container.parentElement);
          }
        });
      }
    };
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(
          `/api/listings?page=${currentPage}&limit=50${selectedMarketplace !== 'all' ? `&source=${selectedMarketplace}` : ''}${searchQuery ? `&search=${encodeURIComponent(searchQuery)}` : ''}`
        );
        const result = await response.json();

        // Check if we have data in the expected format
        if (!result.data || !Array.isArray(result.data)) {
          console.error('Invalid data format:', result);
          setMarketplaceData(null);
          return;
        }

        setTotalItems(result.total);

        // Group data by source
        const groupedData = result.data.reduce((acc: Record<string, { all: Array<Publication> }>, item: Publication) => {
          const source = item.source?.toLowerCase() || 'unknown';
          if (!acc[source]) {
            acc[source] = { all: [] };
          }
          acc[source].all.push(item);
          return acc;
        }, {
          blocket: { all: [] },
          gumtree: { all: [] },
          kleinanzeigen: { all: [] },
          olx: { all: [] },
          ricardo: { all: [] }
        });

        // If it's the first page, replace data, otherwise append
        setMarketplaceData(prev => {
          if (!prev || currentPage === 1) return groupedData;
          
          // Merge new data with existing data
          const merged = { ...prev };
          Object.keys(groupedData).forEach(source => {
            if (!merged[source as keyof typeof merged]) merged[source as keyof typeof merged] = { all: [] };
            merged[source as keyof typeof merged].all = [...merged[source as keyof typeof merged].all, ...groupedData[source].all];
          });
          return merged;
        });
      } catch (error) {
        console.error('Error fetching data:', error);
        setMarketplaceData(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, [currentPage, selectedMarketplace, searchQuery]);

  const handleLoadMore = () => {
    setCurrentPage(prev => prev + 1);
  };

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setCurrentPage(1); // Reset to first page when searching
  };

  const getCurrentMarketplaceData = () => {
    if (!marketplaceData) return undefined;
    
    if (selectedMarketplace === 'all') {
      const allItems = Object.values(marketplaceData)
        .flatMap(marketplace => marketplace.all || []);
      return { 
        items: allItems,
        total: totalItems,
        currentBuffer: allItems.length,
        isLoading
      };
    }

    const items = marketplaceData[selectedMarketplace as keyof typeof marketplaceData]?.all || [];
    return {
      items,
      total: totalItems,
      currentBuffer: items.length,
      isLoading
    };
  };

  return (
    <Container 
      ref={containerRef}
      size="xl" 
      style={{ 
        minHeight: '100vh',
        padding: 0,
        boxShadow: '0 4px 15px 0 rgba(0, 0, 0, 0.8), 0 6px 20px 0 rgba(0, 0, 0, 0.8)',
        backgroundColor: '#2424248c',
        contain: 'paint layout',  // Add containment for better performance
      }}
    >
      {children}
      <Box style={{ 
        minHeight: '100vh',
        backgroundColor: 'rgba(0, 0, 0, 0.75)', 
        width: '100%',
        contain: 'paint layout',  // Add containment for better performance
      }}>
        <Viewport 
          marketplaceData={getCurrentMarketplaceData()}
          selectedCategory={selectedCategory}
          selectedMarketplace={selectedMarketplace}
          onMarketplaceChange={setSelectedMarketplace}
          onLoadMore={handleLoadMore}
          onSearch={handleSearch}
        />
      </Box>
    </Container>
  );
}