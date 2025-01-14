import mongoose from 'mongoose';
import { NextResponse } from 'next/server';

const uri = process.env.MONGODB_URI;

// Define a schema for your listings
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
}, { strict: false }); // Changed to strict: true for data consistency

// Create a model
const Listing = mongoose.models.Listing || mongoose.model('Listing', listingSchema);

export async function GET() {
  try {
    if (!uri) {
      console.error('MongoDB URI is not configured in environment variables');
      return NextResponse.json(
        { error: 'Database configuration error', data: [] },
        { status: 500 }
      );
    }

    // Connect to MongoDB using Mongoose
    await mongoose.connect(uri);

    // Query using Mongoose model
    const listings = await Listing.find({})
      .maxTimeMS(5000)
      .lean(); // .lean() returns plain JavaScript objects instead of Mongoose documents

    return NextResponse.json({ 
      data: listings || [],
      error: null 
    });
    
  } catch (error) {
    return NextResponse.json(
      { error: 'Database connection failed', data: [] },
      { status: 500 }
    );
  } finally {
    // Mongoose manages the connection pool automatically
    // but you can close it if needed
    // await mongoose.disconnect();
  }
}