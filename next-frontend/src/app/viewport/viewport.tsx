import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { Box, Skeleton, Select, TextInput } from '@mantine/core';
import { Publication } from '@/types/publication';
import styles from './viewport.module.css';
import { Header } from '../partials/Header';
import { ListingCard } from './fragments/ListingCard';
import { AdCard } from './fragments/AdCard';
import { Pagination } from './fragments/Pagination';
import { GDPRBanner } from './fragments/GDPRBanner';

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
  onSearch: (query: string) => void;
  onPageChange?: (page: number) => void;
}

export function Viewport({
  marketplaceData,
  selectedCategory,
  selectedMarketplace,
  onMarketplaceChange,
  onLoadMore,
  onSearch,
  onPageChange
}: ViewportProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeSearch, setActiveSearch] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const gridRef = useRef<HTMLDivElement>(null);
  const resizeTimeoutRef = useRef<NodeJS.Timeout>();
  const searchTimeoutRef = useRef<NodeJS.Timeout>();
  const [itemsPerPage, setItemsPerPage] = useState(15);
  const bufferSize = 1000;
  const [showGDPR, setShowGDPR] = useState(true);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

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

  // Debounced search handler
  const handleSearch = useCallback((value: string) => {
    setIsSearching(true);
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }
    searchTimeoutRef.current = setTimeout(() => {
      setActiveSearch(value);
      setIsSearching(false);
      // Call the onSearch prop to trigger API call
      onSearch(value);
    }, 300);
  }, [onSearch]);

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

  // Calculate total pages based on total items from server and items per page
  const totalPages = Math.ceil((marketplaceData?.total ?? 0) / itemsPerPage);
  
  // Ensure current page is valid
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(1);
    }
  }, [totalPages, currentPage]);

  // Use sortedData directly since filtering is now done by the API
  const displayedItems = sortedData;

  // Insert ad at random position
  const displayedItemsWithAd = useMemo(() => {
    if (displayedItems.length === 0) return displayedItems;
    const randomIndex = Math.floor(Math.random() * displayedItems.length);
    const result = [...displayedItems] as (Publication | 'ad')[];
    result.splice(randomIndex, 0, 'ad');
    return result;
  }, [displayedItems]);

// Filter out the 'ad' items
const displayedItemsWithoutAd = useMemo(() => {
  return displayedItemsWithAd.filter(item => item !== 'ad');
}, [displayedItemsWithAd]);

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

  // Add window resize handler for responsive itemsPerPage
  useEffect(() => {
    const handleItemsPerPage = () => {
      const width = window.innerWidth;
      if (width > 1400) { // 5 columns
        setItemsPerPage(15);
      } else if (width > 1100) { // 4 columns
        setItemsPerPage(12);
      } else if (width > 768) { // 3 columns
        setItemsPerPage(9);
      } else { // 2 columns
        setItemsPerPage(6);
      }
    };

    // Set initial value
    handleItemsPerPage();

    // Add event listener
    window.addEventListener('resize', handleItemsPerPage);

    // Cleanup
    return () => window.removeEventListener('resize', handleItemsPerPage);
  }, []);

  useEffect(() => {
    // Check localStorage only on client side
    const gdprAccepted = localStorage.getItem('gdprAccepted');
    if (gdprAccepted) {
      setShowGDPR(false);
    }
  }, []);

  const handleGDPRAccept = () => {
    localStorage.setItem('gdprAccepted', 'true');
    setShowGDPR(false);
  };

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    onPageChange?.(newPage);
    scrollContainerRef.current?.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <Box style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Header 
        searchQuery={searchQuery}
        selectedMarketplace={selectedMarketplace}
        totalItems={totalItems}
        onSearchChange={(value) => {
          setSearchQuery(value);
          handleSearch(value);
        }}
        onSearch={handleSearch}
        onMarketplaceChange={onMarketplaceChange}
      />

      <div 
        ref={scrollContainerRef}
        style={{ flex: 1, overflowY: 'auto', position: 'relative' }}
      >
        <div ref={gridRef} className={styles.gridContainer}>
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
            // displayedItemsWithAd.map((item, index) => {
            //   if (item === 'ad') {
            //     return <AdCard key={`ad-${index}`} />;
            //   }
            //   return (
            //     <ListingCard 
            //       key={`${item.link}-${index}`}
            //       item={item}
            //       getDisplayTitle={getDisplayTitle}
            //     />
            //   );
            // })
            displayedItemsWithoutAd.map((item, index) => {
              return (
                <ListingCard 
                  key={`${item.link}-${index}`}
                  item={item}
                  getDisplayTitle={getDisplayTitle}
                />
              );
            })
          )}
        </div>

        <Pagination 
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={handlePageChange}
        />
      </div>

      {showGDPR && <GDPRBanner onAccept={handleGDPRAccept} />}
    </Box>
  );
}