-- Add filter_status and filter_reason to listings table
ALTER TABLE listings 
ADD COLUMN IF NOT EXISTS filter_status text,
ADD COLUMN IF NOT EXISTS filter_reason text,
ADD COLUMN IF NOT EXISTS session_id text;

CREATE INDEX IF NOT EXISTS idx_listings_filter_status ON listings(filter_status);
CREATE INDEX IF NOT EXISTS idx_listings_session_id ON listings(session_id);
