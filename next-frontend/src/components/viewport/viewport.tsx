import React, { useState, useEffect } from 'react';
import { TextInput, Card, Text, Group, Pagination, Box, Skeleton } from '@mantine/core';
import axios from 'axios';
import qs from 'qs';
import { Publication } from '@/types/publication';
import { motion, AnimatePresence } from 'framer-motion';
import { MarketplaceData } from '@/types/marketplace';
import styles from './viewport.module.css';
import Image from 'next/image';

interface ViewportProps {
  marketplaceData: { all: Publication[] } | undefined;
  selectedCategory: string | null;
  selectedMarketplace: string;
}

export function Viewport({
  marketplaceData,
  selectedCategory,
  selectedMarketplace
}: ViewportProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
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

  return (
    <Box p="md" style={{ maxHeight: '100vh', overflowY: 'auto' }}>
      <div style={{ color: 'white', marginBottom: '20px' }}>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search..."
          style={{
            padding: '8px',
            marginBottom: '10px',
            width: '200px',
            borderRadius: '4px',
            border: '1px solid #666',
            background: 'rgba(255, 255, 255, 0.1)',
            color: 'white'
          }}
        />
        <div style={{ fontSize: '14px', marginTop: '5px' }}>
          Found {searchedData.length} items
        </div>
      </div>

      <div className={styles.gridContainer}>
        {isLoading ? (
          // Show 12 skeleton cards while loading
          Array(12).fill(0).map((_, index) => (
            <div key={index} className={styles.itemCard}>
              <div className={styles.imageContainer}>
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
                  color: '#00ff00',
                  marginBottom: '8px'
                }}>
                  {typeof item.price?.eur === 'number' ? `${item.price.eur} €` : 'Price not available'}
                </div>
                <div style={{ 
                  fontSize: '12px',
                  color: '#999',
                  marginBottom: '4px'
                }}>
                  From: {item.link?.split('/')[2] || 'Unknown source'}
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
        <div className={styles.paginationContainer} style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          gap: '10px',
          padding: '20px 8px',
          width: '100%',
          flexWrap: 'nowrap',
          maxWidth: '100%',
          overflowX: 'auto',
          WebkitOverflowScrolling: 'touch',
          msOverflowStyle: '-ms-autohiding-scrollbar'
        }}>
          <button 
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            style={{
              padding: '5px 10px',
              background: currentPage === 1 ? '#444' : '#666',
              border: 'none',
              borderRadius: '4px',
              color: 'white',
              cursor: currentPage === 1 ? 'default' : 'pointer',
              flexShrink: 0
            }}
          >
            Previous
          </button>
          
          <div style={{ 
            display: 'flex', 
            gap: '4px', 
            padding: '0 4px',
            flexShrink: 0,
            whiteSpace: 'nowrap'
          }}>
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
                style={{
                  padding: '5px 10px',
                  background: currentPage === i + 1 ? '#666' : '#444',
                  border: 'none',
                  borderRadius: '4px',
                  color: 'white',
                  cursor: 'pointer',
                  minWidth: '32px'
                }}
              >
                {i + 1}
              </button>
              );
            })}
          </div>

          <button 
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            style={{
              padding: '5px 10px',
              background: currentPage === totalPages ? '#444' : '#666',
              border: 'none',
              borderRadius: '4px',
              color: 'white',
              cursor: currentPage === totalPages ? 'default' : 'pointer'
            }}
          >
            Next
          </button>
        </div>
      )}
    </Box>
  );
}