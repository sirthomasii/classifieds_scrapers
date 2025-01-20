import { TextInput, Select } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import styles from '../viewport/viewport.module.css';

interface HeaderProps {
  searchQuery: string;
  selectedMarketplace: string;
  totalItems: number;
  onSearchChange: (value: string) => void;
  onSearch: (value: string) => void;
  onMarketplaceChange: (value: string) => void;
}

export function Header({
  searchQuery,
  selectedMarketplace,
  totalItems,
  onSearchChange,
  onSearch,
  onMarketplaceChange
}: HeaderProps) {
  return (
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
          onChange={(event) => onSearchChange(event.currentTarget.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              onSearch(searchQuery);
            }
          }}
          placeholder={`Search ${totalItems.toLocaleString()} listings...`}
          leftSection={
            <IconSearch 
              size={16} 
              style={{ cursor: 'pointer' }}
              onClick={() => onSearch(searchQuery)}
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
  );
} 