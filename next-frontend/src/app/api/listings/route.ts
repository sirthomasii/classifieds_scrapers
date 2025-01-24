import mongoose from 'mongoose';
import { NextResponse } from 'next/server';

const uri = process.env.MONGODB_URI;
// Define schema outside of the route handler
const listingSchema = new mongoose.Schema({
  link: String,
  source: String,
  // description: String,
  // last_updated: Date,
  main_image: String,
  timestamp: Date,
  title: {
    english: String,
    original: String
  },
  price: {
    eur: String
  }

}, { strict: false });

// Create model outside of the route handler
const Listing = mongoose.models.Listing || mongoose.model('Listing', listingSchema);

// Create cached connection
let cachedConnection: typeof mongoose | null = null;

async function connectDB() {
  if (cachedConnection) {
    return cachedConnection;
  }

  if (!uri) {
    throw new Error('MongoDB URI is not configured');
  }

  cachedConnection = await mongoose.connect(uri, {
    dbName: 'fleatronics',
    autoCreate: true,
  });

  return cachedConnection;
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '50');
    const source = searchParams.get('source') || null;
    const search = searchParams.get('search') || '';

    console.log('Search query:', search);

    await connectDB();
    
    let query: any = {};
    if (source && source !== 'all') {
      query.source = source;
    }
    if (search) {
      query.$or = [
        { 'title.english': { $regex: search, $options: 'i' } },
        // { 'title.original': { $regex: search, $options: 'i' } }
      ];
    }
    
    const [listings, total] = await Promise.all([
      Listing.find(query)
        .select('link source main_image timestamp title.english title.original price.eur')
        .sort({ timestamp: -1 })
        .skip((page - 1) * limit)
        .limit(limit)
        .maxTimeMS(5000)
        .lean(),
      Listing.countDocuments(query)
    ]);

    console.log('Listings:', listings);
    console.log('Total:', total);

    return NextResponse.json({ 
      data: listings || [],
      total,
      page,
      totalPages: Math.ceil(total / limit),
      error: null 
    });
    
  } catch (error) {
    const err = error as Error;
    console.error('Database operation failed:', err);
    return NextResponse.json(
      { error: 'Database operation failed', data: [], total: 0, page: 1, totalPages: 0 },
      { status: 500 }
    );
  }
}