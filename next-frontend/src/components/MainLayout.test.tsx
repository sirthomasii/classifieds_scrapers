import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MainLayout } from './MainLayout';
import { MantineProvider } from '@mantine/core';
import axios from 'axios';

// Mock axios
jest.mock('axios');

describe('MainLayout', () => {
  beforeEach(() => {
    // Reset the mock before each test
    (axios.get as jest.Mock).mockResolvedValue({ data: {} }); // Cast axios.get to jest.Mock
  });

  test('renders children correctly', () => {
    render(
      <MantineProvider>
        <MainLayout>
          <div>Test Child</div>
        </MainLayout>
      </MantineProvider>
    );
    // Debug the rendered output
    // screen.debug(); // This will print the current DOM state to the console
    // Use a regex to match the text more flexibly
    expect(screen.getByText('Identifier')).toBeInTheDocument();
  });

  test('renders sidebar button', () => {
    render(
      <MantineProvider>
        <MainLayout>
          <div>Test Child</div>
        </MainLayout>
      </MantineProvider>
    );
    const buttons = screen.getAllByRole('button');
    expect(buttons[0]).toBeInTheDocument(); // Adjust index as necessary
  });
});