import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Viewport } from './viewport';
import { MantineProvider } from '@mantine/core';

describe('Viewport', () => {
  test('renders search input', () => {
    render(
      <MantineProvider>
        <Viewport
          marketplaceData={undefined}
          selectedCategory={null}
          selectedMarketplace="all"
          onMarketplaceChange={() => {}}
          onLoadMore={() => {}}
        />
      </MantineProvider>
    );
    expect(screen.getByPlaceholderText(/Search listings.../i)).toBeInTheDocument();
  });
});