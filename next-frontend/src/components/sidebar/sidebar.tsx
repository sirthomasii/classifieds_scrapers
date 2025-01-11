import React, { useState, useEffect } from 'react';
import { Box, Text, Stack, Accordion } from '@mantine/core';
import axios from 'axios';
import qs from 'qs';
import { MarketplaceData } from '../../types/marketplace';

interface SidebarProps {
  marketplaceData: {
    blocket: MarketplaceData;
    gumtree: MarketplaceData;
    kleinanzeigen: MarketplaceData;
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
        <Accordion variant="filled">
          {['blocket', 'gumtree', 'kleinanzeigen'].map((marketplace) => (
            <Accordion.Item key={marketplace} value={marketplace}>
              <Accordion.Control 
                onClick={() => onMarketplaceChange(marketplace)}
                style={{ 
                  backgroundColor: selectedMarketplace === marketplace ? '#4a4a4a' : 'transparent',
                  color: 'white'
                }}
              >
                {marketplace.charAt(0).toUpperCase() + marketplace.slice(1)}
              </Accordion.Control>
              <Accordion.Panel>
                {marketplaceData?.[marketplace as keyof typeof marketplaceData] && 
                  Object.keys(marketplaceData[marketplace as keyof typeof marketplaceData]).map((category) => (
                    <Text
                      key={category}
                      onClick={() => onCategoryChange(category)}
                      style={{
                        cursor: 'pointer',
                        padding: '8px',
                        backgroundColor: selectedCategory === category ? '#3a3a3a' : 'transparent',
                        color: 'white'
                      }}
                    >
                      {category}
                    </Text>
                  ))
                }
              </Accordion.Panel>
            </Accordion.Item>
          ))}
        </Accordion>
      </Stack>
    </Box>
  );
}