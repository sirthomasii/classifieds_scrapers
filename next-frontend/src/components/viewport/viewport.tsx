import React, { useState, useEffect, useCallback } from 'react';
import { TextInput, Card, Text, Group, Pagination, Box } from '@mantine/core';
import axios from 'axios';
import qs from 'qs';
import { Publication } from '../types/publication';
import { motion, AnimatePresence } from 'framer-motion';
import { MarketplaceData } from '../../types/marketplace';

interface ViewportProps {
  marketplaceData: MarketplaceData | undefined;
  selectedCategory: string | null;
}

export function Viewport({
  marketplaceData,
  selectedCategory
}: ViewportProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const itemsPerPage = 12;

  const filteredData = marketplaceData?.[selectedCategory ?? ''] ?? [];
  const searchedData = filteredData.filter(item => 
    item.title?.english?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.title?.original?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const totalPages = Math.ceil(searchedData.length / itemsPerPage);
  const displayedItems = searchedData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  return (
    <Box p="md">
      <AnimatePresence mode="wait">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <Group justify="apart" mb="md">
            <Text size="xl" fw={700} color="white">
              {selectedCategory ? `Category: ${selectedCategory}` : 'All Items'}
            </Text>
            <TextInput
              placeholder="Search items..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.currentTarget.value)}
              style={{ width: 300 }}
            />
          </Group>
          
          <Group gap="md" align="stretch" component="div">
            {displayedItems.map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card 
                  shadow="sm" 
                  padding="lg" 
                  style={{ 
                    width: 300,
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                    backdropFilter: 'blur(10px)',
                    color: 'white'
                  }}
                >
                  {item.main_image && (
                    <Card.Section>
                      <img
                        src={item.main_image}
                        alt={item.title?.english || 'Product image'}
                        style={{ width: '100%', height: 200, objectFit: 'cover' }}
                      />
                    </Card.Section>
                  )}
                  <Text fw={500} size="lg" mt="md">
                    {item.title?.english || item.title?.original}
                  </Text>
                  <Text size="sm" color="dimmed" mt="xs">
                    {item.price}
                  </Text>
                  {item.link && (
                    <Text 
                      component="a" 
                      href={item.link} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      color="blue" 
                      size="sm" 
                      mt="xs"
                    >
                      View Details
                    </Text>
                  )}
                </Card>
              </motion.div>
            ))}
          </Group>
          
          {totalPages > 1 && (
            <Group justify="center" mt="xl">
              <Pagination
                total={totalPages}
                value={currentPage}
                onChange={setCurrentPage}
                color="violet"
              />
            </Group>
          )}
        </motion.div>
      </AnimatePresence>
    </Box>
  );
}