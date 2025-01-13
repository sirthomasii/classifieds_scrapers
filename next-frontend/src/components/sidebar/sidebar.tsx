import React from 'react';
import { Box, Text, Stack, Accordion } from '@mantine/core';
import { MarketplaceData } from '../../types/marketplace';

interface SidebarProps {
  marketplaceData: {
    blocket: MarketplaceData;
    gumtree: MarketplaceData;
    kleinanzeigen: MarketplaceData;
    olx: MarketplaceData;
    ricardo: MarketplaceData;
  } | null;
  selectedMarketplace: string;
  selectedCategory: string | null;
  onMarketplaceChange: (marketplace: string) => void;
  onCategoryChange: (category: string | null) => void;
}

export function Sidebar({
  marketplaceData,
  selectedMarketplace,
  selectedCategory,
  onMarketplaceChange,
  onCategoryChange
}: SidebarProps) {
  return (
    <Box p="md">
      <Stack gap="md">
        <Text size="xl" fw={700} color="white">Marketplaces</Text>
        <Accordion 
          variant="filled"
          styles={{
            item: {
              backgroundColor: '#1A1B1E',
              borderColor: 'rgba(255, 255, 255, 0.1)',
            },
            control: {
              backgroundColor: '#1A1B1E',
              '&:hover': {
                backgroundColor: '#2C2E33'
              }
            },
            panel: {
              backgroundColor: '#1A1B1E'
            },
            chevron: {
              color: 'white'
            }
          }}
        >
          <Accordion.Item value="all">
            <Accordion.Control 
              onClick={() => {
                onMarketplaceChange('all');
                onCategoryChange(null);
              }}
              style={{ 
                backgroundColor: selectedMarketplace === 'all' ? '#4a4a4a' : 'transparent',
                color: 'white'
              }}
            >
              All Websites
            </Accordion.Control>
            <Accordion.Panel>
              {['blocket', 'gumtree', 'olx','kleinanzeigen', 'ricardo'].map((marketplace) => (
                <Text
                  key={marketplace}
                  onClick={() => {
                    onMarketplaceChange(marketplace);
                    onCategoryChange(null);
                  }}
                  style={{
                    cursor: 'pointer',
                    padding: '8px',
                    backgroundColor: selectedMarketplace === marketplace ? '#3a3a3a' : 'transparent',
                    color: 'white'
                  }}
                >
                  {marketplace.charAt(0).toUpperCase() + marketplace.slice(1)}
                </Text>
              ))}
            </Accordion.Panel>
          </Accordion.Item>
        </Accordion>
      </Stack>
    </Box>
  );
}