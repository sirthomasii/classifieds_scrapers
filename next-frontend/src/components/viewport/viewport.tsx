import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Box, Skeleton, Select, TextInput } from '@mantine/core';
import { Publication } from '@/types/publication';
import styles from './viewport.module.css';
import Image from 'next/image';
import { IconSearch } from '@tabler/icons-react';
import { GB, DK, FI, CH, DE, RO, SE } from 'country-flag-icons/react/3x2';
import Head from 'next/head';

interface ViewportProps {
  marketplaceData: {
    items: Publication[];
    total: number;
    currentBuffer: number;
  } | undefined;
  selectedCategory: string | null;
  selectedMarketplace: string;
  onMarketplaceChange: (marketplace: string) => void;
  onLoadMore: (buffer: number) => void;
}

export function Viewport({
  marketplaceData,
  selectedCategory,
  selectedMarketplace,
  onMarketplaceChange,
  onLoadMore
}: ViewportProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const gridRef = useRef<HTMLDivElement>(null);
  const resizeTimeoutRef = useRef<NodeJS.Timeout>();
  const searchTimeoutRef = useRef<NodeJS.Timeout>();
  const itemsPerPage = 15;
  const bufferSize = 1000;

  const filteredData = marketplaceData?.items ?? [];
  const totalItems = marketplaceData?.total ?? 0;

  // Memoize sorted data to prevent unnecessary re-sorting
  const sortedData = useMemo(() => 
    [...filteredData].sort((a, b) => {
      const timeA = a.timestamp ? new Date(a.timestamp).getTime() : 0;
      const timeB = b.timestamp ? new Date(b.timestamp).getTime() : 0;
      return timeB - timeA;
    }), [filteredData]);

  // Helper function to get the display title
  const getDisplayTitle = (item: Publication) => {
    if (!item.title) return '';
    return item.title.english || item.title.original || '';
  };

  // Memoize searched data to prevent unnecessary filtering
  const searchedData = useMemo(() => 
    activeSearch 
      ? sortedData.filter(item => {
          const title = getDisplayTitle(item);
          const searchTerm = activeSearch.toLowerCase();
          return title && title.toLowerCase().includes(searchTerm);
        })
      : sortedData,
    [sortedData, activeSearch]
  );

  // Debounced search handler
  const handleSearch = useCallback((value: string) => {
    setIsSearching(true);
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    searchTimeoutRef.current = setTimeout(() => {
      setActiveSearch(value);
      setIsSearching(false);
    }, 300);
  }, []);

  // Cleanup timeouts
  useEffect(() => {
    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, []);

  // Modified resize handler with search state check
  const handleResize = useCallback(() => {
    if (resizeTimeoutRef.current) {
      clearTimeout(resizeTimeoutRef.current);
    }
    if (!isSearching && gridRef.current) {
      resizeTimeoutRef.current = setTimeout(() => {
        if (gridRef.current) {
          // Instead of toggling display, use a transform to force a new stacking context
          gridRef.current.style.transform = 'translateZ(0)';
          requestAnimationFrame(() => {
            if (gridRef.current) {
              gridRef.current.style.transform = '';
            }
          });
        }
      }, 100);
    }
  }, [isSearching]);

  useEffect(() => {
    window.addEventListener('resize', handleResize);
    return () => {
      window.removeEventListener('resize', handleResize);
      if (resizeTimeoutRef.current) {
        clearTimeout(resizeTimeoutRef.current);
      }
    };
  }, [handleResize]);

  // Load more data when approaching end of current buffer
  useEffect(() => {
    const currentPosition = (currentPage - 1) * itemsPerPage;
    const bufferThreshold = marketplaceData?.currentBuffer ?? 0 - 100; // Load more when 100 items from end
    
    if (currentPosition > bufferThreshold) {
      onLoadMore(marketplaceData?.currentBuffer ?? 0 + bufferSize);
    }
  }, [currentPage, marketplaceData?.currentBuffer]);

  // Reset to page 1 when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [activeSearch, selectedCategory, selectedMarketplace]);

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

  const isLoading = !marketplaceData;

  // Generate search suggestions from titles
  useEffect(() => {
    if (searchQuery.length > 2) {
      const allTitles = (marketplaceData?.items || [])
        .map(getDisplayTitle)
        .filter((title): title is string => typeof title === 'string' && title.length > 0);
      
      // Create a Set to ensure unique values
      const uniqueSuggestions = new Set(allTitles
        .filter(title => 
          title.toLowerCase().includes(searchQuery.toLowerCase())
        ));
      // Convert back to array and take first 5
      const suggestions = Array.from(uniqueSuggestions).slice(0, 5);
      setSearchSuggestions(suggestions);
    } else {
      setSearchSuggestions([]);
    }
  }, [searchQuery, marketplaceData]);

  const getFlagComponent = (source: string) => {
    switch(source) {
      case 'ricardo':
        return <CH style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
      case 'gumtree':
        return <GB style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
      case 'kleinanzeigen':
        return <DE style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
      case 'olx':
        return <RO style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
      case 'blocket':
        return <SE style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
      case 'tori':
        return <FI style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
      case 'dba':
        return <DK style={{ width: '14px', marginRight: '4px', verticalAlign: 'middle' }} />;
      default:
        return null;
    }
  };

  return (
    <>
      <Box p="md" style={{ maxHeight: '100vh', overflowY: 'auto' }}>
        <div style={{ 
          padding: '16px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
        }} className={styles.headerContainer}>
          <div className={styles.logoText}>Fleatronics</div>
          <div className={styles.controlsWrapper}>
            <Select
              className={styles.marketplaceSelect}
              value={selectedMarketplace}
              onChange={(value) => onMarketplaceChange(value || 'all')}
              data={[
                { value: 'all', label: 'All Marketplaces' },
                { value: 'blocket', label: 'Blocket' },
                { value: 'gumtree', label: 'Gumtree' },
                { value: 'kleinanzeigen', label: 'Kleinanzeigen' },
                { value: 'olx', label: 'OLX' },
                { value: 'dba', label: 'DBA' },
                { value: 'tori', label: 'Tori' },
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
                option: {
                  backgroundColor: '#2C2E33',
                  color: 'white',
                  '&:hover': {
                    backgroundColor: '#1C1E23'
                  }
                },
              }}
            />
            <TextInput
              className={styles.searchBar}
              style={{ flex: 1 }}
              value={searchQuery}
              onChange={(event) => {
                setSearchQuery(event.currentTarget.value);
                handleSearch(event.currentTarget.value);
              }}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  handleSearch(searchQuery);
                }
              }}
              placeholder={`Search ${totalItems.toLocaleString()} listings...`}
              leftSection={
                <IconSearch 
                  size={16} 
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleSearch(searchQuery)}
                />
              }
              styles={{
                input: {
                  backgroundColor: '#2C2E33',
                  color: 'white',
                  borderRadius: '20px',
                  '&::placeholder': {
                    color: 'rgba(255, 255, 255, 0.5)',
                  },
                },
              }}
            />
          </div>
        </div>

        <div 
          ref={gridRef} 
          className={styles.gridContainer}
          style={{
            opacity: isSearching ? 0.8 : 1,
            transition: 'opacity 0.5s ease-in-out'
          }}
        >
          {isLoading ? (
            // Show 15 skeleton cards while loading
            Array(15).fill(0).map((_, index) => (
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
                    <img
                      src={item.main_image}
                      alt={getDisplayTitle(item) || 'Product image'}
                      className={styles.imageLoading}
                      onError={(e) => {
                        const imgElement = e.target as HTMLImageElement;
                        imgElement.style.display = 'none';
                        const container = imgElement.parentElement;
                        if (container) {
                          container.style.backgroundColor = '#333';
                        }
                      }}
                      onLoad={(e) => {
                        const imgElement = e.target as HTMLImageElement;
                        imgElement.style.display = 'block';
                        imgElement.classList.remove(styles.imageLoading);
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
                    {item.title?.english || item.title?.original}
                  </div>
                  <div style={{ 
                    fontSize: '14px',
                    color: '#4CAF50',
                    marginBottom: '8px'
                  }}>
                    {typeof item.price?.eur === 'number' ? `${item.price.eur} €` : 'Negotiable'}
                  </div>
                  <div style={{ 
                    fontSize: '12px',
                    color: '#aaa',
                    marginBottom: '4px'
                  }}>
                    <span style={{ 
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      marginRight: '8px',
                      textTransform: 'capitalize',
                      display: 'inline-flex',
                      alignItems: 'center'
                    }}>
                      {item.source}&nbsp;
                      {getFlagComponent(item.source)}
                    </span>
                    {item.timestamp ? new Date(item.timestamp).toLocaleString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                      hour12: false
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
    </>
  );
}