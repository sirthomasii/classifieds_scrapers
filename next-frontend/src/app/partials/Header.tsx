import { TextInput, Select, ComboboxData } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import styles from '../viewport/viewport.module.css';
import { SE, GB, DE, PL, DK, FI, NL, CH } from 'country-flag-icons/react/3x2';

const FLAG_SIZE = { width: '20px', height: '12px', marginRight: '8px' };

interface MarketplaceItem {
  label: string;
  value: string;
  flag?: JSX.Element;
}

const MARKETPLACE_DATA: MarketplaceItem[] = [
  { label: '🌍 All Marketplaces', value: 'all' },
  { label: 'Blocket', value: 'blocket', flag: <SE style={FLAG_SIZE} /> },
  { label: 'Marktplaats', value: 'blocket', flag: <NL style={FLAG_SIZE} /> },
  { label: 'Gumtree', value: 'gumtree', flag: <GB style={FLAG_SIZE} /> },
  { label: 'Kleinanzeigen', value: 'kleinanzeigen', flag: <DE style={FLAG_SIZE} /> },
  { label: 'OLX', value: 'olx', flag: <PL style={FLAG_SIZE} /> },
  { label: 'DBA', value: 'dba', flag: <DK style={FLAG_SIZE} /> },
  { label: 'Tori', value: 'tori', flag: <FI style={FLAG_SIZE} /> },
  { label: 'Ricardo', value: 'ricardo', flag: <CH style={FLAG_SIZE} /> },
] as const;

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
      <div className={styles.logoText} style={{ 
        userSelect: 'none',
        WebkitUserSelect: 'none',
        msUserSelect: 'none'
      }}>Fleatronics</div>
      <div className={styles.controlsWrapper}>
        <Select
          className={styles.marketplaceSelect}
          value={selectedMarketplace}
          onChange={(value) => onMarketplaceChange(value || 'all')}
          data={MARKETPLACE_DATA}
          renderOption={({ option }) => (
            <div style={{ display: 'flex', alignItems: 'center' }}>
              {(option as MarketplaceItem).flag}
              <span>{option.label}</span>
            </div>
          )}
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
            const value = event.currentTarget.value;
            onSearchChange(value);
            // Trigger search immediately
            onSearch(value);
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