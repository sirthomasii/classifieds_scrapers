import mongoose from 'mongoose';
import { NextResponse } from 'next/server';

const uri = process.env.MONGODB_URI;

// Define schema outside of the route handler
const listingSchema = new mongoose.Schema({
  link: String,
  source: String,
  description: String,
  last_updated: Date,
  main_image: String,
  price: String,
  timestamp: Date,
  title: {
    original: String,
    english: String
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

export async function GET() {
  try {
    await connectDB();
    
    const listings = await Listing.find({})
      .maxTimeMS(5000)
      .lean();

    return NextResponse.json({ 
      data: listings || [],
      error: null 
    });
    
  } catch (error) {
    const err = error as Error;
    console.error('Database operation failed:', err);
    return NextResponse.json(
      { error: 'Database operation failed', data: [] },
      { status: 500 }
    );
  }
}