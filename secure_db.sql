
-- 1. RLS auf der Tabelle aktivieren (sperrt alles standardmäßig)
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;

-- 2. Policy für EINGELOGGTE User (Dashboard)
-- Erlaubt alles (Lesen, Bearbeiten, Löschen), solange man eingeloggt ist.
CREATE POLICY "Enable access for authenticated users only"
ON "public"."listings"
AS PERMISSIVE
FOR ALL
TO authenticated
USING (true)
WITH CHECK (true);

-- 3. (Optional) Policy für Bot, falls er den Anon-Key nutzt (Nicht empfohlen, besser Service-Role nutzen!)
-- Wenn dein Bot den Service-Role Key hat, braucht er KEINE Policy (er darf immer alles).
-- Falls der Bot kaputt geht, nutze vorübergehend diese Zeile (macht aber Schutz schwächer):
-- CREATE POLICY "Enable access for anon" ON "public"."listings" FOR ALL TO anon USING (true) WITH CHECK (true);
