export function getSiteUrl(): URL {
  const raw = process.env.BOLSABR_SITE_URL ?? "http://localhost:3000";
  return new URL(raw.endsWith("/") ? raw : `${raw}/`);
}
