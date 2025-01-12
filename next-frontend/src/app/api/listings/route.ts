import { MongoClient } from 'mongodb';
import { NextResponse } from 'next/server';

const uri = process.env.MONGODB_URI;

export async function GET() {
  try {
    if (!uri) {
      throw new Error('MongoDB URI not configured');
    }

    const client = new MongoClient(uri);
    await client.connect();

    const db = client.db('fleatronics');
    const collections = await db.listCollections().toArray();
    // console.log('Available collections:', collections.map(c => c.name));

    // Check if the 'listings' collection exists
    if (!collections.some(c => c.name === 'listings')) {
    //   console.log('Listings collection does not exist.');
      return NextResponse.json([], { status: 200 });
    }

    const listings = await db.collection('listings').find({}).toArray();
    // console.log(`Retrieved ${listings.length} listings from database`);
    
    await client.close();

    if (!listings || listings.length === 0) {
      console.log('No listings found in database');
      return NextResponse.json([], { status: 200 });
    }

    // console.log('Successfully returning listings');
    return NextResponse.json(listings);
    
  } catch (error) {
    // console.error('Database error:', error);
    return NextResponse.json(
      { error: `Failed to fetch listings: ${error instanceof Error ? error.message : 'Unknown error'}` },
      { status: 500 }
    );
  }
}