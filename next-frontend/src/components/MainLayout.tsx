'use client'

import React, { useState, useEffect } from 'react';
import { Container, Flex, Box, Button } from '@mantine/core';
import { IconMenu2 } from '@tabler/icons-react';
import classes from './MainLayout.module.css';
import { Viewport } from './viewport/viewport';
import { Sidebar } from './sidebar/sidebar';
import { Publication } from '@/types/publication';

interface MainLayoutProps {
  children: React.ReactNode;
  initialMarketplace?: string;
  initialCategory?: string | null;
}

interface MarketplaceData {
  [key: string]: Array<{
    title: {
      original: string | null;
      english: string | null;
    };
    description: string | null;
    main_image: string | null;
    link: string | null;
    price: string | null;
    timestamp: string | null;
  }>;
}

export function MainLayout({ children, initialMarketplace = 'all', initialCategory = null }: MainLayoutProps) {
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [marketplaceData, setMarketplaceData] = useState<{
    blocket: { all: Publication[] };
    gumtree: { all: Publication[] };
    kleinanzeigen: { all: Publication[] };
    olx: { all: Publication[] };
    ricardo: { all: Publication[] };
  } | null>(null);
  const [selectedMarketplace, setSelectedMarketplace] = useState(initialMarketplace);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/listings');
        const result = await response.json();

        // Check if we have data in the expected format
        if (!result.data || !Array.isArray(result.data)) {
          console.error('Invalid data format:', result);
          setMarketplaceData(null);
          return;
        }

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

        setMarketplaceData(groupedData);
      } catch (error) {
        console.error('Error fetching data:', error);
        setMarketplaceData(null);
      }
    };

    fetchData();
  }, []);

  const toggleSidebar = () => {
    setIsSidebarVisible(!isSidebarVisible);
  };

  const getCurrentMarketplaceData = (): { all: Publication[] } | undefined => {
    if (!marketplaceData) return undefined;
    
    if (selectedMarketplace === 'all') {
      const allItems = Object.values(marketplaceData)
        .flatMap(marketplace => marketplace.all || []);
      return { all: allItems };
    }

    return marketplaceData[selectedMarketplace as keyof typeof marketplaceData];
  };

  return (
    <Container 
      size="xl" 
      style={{ 
        minHeight: '100vh',
        padding: 0,
        boxShadow: '0 4px 15px 0 rgba(0, 0, 0, 0.8), 0 6px 20px 0 rgba(0, 0, 0, 0.8)',
        backgroundColor: '#2424248c',
      }}
    >
      {children}
      <Button
        className={classes.mobileMenuButton}
        onClick={toggleSidebar}
        variant="subtle"
        style={{
          position: 'absolute',
          left: '-15px',
          top: '10px',
          zIndex: 1000
        }}
      >
        <IconMenu2 size={32} />
      </Button>
      <Flex style={{ minHeight: '100vh' }}>
        <Box 
          style={{
            width: '300px',
            flexShrink: 0,
            borderRight: '1px solid rgba(255, 255, 255, 0.25)',
            borderLeft: '1px solid rgba(255, 255, 255, 0.25)',
          }}
          className={`${classes.sidebar} ${isSidebarVisible ? '' : classes.hidden}`}
        >
          <Sidebar
            marketplaceData={marketplaceData}
            selectedMarketplace={selectedMarketplace}
            selectedCategory={selectedCategory}
            onMarketplaceChange={setSelectedMarketplace}
            onCategoryChange={setSelectedCategory}
          />
        </Box>
        <Box style={{ flex: 1, position: 'relative', backgroundColor: 'rgba(0, 0, 0, 0.75)', borderRight: '1px solid rgba(255, 255, 255, 0.25)' }}>
          <Viewport 
            marketplaceData={getCurrentMarketplaceData()}
            selectedCategory={selectedCategory}
            selectedMarketplace={selectedMarketplace}
          />
        </Box>
      </Flex>
    </Container>
  );
}