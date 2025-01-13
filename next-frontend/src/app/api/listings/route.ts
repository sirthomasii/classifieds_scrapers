import { MongoClient } from 'mongodb';
import { NextResponse } from 'next/server';

const uri = process.env.MONGODB_URI;

export async function GET() {
  let client;
  try {
    if (!uri) {
      console.error('MongoDB URI is not configured in environment variables');
      return NextResponse.json(
        { error: 'Database configuration error', data: [] },
        { status: 500 }
      );
    }

    if (!uri.startsWith('mongodb')) {
      console.error('Invalid MongoDB URI format');
      return NextResponse.json(
        { error: 'Invalid database configuration', data: [] },
        { status: 500 }
      );
    }
    
    client = new MongoClient(uri, {
      connectTimeoutMS: 5000,
      socketTimeoutMS: 10000,
      serverSelectionTimeoutMS: 5000,
    });
    
    await client.connect();

    const db = client.db('fleatronics');
    const listings = await db.collection('listings')
      .find({})
      // .limit(50)
      .maxTimeMS(5000)
      .toArray();

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
    await client?.close().catch(() => {});
  }
}