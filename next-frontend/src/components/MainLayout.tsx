'use client'

import React, { useState, useEffect } from 'react';
import { Container, Flex, Box, Button } from '@mantine/core';
import { IconMenu2 } from '@tabler/icons-react';
import classes from './MainLayout.module.css';
import { Viewport } from './viewport/viewport';
import { Sidebar } from './sidebar/sidebar';

interface MainLayoutProps {
  children: React.ReactNode;
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

export function MainLayout({ children }: MainLayoutProps) {
  const [isSidebarVisible, setIsSidebarVisible] = useState(true);
  const [marketplaceData, setMarketplaceData] = useState<{
    blocket: MarketplaceData;
    gumtree: MarketplaceData;
    kleinanzeigen: MarketplaceData;
  } | null>(null);
  const [selectedMarketplace, setSelectedMarketplace] = useState<string>('blocket');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [blocketRes, gumtreeRes, kleinanzeigenRes] = await Promise.all([
          fetch('/jsons/blocket_ads.json'),
          fetch('/jsons/gumtree_ads.json'),
          fetch('/jsons/kleinanzeigen_ads.json')
        ]);

        const [blocketData, gumtreeData, kleinanzeigenData] = await Promise.all([
          blocketRes.json(),
          gumtreeRes.json(),
          kleinanzeigenRes.json()
        ]);

        setMarketplaceData({
          blocket: blocketData,
          gumtree: gumtreeData,
          kleinanzeigen: kleinanzeigenData
        });
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
  }, []);

  const toggleSidebar = () => {
    setIsSidebarVisible(!isSidebarVisible);
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
            marketplaceData={marketplaceData?.[selectedMarketplace as keyof typeof marketplaceData]}
            selectedCategory={selectedCategory}
          />
        </Box>
      </Flex>
    </Container>
  );
}