import React, { useState, useEffect } from 'react';
import { TextInput, Card, Text, Group, Pagination, Box, Skeleton, Select, Autocomplete } from '@mantine/core';
import axios from 'axios';
import qs from 'qs';
import { Publication } from '@/types/publication';
import { motion, AnimatePresence } from 'framer-motion';
import { MarketplaceData } from '@/types/marketplace';
import styles from './viewport.module.css';
import Image from 'next/image';
import { IconSearch } from '@tabler/icons-react';

interface ViewportProps {
  marketplaceData: { all: Publication[] } | undefined;
  selectedCategory: string | null;
  selectedMarketplace: string;
  onMarketplaceChange: (marketplace: string) => void;
}

export function Viewport({
  marketplaceData,
  selectedCategory,
  selectedMarketplace,
  onMarketplaceChange
}: ViewportProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const itemsPerPage = 12;

  console.log('Raw marketplaceData:', marketplaceData); // Debug log

  const filteredData = marketplaceData?.all ?? [];

  console.log('Filtered data before search:', filteredData); // Debug log

  const searchedData = searchQuery 
    ? filteredData.filter(item => {
        const englishTitle = item.title?.english?.toLowerCase() || '';
        const originalTitle = item.title?.original?.toLowerCase() || '';
        const searchTerm = searchQuery.toLowerCase();
        return englishTitle.includes(searchTerm) || originalTitle.includes(searchTerm);
      })
    : filteredData;

  // Reset to page 1 when search query, category, or marketplace changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery, selectedCategory, selectedMarketplace]);

  const totalPages = Math.ceil(searchedData.length / itemsPerPage);
  
  // Ensure current page is valid
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(1);
    }
  }, [totalPages, currentPage]);

  const displayedItems = searchedData.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  console.log('Displayed items:', displayedItems.map(item => ({
    title: item.title,
    link: item.link,
    image: item.main_image
  })));

  const isLoading = !marketplaceData;

  // Generate search suggestions from titles
  useEffect(() => {
    if (searchQuery.length > 2) {
      const allTitles = (marketplaceData?.all || []).map(item => 
        item.title?.english || item.title?.original || ''
      );
      const suggestions = allTitles
        .filter(title => 
          title.toLowerCase().includes(searchQuery.toLowerCase())
        )
        .slice(0, 5);
      setSearchSuggestions(suggestions);
    } else {
      setSearchSuggestions([]);
    }
  }, [searchQuery, marketplaceData]);

  return (
    <Box p="md" style={{ maxHeight: '100vh', overflowY: 'auto' }}>
      <div style={{ 
        padding: '16px',
        display: 'flex',
        gap: '16px',
        alignItems: 'center',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div className={styles.logoText}>Fleatronics</div>
        <Select
          value={selectedMarketplace}
          onChange={(value) => onMarketplaceChange(value || 'all')}
          data={[
            { value: 'all', label: 'All Marketplaces' },
            { value: 'blocket', label: 'Blocket' },
            { value: 'gumtree', label: 'Gumtree' },
            { value: 'kleinanzeigen', label: 'Kleinanzeigen' },
            { value: 'olx', label: 'OLX' },
            { value: 'ricardo', label: 'Ricardo' },
          ]}
          style={{ width: '200px' }}
          styles={{
            input: {
              backgroundColor: '#2C2E33',
              color: 'white',
            },
            dropdown: {
              backgroundColor: '#2C2E33',
              color: 'white',
            },
            item: {
              '&[data-selected]': {
                backgroundColor: '#1C1E23',
              },
              '&[data-hovered]': {
                backgroundColor: '#1C1E23',
              },
            },
          }}
        />
        <Autocomplete
          value={searchQuery}
          onChange={setSearchQuery}
          data={searchSuggestions}
          placeholder="Search listings..."
          leftSection={<IconSearch size={16} />}
          styles={{
            input: {
              backgroundColor: '#2C2E33',
              color: 'white',
              borderRadius: '20px',
              '&::placeholder': {
                color: 'rgba(255, 255, 255, 0.5)',
              },
            },
            dropdown: {
              backgroundColor: '#2C2E33',
              color: 'white',
              borderRadius: '12px',
              marginTop: '8px'
            },
          }}
        />
      </div>

      <div className={styles.gridContainer}>
        {isLoading ? (
          // Show 12 skeleton cards while loading
          Array(12).fill(0).map((_, index) => (
            <div key={index} className={styles.itemCard}>
              <div className={`${styles.imageContainer} ${styles.shimmerLoading}`}>
                <Skeleton height="100%" radius="sm" className={styles.skeleton} />
              </div>
              <div className={styles.itemContent}>
                <Skeleton height={20} width="80%" mb={8} className={styles.skeleton} />
                <Skeleton height={16} width="40%" mb={8} className={styles.skeleton} />
                <Skeleton height={14} width="60%" mb={4} className={styles.skeleton} />
                <Skeleton height={12} width="30%" className={styles.skeleton} />
              </div>
            </div>
          ))
        ) : (
          displayedItems.map((item, index) => (
            <div 
              key={`${item.link}-${index}`}
              className={styles.itemCard}
              onClick={() => item.link && window.open(item.link, '_blank')}
            >
              <div className={styles.imageContainer}>
                {item.main_image && (
                  <Image
                    src={item.main_image || ''}
                    alt={item.title?.english || item.title?.original || 'Product image'}
                    width={250}
                    height={180}
                    className={styles.imageLoading}
                    onLoadingComplete={() => {
                      const img = document.querySelector(`[src="${item.main_image}"]`);
                      img?.classList.remove(styles.imageLoading);
                    }}
                    style={{ 
                      objectFit: 'cover',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                      width: '100%',
                      height: '100%'
                    }}
                  />
                )}
              </div>
              <div className={styles.itemContent}>
                <div style={{ 
                  fontSize: '16px', 
                  fontWeight: 'bold',
                  marginBottom: '8px',
                  color: 'white'
                }}>
                  {item.title?.english || item.title?.original || 'No title'}
                </div>
                <div style={{ 
                  fontSize: '14px',
                  color: '#4CAF50',
                  marginBottom: '8px'
                }}>
                  {typeof item.price?.eur === 'number' ? `${item.price.eur} €` : 'Price not available'}
                </div>
                <div style={{ 
                  fontSize: '12px',
                  color: '#aaa',
                  marginBottom: '4px'
                }}>
                  {item.timestamp ? new Date(item.timestamp).toLocaleString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  }) : 'No date'}
                </div>
                <div style={{
                  fontSize: '11px',
                  color: '#666',
                  fontStyle: 'italic'
                }}>
                  {item.timestamp ? new Date(item.timestamp).toLocaleString('en-GB', {
                    day: 'numeric',
                    month: 'short',
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  }) : 'No date'}
                </div>
              </div>
            </div>
          ))
        )}
      </div>

      {totalPages > 1 && (
        <div className={styles.paginationContainer}>
          <div className={styles.paginationWrapper}>
            {[...Array(totalPages)].map((_, i) => {
              // Show current page, 2 before and 2 after
              const shouldShow = 
                i === 0 || // First page
                i === totalPages - 1 || // Last page
                (i >= currentPage - 2 && i <= currentPage + 2); // Current range
              
              if (!shouldShow) {
                if (i === currentPage - 3 || i === currentPage + 3) {
                  return <span key={i} style={{ color: 'white' }}>...</span>;
                }
                return null;
              }
              
              return (
                <button
                  key={i}
                  onClick={() => setCurrentPage(i + 1)}
                  className={currentPage === i + 1 ? styles.paginationButtonActive : styles.paginationButton}
                >
                  {i + 1}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </Box>
  );
}