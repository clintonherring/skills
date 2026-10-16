#!/usr/bin/env node
/**
 * Build a one-column, ATS-readable CV (.docx, optional .pdf) from a JSON content file.
 *
 * Usage:
 *   node build-cv.js content.json out.docx [--pdf]
 *
 * --pdf converts with LibreOffice (soffice must be on PATH) and reports page count
 * and file size (target: 2 pages, < 2.5 MB, selectable text).
 *
 * Content schema (all strings are plain text; facts come from the person's facts.md).
 * Produce it with `python3 md_to_cvjson.py cv.md cv.json`:
 * {
 *   "name": "Sam Example",
 *   "headline": "Service Delivery Manager · IT service operations and supplier SLAs",
 *   "contact": ["Utrecht, Netherlands", "+31 6 12345678", "sam.example@example.com"],
 *   "links": [{ "text": "linkedin.com/in/samexample", "url": "https://www.linkedin.com/in/samexample" }],
 *   "status": "Dutch national · Dutch (native), English (fluent)",
 *   "summary": "One short paragraph in first person.",
 *   "highlights": [{ "label": "Supplier SLAs", "text": "One line." }],
 *   "skills": [{ "label": "Service management", "text": "ITIL 4, service reviews, …" }],
 *   "experience": [{ "title": "", "org": "", "dates": "", "intro": "optional", "bullets": ["…"] }],
 *   "projects": [{ "title": "", "org": "", "dates": "", "intro": "", "bullets": [], "link": { "text": "", "url": "" } }],
 *   "education": ["BSc …, 2016", "ITIL 4 Foundation (2019)"],
 *   "extra": { "heading": "Interests", "text": "One line." },
 *   "headings": { "summary": "Summary", "skills": "Skills", "experience": "Experience",
 *                 "projects": "Projects", "education": "Education and certifications" }
 * }
 *
 * The docx package is resolved from: ./node_modules, $DOCX_MODULE, or a global install.
 * Install with `npm install` in this directory.
 */
const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");

function loadDocx() {
  const candidates = ["docx", process.env.DOCX_MODULE, path.join(__dirname, "node_modules", "docx")].filter(Boolean);
  for (const c of candidates) {
    try {
      return require(c);
    } catch (_) {
      /* next */
    }
  }
  console.error("Could not load 'docx'. Run `npm install` in scripts/ or set DOCX_MODULE.");
  process.exit(1);
}

const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  AlignmentType,
  BorderStyle,
  LevelFormat,
  HeadingLevel,
  ExternalHyperlink,
  TabStopType,
  TabStopPosition,
} = loadDocx();

const FONT = "Calibri";
const INK = "1A2332";
const ACCENT = "2C3E50";
const MUTE = "546E7A";
const LINK = "2B579A";
const A4 = { width: 11906, height: 16838 };
const rule = { bottom: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 1 } };

const run = (text, opts = {}) => new TextRun({ text, font: FONT, color: INK, size: 20, ...opts });

const sectionHeading = (text) =>
  new Paragraph({
    keepNext: true,
    heading: HeadingLevel.HEADING_1,
    border: rule,
    spacing: { before: 260, after: 100 },
    children: [run(text.toUpperCase(), { bold: true, color: ACCENT, characterSpacing: 60 })],
  });

const body = (text, opts = {}) =>
  new Paragraph({
    keepNext: !!opts.keepNext,
    keepLines: true,
    spacing: { after: opts.after ?? 80, before: opts.before ?? 0, line: 276 },
    children: [run(text, { size: opts.size ?? 20, italics: !!opts.italics, color: opts.color ?? INK })],
  });

const bullet = (text) =>
  new Paragraph({
    numbering: { reference: "cv-bullets", level: 0 },
    spacing: { after: 60, line: 276 },
    children: [run(text)],
  });

const labelledBullet = (label, text) =>
  new Paragraph({
    numbering: { reference: "cv-bullets", level: 0 },
    spacing: { after: 70, line: 276 },
    children: [run(`${label}  `, { bold: true, color: ACCENT }), run(text)],
  });

const skillLine = (label, text) =>
  new Paragraph({
    spacing: { after: 50, line: 276 },
    indent: { left: 1700, hanging: 1700 },
    tabStops: [{ type: TabStopType.LEFT, position: 1700 }],
    children: [run(label, { bold: true, color: ACCENT }), run(`\t${text}`)],
  });

const roleHeader = (title, org, dates) =>
  new Paragraph({
    keepNext: true,
    spacing: { before: 160, after: 40 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      run(title, { bold: true, size: 21 }),
      ...(org ? [run(`  |  ${org}`, { size: 21, color: ACCENT })] : []),
      ...(dates ? [run(`\t${dates}`, { size: 19, color: MUTE })] : []),
    ],
  });

const hyperlink = (text, url, size = 18) =>
  new ExternalHyperlink({ link: url, children: [run(text, { size, color: LINK, underline: {} })] });

const styles = {
  default: { document: { run: { font: FONT, size: 20, color: INK } } },
  paragraphStyles: [
    {
      id: "Heading1",
      name: "Heading 1",
      basedOn: "Normal",
      next: "Normal",
      quickFormat: true,
      run: { size: 20, bold: true, font: FONT, color: ACCENT },
      paragraph: { spacing: { before: 260, after: 100 }, outlineLevel: 0 },
    },
  ],
};

const numbering = {
  config: [
    {
      reference: "cv-bullets",
      levels: [
        {
          level: 0,
          format: LevelFormat.BULLET,
          text: "•",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 360, hanging: 180 } } },
        },
      ],
    },
  ],
};

function entryBlock(e) {
  const out = [roleHeader(e.title, e.org, e.dates)];
  if (e.intro) out.push(body(e.intro, { after: 40, keepNext: (e.bullets || []).length > 0 }));
  for (const b of e.bullets || []) out.push(bullet(b));
  if (e.link && e.link.url) {
    out.push(
      new Paragraph({
        spacing: { after: 40 },
        indent: { left: 360 },
        children: [run("See: ", { size: 18, color: MUTE }), hyperlink(e.link.text || e.link.url, e.link.url)],
      })
    );
  }
  return out;
}

function buildCv(c) {
  const h = Object.assign(
    {
      summary: "Summary",
      skills: "Skills",
      experience: "Experience",
      projects: "Projects",
      education: "Education and certifications",
    },
    c.headings || {}
  );

  const contactChildren = [];
  const contactText = (c.contact || []).join("  ·  ");
  if (contactText) contactChildren.push(run(contactText + ((c.links || []).length ? "  ·  " : ""), { size: 18, color: MUTE }));
  (c.links || []).forEach((l, i) => {
    if (i > 0) contactChildren.push(run("  ·  ", { size: 18, color: MUTE }));
    contactChildren.push(hyperlink(l.text || l.url, l.url));
  });

  const header = [
    new Paragraph({ spacing: { after: 40 }, children: [run(c.name, { bold: true, size: 36 })] }),
    ...(c.headline
      ? [new Paragraph({ spacing: { after: 60 }, children: [run(c.headline, { size: 22, color: ACCENT })] })]
      : []),
    new Paragraph({ spacing: { after: 40 }, border: rule, children: contactChildren }),
    ...(c.status ? [body(c.status, { size: 17, italics: true, color: MUTE, before: 60, after: 40 })] : []),
  ];

  const summary = [];
  if (c.summary || (c.highlights || []).length) {
    summary.push(sectionHeading(h.summary));
    if (c.summary) summary.push(body(c.summary, { after: (c.highlights || []).length ? 100 : 60 }));
    for (const x of c.highlights || []) summary.push(labelledBullet(x.label, x.text));
  }

  const skills = (c.skills || []).length
    ? [sectionHeading(h.skills), ...c.skills.map((s) => skillLine(s.label, s.text))]
    : [];

  const experience = (c.experience || []).length
    ? [sectionHeading(h.experience), ...c.experience.flatMap(entryBlock)]
    : [];

  const projects = (c.projects || []).length
    ? [sectionHeading(h.projects), ...c.projects.flatMap(entryBlock)]
    : [];

  const education = (c.education || []).length
    ? [sectionHeading(h.education), ...c.education.map(bullet)]
    : [];

  const extra = c.extra && c.extra.text ? [sectionHeading(c.extra.heading || "Interests"), body(c.extra.text)] : [];

  return new Document({
    creator: c.name,
    title: `${c.name} — CV`,
    styles,
    numbering,
    sections: [
      {
        properties: { page: { size: A4, margin: { top: 720, right: 760, bottom: 720, left: 760 } } },
        children: [...header, ...summary, ...skills, ...experience, ...projects, ...education, ...extra],
      },
    ],
  });
}

function toPdf(docxPath) {
  const outDir = path.dirname(path.resolve(docxPath));
  try {
    execFileSync("soffice", ["--headless", "--convert-to", "pdf", "--outdir", outDir, docxPath], { stdio: "ignore" });
  } catch (e) {
    console.error("PDF conversion failed (is LibreOffice installed?):", e.message);
    return;
  }
  const pdf = path.join(outDir, path.basename(docxPath).replace(/\.docx$/i, ".pdf"));
  const sizeMb = fs.statSync(pdf).size / (1024 * 1024);
  let pages = "?";
  try {
    const info = execFileSync("pdfinfo", [pdf], { encoding: "utf8" });
    pages = (info.match(/Pages:\s+(\d+)/) || [])[1] || "?";
  } catch (_) {
    /* pdfinfo optional */
  }
  console.log(`Wrote ${pdf}  (${pages} pages, ${sizeMb.toFixed(2)} MB${sizeMb > 2.5 ? " — OVER 2.5 MB" : ""})`);
}

async function main() {
  const [, , input, output, ...flags] = process.argv;
  if (!input || !output) {
    console.error("Usage: node build-cv.js content.json out.docx [--pdf]");
    process.exit(2);
  }
  const content = JSON.parse(fs.readFileSync(input, "utf8"));
  fs.mkdirSync(path.dirname(path.resolve(output)), { recursive: true });
  fs.writeFileSync(output, await Packer.toBuffer(buildCv(content)));
  console.log("Wrote", output);
  if (flags.includes("--pdf")) toPdf(output);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
