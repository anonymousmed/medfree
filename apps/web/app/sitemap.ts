import type { MetadataRoute } from "next";

const base = process.env.NEXT_PUBLIC_SITE_URL ?? "https://medfree.example.com";

export default function sitemap(): MetadataRoute.Sitemap {
  return [
    {
      url: `${base}/`,
      changeFrequency: "weekly",
      priority: 1,
    },
    {
      url: `${base}/atlas`,
      changeFrequency: "weekly",
      priority: 0.9,
    },
    {
      url: `${base}/learn`,
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${base}/practice`,
      changeFrequency: "weekly",
      priority: 0.8,
    },
    {
      url: `${base}/library`,
      changeFrequency: "weekly",
      priority: 0.7,
    },
    {
      url: `${base}/partners`,
      changeFrequency: "monthly",
      priority: 0.4,
    },
  ];
}
