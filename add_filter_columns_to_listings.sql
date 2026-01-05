-- Add filter_status and filter_reason to listings table
ALTER TABLE listings 
ADD COLUMN filter_status text,
ADD COLUMN filter_reason text;

CREATE INDEX idx_listings_filter_status ON listings(filter_status);
