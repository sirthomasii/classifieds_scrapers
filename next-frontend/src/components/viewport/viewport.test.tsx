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
          authToken={null}
          initialPublication={null}
          identifierFilter={null}
          categoryFilter={null}
          onPublicationsChange={() => {}}
        />
      </MantineProvider>
    );
    expect(screen.getByPlaceholderText(/Search publications.../i)).toBeInTheDocument();
  });
});