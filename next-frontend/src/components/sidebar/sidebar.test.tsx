import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Sidebar } from './sidebar';
import { Publication } from '../types/publication';
import { MantineProvider } from '@mantine/core';

const mockPublications: Publication[] = [
  { id: 1, name: 'Publication 1', identifier: 'pub1', status: 'published', category: 'news', title: 'Title 1', uid: 'uid1', level: 'level1', is_visible: true, is_default: false, created_on: new Date().toISOString(), modified_on: new Date().toISOString(), affected_on: new Date().toISOString(), first_published_on: new Date().toISOString(), published_on: new Date().toISOString() },
  { id: 2, name: 'Publication 2', identifier: 'pub2', status: 'draft', category: 'tech', title: 'Title 2', uid: 'uid2', level: 'level2', is_visible: false, is_default: false, created_on: new Date().toISOString(), modified_on: new Date().toISOString(), affected_on: new Date().toISOString(), first_published_on: new Date().toISOString(), published_on: new Date().toISOString() },
];

describe('Sidebar', () => {
  test('renders publication filters', () => {
    render(
      <MantineProvider>
        <Sidebar
          publications={mockPublications}
          identifierFilter={null}
          categoryFilter={null}
          onIdentifierChange={() => {}}
          onCategoryChange={() => {}}
        />
      </MantineProvider>
    );
    expect(screen.getByText('news')).toBeInTheDocument();
  });
});