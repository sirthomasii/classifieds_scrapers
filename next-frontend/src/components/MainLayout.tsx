'use client'

import React, { useState, useEffect } from 'react';
import { Container, Flex, Box, Button } from '@mantine/core';
import { IconMenu2 } from '@tabler/icons-react';
import classes from './MainLayout.module.css';
import { Viewport } from './viewport/viewport';
import { Sidebar } from './sidebar/sidebar';

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
    blocket: MarketplaceData;
    gumtree: MarketplaceData;
    kleinanzeigen: MarketplaceData;
    ricardo: MarketplaceData;
  } | null>(null);
  const [selectedMarketplace, setSelectedMarketplace] = useState(initialMarketplace);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/listings');
        const data = await response.json();

        const groupedData = data.reduce((acc: any, item: any) => {
          const source = item.source;
          if (!acc[source]) {
            acc[source] = { all: [] };
          }
          acc[source].all.push(item);
          return acc;
        }, {});

        setMarketplaceData(groupedData);
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  const toggleSidebar = () => {
    setIsSidebarVisible(!isSidebarVisible);
  };

  const getCurrentMarketplaceData = (): MarketplaceData | undefined => {
    if (!marketplaceData) return { all: [] };
    
    if (selectedMarketplace === 'all') {
      // Merge all items from all marketplaces
      const mergedData: MarketplaceData = { all: [] };
      
      Object.values(marketplaceData).forEach(marketplace => {
        if (marketplace.all && Array.isArray(marketplace.all)) {
          mergedData.all = [...mergedData.all, ...marketplace.all];
        }
      });
      
      return mergedData;
    }

    // For single marketplace
    const currentMarketplace = marketplaceData[selectedMarketplace as keyof typeof marketplaceData];
    return currentMarketplace ? { all: currentMarketplace.all || [] } : { all: [] };
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