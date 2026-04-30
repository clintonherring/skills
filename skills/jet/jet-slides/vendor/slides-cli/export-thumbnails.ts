#!/usr/bin/env bun
// Export all slides from a presentation as PNG thumbnails
import { getAuthClient } from "./src/auth";
import { google } from "googleapis";
import * as fs from "node:fs";
import * as path from "node:path";

const presentationId = process.argv[2];
const outputDir = process.argv[3] || "/tmp/slides-export";

if (!presentationId) {
  console.error("Usage: bun export-thumbnails.ts <presentation-id> <output-dir>");
  process.exit(1);
}

fs.mkdirSync(outputDir, { recursive: true });

const auth = await getAuthClient();
if (!auth) {
  console.error("Not authenticated");
  process.exit(1);
}

const slides = google.slides({ version: "v1", auth });
const pres = await slides.presentations.get({ presentationId });
const slidePages = pres.data.slides ?? [];

console.log(`Exporting ${slidePages.length} slides from "${pres.data.title}"...`);

for (let i = 0; i < slidePages.length; i++) {
  const slideId = slidePages[i].objectId!;
  const thumb = await slides.presentations.pages.getThumbnail({
    presentationId,
    pageObjectId: slideId,
    "thumbnailProperties.thumbnailSize": "LARGE",
  });
  
  const url = thumb.data.contentUrl!;
  const response = await fetch(url);
  const buffer = await response.arrayBuffer();
  const outPath = path.join(outputDir, `slide-${String(i).padStart(2, "0")}.png`);
  fs.writeFileSync(outPath, Buffer.from(buffer));
  console.log(`  Slide ${i}: ${outPath}`);
}

console.log("Done!");
