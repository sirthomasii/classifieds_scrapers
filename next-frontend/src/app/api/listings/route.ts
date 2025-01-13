import { MongoClient } from 'mongodb';
import { NextResponse } from 'next/server';

const uri = process.env.MONGODB_URI;

export async function GET() {
  let client;
  try {
    if (!uri) {
      throw new Error('MongoDB URI not configured');
    }

    console.log('Connecting to MongoDB...');
    client = new MongoClient(uri, {
      // Add connection options
      connectTimeoutMS: 10000, // 10 seconds
      socketTimeoutMS: 45000,  // 45 seconds
    });
    
    await client.connect();
    console.log('Connected successfully');

    const db = client.db('fleatronics');
    const listings = await db.collection('listings')
      .find({})
      .limit(100)  // Limit results to prevent timeout
      .toArray();
      
    console.log(`Retrieved ${listings?.length || 0} listings`);

    if (!listings || !Array.isArray(listings)) {
      return NextResponse.json([], { status: 200 });
    }

    return NextResponse.json(listings);
    
  } catch (error) {
    console.error('Detailed error:', error);
    return NextResponse.json(
      { error: `Failed to fetch listings: ${error instanceof Error ? error.message : 'Unknown error'}` },
      { status: 500 }
    );
  } finally {
    if (client) {
      await client?.close();
    }
  }
}