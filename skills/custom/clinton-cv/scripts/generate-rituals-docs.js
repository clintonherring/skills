/**
 * Generates the Rituals-tailored CV and cover letter for Clinton Herring.
 *
 * Usage:
 *   cd skills/custom/clinton-cv/scripts && npm install && node generate-rituals-docs.js
 *
 * Content facts come from ../SKILL.md and ../references/. Edit text here only
 * after updating those files so the skill stays the source of truth.
 */
const fs = require("fs");
const path = require("path");

function loadDocx() {
  const candidates = [
    "docx",
    process.env.DOCX_MODULE,
    path.join(__dirname, "node_modules", "docx"),
  ].filter(Boolean);
  for (const candidate of candidates) {
    try {
      return require(candidate);
    } catch (_) {
      // try next
    }
  }
  console.error(
    "Could not load the 'docx' package. Run `npm install` in this scripts/ directory, " +
      "or set DOCX_MODULE to a docx package path."
  );
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

const ASSETS = path.join(__dirname, "..", "assets");
const CV_OUT = path.join(ASSETS, "Clinton_Herring_Rituals_Retail_Tech_Architect_CV.docx");
const LETTER_OUT = path.join(ASSETS, "Clinton_Herring_Rituals_Cover_Letter.docx");

const FONT = "Calibri";
const INK = "1A2332";
const ACCENT = "2C3E50";
const MUTE = "546E7A";
const LINK = "2B579A";

const A4 = { width: 11906, height: 16838 };

const rule = {
  bottom: { style: BorderStyle.SINGLE, size: 12, color: ACCENT, space: 1 },
};

const run = (text, opts = {}) =>
  new TextRun({ text, font: FONT, color: INK, size: 20, ...opts });

function sectionHeading(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    border: rule,
    spacing: { before: 260, after: 100 },
    children: [
      run(text.toUpperCase(), { bold: true, color: ACCENT, characterSpacing: 60 }),
    ],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 80, before: opts.before ?? 0, line: 276 },
    children: [run(text, { size: opts.size ?? 20, italics: !!opts.italics, color: opts.color ?? INK })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "cv-bullets", level: 0 },
    spacing: { after: 40, line: 276 },
    children: [run(text)],
  });
}

function labelledBullet(label, text) {
  return new Paragraph({
    numbering: { reference: "cv-bullets", level: 0 },
    spacing: { after: 40, line: 276 },
    children: [run(`${label} `, { bold: true }), run(text)],
  });
}

function roleHeader(title, org, dates) {
  return new Paragraph({
    spacing: { before: 160, after: 40 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      run(title, { bold: true, size: 21 }),
      run(`  |  ${org}`, { size: 21, color: ACCENT }),
      run(`\t${dates}`, { size: 19, color: MUTE }),
    ],
  });
}

function subRoleHeader(title, org, dates) {
  return new Paragraph({
    spacing: { before: 100, after: 30 },
    indent: { left: 180 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      run(title, { bold: true }),
      run(`  |  ${org}`, { color: ACCENT }),
      run(`\t${dates}`, { size: 19, color: MUTE }),
    ],
  });
}

const baseStyles = {
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

// ---------------------------------------------------------------------------
// CV
// ---------------------------------------------------------------------------

function buildCv() {
  const header = [
    new Paragraph({
      spacing: { after: 40 },
      children: [run("Clinton Herring", { bold: true, size: 36 })],
    }),
    new Paragraph({
      spacing: { after: 60 },
      children: [
        run("Retail Technology Architect  ·  store infrastructure, standards and supplier governance", {
          size: 22,
          color: ACCENT,
        }),
      ],
    }),
    new Paragraph({
      spacing: { after: 40 },
      border: rule,
      children: [
        run("Almere (near Amsterdam)  ·  +31 6 27517972  ·  Clinton.herring@remoteconsulting.eu  ·  ", {
          size: 18,
          color: MUTE,
        }),
        new ExternalHyperlink({
          link: "https://www.remoteconsulting.eu",
          children: [run("remoteconsulting.eu", { size: 18, color: LINK, underline: {} })],
        }),
      ],
    }),
    body(
      "Dutch residence permit — arbeid vrij toegestaan, TWV niet vereist  ·  ZZP (Remoteconsulting.EU)  ·  Native English",
      { size: 17, italics: true, color: MUTE, before: 60, after: 40 }
    ),
  ];

  const profile = [
    sectionHeading("Profile"),
    body(
      "Retail technology architect with 20+ years in infrastructure: 15 years owning network architecture and third-party vendors at South Africa’s largest private asset manager, then multi-vendor retail store estates with CGI, Suitsupply and the Rituals supplier landscape. I set the standards, lifecycle and designs that keep Meraki networking, iPad POS, payment terminals and back-office devices supportable, and I hold partners to them. Currently a platform engineer at Just Eat Takeaway, where I root-cause production incidents and build AI-assisted tooling that turns recurring operational issues into structural fixes."
    ),
  ];

  const strengths = [
    sectionHeading("Why this role"),
    labelledBullet(
      "Store architecture ownership.",
      "Principles, standards and lifecycle for end-to-end store technology: Meraki networking, iPad POS on NewBlack with a back-room Mac, payment terminals, and the MDM/Jamf layer that keeps Apple store devices managed."
    ),
    labelledBullet(
      "Problem management to structural fix.",
      "Root-cause analysis of production incidents at Just Eat Takeaway (AWS, Kubernetes, DNS and routing, IAM) and 15 years of third-line escalation at Allan Gray; findings fed back into standards and runbooks."
    ),
    labelledBullet(
      "Supplier governance.",
      "15 years managing contractors and vendor contracts; working relationships with several Rituals partners and a clear view of how they fit together (e.g. Veducon network design, CGI with NewBlack for omnichannel, RSG for in-store rollout and break-fix)."
    ),
    labelledBullet(
      "Multi-site retail delivery.",
      "Network architecture for 1000+ stores worldwide and ~150 store hardware deployments project-managed: design, validation, pilot, handover into support."
    ),
    labelledBullet(
      "ITSM in practice.",
      "Jira and Confluence daily; ServiceNow store incident-management model (CGI rollout and training); published research on ITSM metrics and the business value of IT."
    ),
    labelledBullet(
      "Cloud, identity and AI-assisted operations.",
      "Azure (Network Engineer Associate) and AWS since 2016; Entra ID administration for internal users at Just Eat Takeaway; building AI agent tooling that codifies incident investigation and change review."
    ),
  ];

  const experience = [
    sectionHeading("Experience"),

    roleHeader("Independent Consultant", "Remoteconsulting.EU (own ZZP)", "2022 – Present"),
    body(
      "Sole-proprietor vehicle for the engagements below. Also runs own Azure and DigitalOcean monitoring platforms and advises smaller retail, solar and financial-services clients on security maturity (C2M2) and cloud/DC/WAN design under ITSM change control.",
      { after: 40 }
    ),

    subRoleHeader("Platform Engineer", "Just Eat Takeaway", "Nov 2024 – Present"),
    bullet(
      "Platform engineering on an AWS and Kubernetes estate; investigate production incidents by correlating infrastructure changes, Datadog telemetry, pull-request history and AWS CloudTrail to reach a specific root cause."
    ),
    bullet(
      "Built reusable AI agent skills that encode investigation runbooks, incident patterns and change-review checks, so recurring issues are diagnosed faster and fixed structurally rather than repeatedly."
    ),
    bullet(
      "Managed Entra ID for internal users for about a year, until identity (Entra, network access, Okta) was consolidated from separate departments into one."
    ),
    bullet(
      "Review infrastructure changes (DNS, IAM, access) against evidence before closure; Jira and Confluence for documentation and task management every day."
    ),

    subRoleHeader("Principal Architect", "Suitsupply (contracted through CGI)", "2022 – Oct 2024"),
    bullet(
      "Store-technology architecture for an international branded retailer, continuing the CGI store-estate model as a sole proprietor under CGI contract."
    ),
    bullet(
      "Standards, supportability and supplier coordination across store networking and POS-adjacent infrastructure."
    ),

    roleHeader("Principal Architect", "CGI", "2021 – 2022 (8 months)"),
    bullet(
      "With the team, responsible for network architecture across 1000+ retail stores worldwide, primarily Meraki, including POS and payment-terminal connectivity."
    ),
    bullet(
      "Worked inside the Rituals supplier landscape: store operations, the CGI call-centre and support model, and day-to-day coordination with partners such as Veducon."
    ),
    bullet(
      "Part of the team that moved store POS off Cowhills onto NewBlack — iPads on the shop floor with a back-room Mac running POS."
    ),
    bullet(
      "Project-managed network hardware deployments for approximately 150 stores; produced requirements, business cases, scope and technical packs for plan and support teams."
    ),
    bullet(
      "Design and implementation through to structured handover into support; completed CGI’s ServiceNow training when ServiceNow was rolled out to stores for incident management."
    ),

    roleHeader("Infrastructure Architect", "Allan Gray", "2006 – 2021 (15 years)"),
    bullet(
      "Owned network architecture for South Africa’s largest private asset manager: seven offices across South Africa, Botswana and Namibia, ~1500 staff; Cisco core, Radware WAF and load balancing, Raytheon proxy, VMware, Azure and AWS from 2016."
    ),
    bullet(
      "Managed contractors and third-party vendors throughout — contracts, performance and escalation — and set the infrastructure direction and business cases with peers, reporting to the Group Infrastructure Manager."
    ),
    bullet(
      "Translated risk and compliance policy into security controls; monitoring and third-line support for the helpdesk and business departments."
    ),
    bullet(
      "Built an ISP-redundant Cisco AnyConnect VPN in days at the start of the 2020 lockdown so the whole company could work from home; 100% uptime from March 2020."
    ),

    roleHeader("Systems Engineer", "Prudential Portfolio Managers", "2006 (1 year)"),
    bullet(
      "All network infrastructure across three branches — LAN, WAN, IP telephony, mail; replaced the PBX with Asterisk and ISP-managed monitoring with SolarWinds."
    ),

    roleHeader("Systems Engineer", "Abvest", "2001 – 2006"),
    bullet(
      "Networking, security and IT support for a 30-person asset manager; wrote in-house tooling to read PIX firewall syslog for connectivity troubleshooting and ACL management."
    ),
  ];

  const education = [
    sectionHeading("Education, certifications and publication"),
    bullet("BCom (Hons) Information Systems — University of Cape Town"),
    bullet("Cisco Meraki Solutions Specialist  ·  Microsoft Azure Network Engineer Associate"),
    bullet(
      "African Journal of Business Management, 2014 — “An exploratory investigation into using ITSM metrics to indicate the business value of IT in a South African financial services company”"
    ),
  ];

  const additional = [
    sectionHeading("Beyond work"),
    body(
      "Multirotor UAS pilot and builder (commercial RPL, South Africa; registered operator, Netherlands). Building a search-and-rescue computer-vision system on Azure with the DJI platform to help locate lost hikers."
    ),
  ];

  return new Document({
    creator: "Clinton Herring",
    title: "Clinton Herring — Retail Technology Architect CV",
    styles: baseStyles,
    numbering,
    sections: [
      {
        properties: {
          page: { size: A4, margin: { top: 720, right: 760, bottom: 720, left: 760 } },
        },
        children: [...header, ...profile, ...strengths, ...experience, ...education, ...additional],
      },
    ],
  });
}

// ---------------------------------------------------------------------------
// Cover letter
// ---------------------------------------------------------------------------

function buildCoverLetter() {
  const p = (text, opts = {}) =>
    new Paragraph({
      spacing: { after: opts.after ?? 160, line: 276 },
      children: [run(text, { size: 22, bold: !!opts.bold })],
    });

  const paragraphs = [
    p("Clinton Herring", { bold: true, after: 40 }),
    p("Almere  ·  +31 6 27517972  ·  Clinton.herring@remoteconsulting.eu  ·  remoteconsulting.eu", { after: 320 }),
    p("Dear Renée and the Retail Technology team,", { after: 200 }),
    p(
      "I am applying for the Retail Technology IT Architect role. I know the Rituals store landscape from the supplier side, and I have spent the last few years doing exactly the work this role describes: owning store-technology architecture, holding partners to standards, and turning recurring incidents into structural fixes."
    ),
    p(
      "At CGI I worked with the team responsible for network architecture across 1000+ retail stores — Meraki networking, POS and payment terminals, multi-site rollout and handover into support. I was part of the team that moved store POS off Cowhills onto NewBlack, with iPads on the floor and a Mac in the back room. I know how CGI’s call-centre model works with the stores, I have worked with Veducon, and I understand how the wider partner model fits together: Veducon for network design, CGI with NewBlack for omnichannel, RSG for in-store rollout and break-fix. I continued as Principal Architect for Suitsupply under contract with CGI until October 2024."
    ),
    p(
      "Before that I spent 15 years at Allan Gray owning network architecture and managing contractors and third-party vendors for South Africa’s largest private asset manager. That is the muscle this role needs when it asks for architecture principles, lifecycle management and supplier adherence rather than one-off designs."
    ),
    p(
      "Since November 2024 I have been a platform engineer at Just Eat Takeaway. I root-cause production incidents across AWS, Kubernetes, DNS and IAM, and I have built AI agent tooling that codifies those investigations so the same problem is not solved twice. I also managed Entra ID for internal users for about a year, until identity was consolidated into a single department. I use Jira and Confluence every day, and I completed CGI’s ServiceNow training when it was rolled out to stores for incident management. On the Apple side I understand how Jamf and MDM fit an iPad-and-Mac store estate; I would describe that as working knowledge rather than Jamf administration, and I would say so in the interview."
    ),
    p(
      "I live in Almere, close to Amsterdam, so an office-first week is practical. I hold a residence permit with arbeid vrij toegestaan, TWV niet vereist."
    ),
    p("I would welcome the conversation."),
    p("Kind regards,", { after: 200 }),
    p("Clinton Herring", { bold: true, after: 40 }),
    p("+31 6 27517972  ·  Clinton.herring@remoteconsulting.eu", { after: 40 }),
  ];

  return new Document({
    creator: "Clinton Herring",
    title: "Clinton Herring — Rituals cover letter",
    styles: baseStyles,
    numbering,
    sections: [
      {
        properties: {
          page: { size: A4, margin: { top: 1134, right: 1134, bottom: 1134, left: 1134 } },
        },
        children: paragraphs,
      },
    ],
  });
}

// ---------------------------------------------------------------------------

async function main() {
  fs.mkdirSync(ASSETS, { recursive: true });
  fs.writeFileSync(CV_OUT, await Packer.toBuffer(buildCv()));
  console.log("Wrote", CV_OUT);
  fs.writeFileSync(LETTER_OUT, await Packer.toBuffer(buildCoverLetter()));
  console.log("Wrote", LETTER_OUT);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
