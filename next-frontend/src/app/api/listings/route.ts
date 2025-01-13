import { MongoClient } from 'mongodb';
import { NextResponse } from 'next/server';

const uri = process.env.MONGODB_URI;

export async function GET() {
  let client;
  try {
    if (!uri) {
      return NextResponse.json({ error: 'MongoDB URI not configured' }, { status: 500 });
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
      .limit(50)
      .maxTimeMS(5000)
      .toArray();

    return NextResponse.json(listings || []);
    
  } catch (error) {
    return NextResponse.json(
      { error: 'Database connection failed' },
      { status: 500 }
    );
  } finally {
    await client?.close().catch(() => {});
  }
}