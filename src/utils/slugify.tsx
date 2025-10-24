export const slugify = (str: string) =>
  str.toLowerCase().replace(/\s+/g, '_').replace(/[^\w_]/g, '');

export const unslugify = (slug: string) =>
  slug
    .replace(/_/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());