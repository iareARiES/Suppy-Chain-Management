// MongoDB initialization script for CERONIX Supply Chain Risk Analysis
// This script sets up the database, collections, and initial indexes

// Switch to the Ceronix database
db = db.getSiblingDB('Ceronix');

// Create collections with validation schemas
db.createCollection('nodes', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['node_id', 'name', 'country', 'lat', 'lon'],
      properties: {
        node_id: { bsonType: 'string' },
        name: { bsonType: 'string' },
        country: { bsonType: 'string' },
        lat: { bsonType: 'double', minimum: -90, maximum: 90 },
        lon: { bsonType: 'double', minimum: -180, maximum: 180 },
        tier: { bsonType: 'double', minimum: 0 },
        node_type: { bsonType: 'string' },
        category: { bsonType: 'string' },
        region: { bsonType: 'string' },
        city: { bsonType: 'string' },
        site_url: { bsonType: 'string' },
        alt_url: { bsonType: 'string' },
        x_handle: { bsonType: 'string' },
        ticker: { bsonType: 'string' }
      }
    }
  }
});

db.createCollection('news_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['node_id', 'url', 'headline', 'outlet', 'ts'],
      properties: {
        node_id: { bsonType: 'string' },
        url: { bsonType: 'string' },
        headline: { bsonType: 'string' },
        snippet: { bsonType: 'string' },
        outlet: { bsonType: 'string' },
        ts: { bsonType: 'date' },
        ts_ingested: { bsonType: 'date' },
        sentiment_score: { bsonType: 'double', minimum: -1, maximum: 1 },
        language: { bsonType: 'string' },
        region: { bsonType: 'string' }
      }
    }
  }
});

db.createCollection('social_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['node_id', 'ts', 'handle', 'text'],
      properties: {
        node_id: { bsonType: 'string' },
        ts: { bsonType: 'date' },
        handle: { bsonType: 'string' },
        text: { bsonType: 'string' },
        url: { bsonType: 'string' },
        ts_ingested: { bsonType: 'date' },
        sentiment_score: { bsonType: 'double', minimum: -1, maximum: 1 },
        engagement_count: { bsonType: 'int', minimum: 0 }
      }
    }
  }
});

db.createCollection('extracted_events', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['node_id', 'event_type', 'ts_event', 'source_url', 'extracted_text'],
      properties: {
        node_id: { bsonType: 'string' },
        event_type: { 
          bsonType: 'string',
          enum: ['fire', 'flood', 'strike', 'inspection', 'shutdown', 'outage', 'policy', 'M&A', 'other']
        },
        ts_event: { bsonType: 'date' },
        severity: { 
          bsonType: 'string',
          enum: ['low', 'medium', 'high']
        },
        duration_h: { bsonType: 'double', minimum: 0 },
        geo_text: { bsonType: 'string' },
        source_url: { bsonType: 'string' },
        extracted_text: { bsonType: 'string' },
        confidence: { bsonType: 'double', minimum: 0, maximum: 1 }
      }
    }
  }
});

db.createCollection('weather_anomalies', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['node_id', 'ts', 'anomaly_type', 'severity', 'value', 'threshold'],
      properties: {
        node_id: { bsonType: 'string' },
        ts: { bsonType: 'date' },
        anomaly_type: { 
          bsonType: 'string',
          enum: ['heavy_precip', 'extreme_heat', 'high_wind', 'storm']
        },
        severity: { 
          bsonType: 'string',
          enum: ['low', 'medium', 'high']
        },
        value: { bsonType: 'double' },
        threshold: { bsonType: 'double' },
        duration_h: { bsonType: 'double', minimum: 0 }
      }
    }
  }
});

db.createCollection('market_signals', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['node_id', 'ts', 'signal_type', 'value'],
      properties: {
        node_id: { bsonType: 'string' },
        ticker: { bsonType: 'string' },
        ts: { bsonType: 'date' },
        signal_type: { 
          bsonType: 'string',
          enum: ['price', 'volume', 'volatility']
        },
        value: { bsonType: 'double' },
        z_score: { bsonType: 'double' },
        change_pct: { bsonType: 'double' }
      }
    }
  }
});

db.createCollection('feature_rows', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['node_id', 'name', 'country'],
      properties: {
        node_id: { bsonType: 'string' },
        node_type: { bsonType: 'string' },
        name: { bsonType: 'string' },
        country: { bsonType: 'string' },
        lat: { bsonType: 'double' },
        lon: { bsonType: 'double' },
        tier: { bsonType: 'double' },
        news_count_1d: { bsonType: 'int', minimum: 0 },
        news_count_7d: { bsonType: 'int', minimum: 0 },
        neg_tone_frac_3d: { bsonType: 'double', minimum: 0, maximum: 1 },
        weather_anomaly_7d: { bsonType: 'int', enum: [0, 1] },
        strike_flag_7d: { bsonType: 'int', enum: [0, 1] },
        avg_lead_time_days: { bsonType: 'double', minimum: 0 },
        inventory_days: { bsonType: 'double', minimum: 0 },
        single_sourced: { bsonType: 'int', enum: [0, 1] },
        past_delay_days: { bsonType: 'int', minimum: 0 },
        news_velocity: { bsonType: 'double', minimum: 0 },
        disruption_within_7d: { bsonType: 'int', enum: [0, 1] },
        days_to_disruption: { bsonType: 'int', minimum: 0 }
      }
    }
  }
});

db.createCollection('region_configs', {
  validator: {
    $jsonSchema: {
      bsonType: 'object',
      required: ['name', 'outlets'],
      properties: {
        name: { bsonType: 'string' },
        outlets: { 
          bsonType: 'array',
          items: {
            bsonType: 'object',
            required: ['name', 'url'],
            properties: {
              name: { bsonType: 'string' },
              url: { bsonType: 'string' },
              type: { bsonType: 'string' }
            }
          }
        }
      }
    }
  }
});

// Create indexes for optimal query performance
print('Creating indexes...');

// Nodes indexes
db.nodes.createIndex({ "node_id": 1 }, { unique: true });
db.nodes.createIndex({ "country": 1 });
db.nodes.createIndex({ "node_type": 1 });
db.nodes.createIndex({ "tier": 1 });
db.nodes.createIndex({ "lat": 1, "lon": 1 });
db.nodes.createIndex({ "name": "text", "country": "text" });

// News events indexes
db.news_events.createIndex({ "node_id": 1 });
db.news_events.createIndex({ "ts": -1 });
db.news_events.createIndex({ "outlet": 1 });
db.news_events.createIndex({ "sentiment_score": 1 });
db.news_events.createIndex({ "ts_ingested": -1 });
db.news_events.createIndex({ "url": 1 }, { unique: true });
db.news_events.createIndex({ "headline": "text", "snippet": "text" });
db.news_events.createIndex({ "node_id": 1, "ts": -1 });

// Social events indexes
db.social_events.createIndex({ "node_id": 1 });
db.social_events.createIndex({ "ts": -1 });
db.social_events.createIndex({ "handle": 1 });
db.social_events.createIndex({ "sentiment_score": 1 });
db.social_events.createIndex({ "engagement_count": -1 });
db.social_events.createIndex({ "ts_ingested": -1 });
db.social_events.createIndex({ "text": "text" });
db.social_events.createIndex({ "node_id": 1, "ts": -1 });

// Extracted events indexes
db.extracted_events.createIndex({ "node_id": 1 });
db.extracted_events.createIndex({ "event_type": 1 });
db.extracted_events.createIndex({ "ts_event": -1 });
db.extracted_events.createIndex({ "severity": 1 });
db.extracted_events.createIndex({ "confidence": -1 });
db.extracted_events.createIndex({ "source_url": 1 });
db.extracted_events.createIndex({ "extracted_text": "text" });
db.extracted_events.createIndex({ "node_id": 1, "event_type": 1 });
db.extracted_events.createIndex({ "node_id": 1, "ts_event": -1 });

// Weather anomalies indexes
db.weather_anomalies.createIndex({ "node_id": 1 });
db.weather_anomalies.createIndex({ "ts": -1 });
db.weather_anomalies.createIndex({ "anomaly_type": 1 });
db.weather_anomalies.createIndex({ "severity": 1 });
db.weather_anomalies.createIndex({ "node_id": 1, "anomaly_type": 1 });
db.weather_anomalies.createIndex({ "node_id": 1, "ts": -1 });

// Market signals indexes
db.market_signals.createIndex({ "node_id": 1 });
db.market_signals.createIndex({ "ticker": 1 });
db.market_signals.createIndex({ "ts": -1 });
db.market_signals.createIndex({ "signal_type": 1 });
db.market_signals.createIndex({ "node_id": 1, "signal_type": 1 });
db.market_signals.createIndex({ "ticker": 1, "ts": -1 });

// Feature rows indexes
db.feature_rows.createIndex({ "node_id": 1 }, { unique: true });
db.feature_rows.createIndex({ "country": 1 });
db.feature_rows.createIndex({ "node_type": 1 });
db.feature_rows.createIndex({ "tier": 1 });
db.feature_rows.createIndex({ "disruption_within_7d": 1 });
db.feature_rows.createIndex({ "news_velocity": -1 });
db.feature_rows.createIndex({ "name": "text", "country": "text" });

// Region configs indexes
db.region_configs.createIndex({ "name": 1 }, { unique: true });
db.region_configs.createIndex({ "name": "text" });

print('Database initialization completed successfully!');
print('Collections created: nodes, news_events, social_events, extracted_events, weather_anomalies, market_signals, feature_rows, region_configs');
print('Indexes created for optimal query performance');
