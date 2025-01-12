export interface Publication {
  title: {
    original: string | null;
    english: string | null;
  };
  description: string | null;
  main_image: string | null;
  link: string | null;
  price: string | null;
  timestamp: string | null;
  source: string;
  scraped_at: string;
} 