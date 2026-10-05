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
    keepNext: true,
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
    keepNext: !!opts.keepNext,
    keepLines: true,
    spacing: { after: opts.after ?? 80, before: opts.before ?? 0, line: 276 },
    children: [run(text, { size: opts.size ?? 20, italics: !!opts.italics, color: opts.color ?? INK })],
  });
}

function bullet(text) {
  return new Paragraph({
    numbering: { reference: "cv-bullets", level: 0 },
    spacing: { after: 60, line: 276 },
    children: [run(text)],
  });
}

function labelledBullet(label, text) {
  return new Paragraph({
    numbering: { reference: "cv-bullets", level: 0 },
    spacing: { after: 70, line: 276 },
    children: [run(`${label}  `, { bold: true, color: ACCENT }), run(text)],
  });
}

function skillLine(label, text) {
  return new Paragraph({
    spacing: { after: 50, line: 276 },
    indent: { left: 1700, hanging: 1700 },
    tabStops: [{ type: TabStopType.LEFT, position: 1700 }],
    children: [run(label, { bold: true, color: ACCENT }), run(`\t${text}`)],
  });
}

function roleHeader(title, org, dates) {
  return new Paragraph({
    keepNext: true,
    spacing: { before: 160, after: 40 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      run(title, { bold: true, size: 21 }),
      run(`  |  ${org}`, { size: 21, color: ACCENT }),
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
        run("Retail Technology Architect  ·  store infrastructure, standards and vendor management", {
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
      "I design, secure and maintain enterprise and retail store infrastructure, with more than 20 years experience aligning IT infrastructure with business needs. I spent 15 years at Allan Gray, the largest private asset manager in South Africa, and since 2021 I have worked in retail: at CGI on the Rituals store estate and then for Suitsupply as a sub-contractor to CGI, so I know the Rituals store environment from the supplier side. Since November 2024 I have been a platform engineer at Just Eat Takeaway, finding the root cause of production incidents and building AI tooling to do that faster.",
      { after: 60 }
    ),
  ];

  const strengths = [
    sectionHeading("In short"),
    labelledBullet(
      "Store technology",
      "I know the Rituals store setup: Meraki networks, iPad POS on NewBlack with a Mac in the back room, payment terminals, and the partners behind it."
    ),
    labelledBullet(
      "Rollouts",
      "At CGI I project managed Meraki rollouts to around 150 stores and helped look after a 1000+ store estate."
    ),
    labelledBullet(
      "Vendors",
      "I managed 3rd party vendors and contractors for 15 years at Allan Gray and know several of the Rituals partners."
    ),
    labelledBullet(
      "Problem management",
      "At Just Eat Takeaway I find the root cause of production incidents and make sure the fix goes into the standard, not just the ticket."
    ),
    labelledBullet(
      "Tools",
      "Jira and Confluence every day. ServiceNow from the CGI store rollout. Entra ID for a year at Just Eat Takeaway. Azure and AWS since 2016."
    ),
    labelledBullet(
      "AI",
      "I build AI agent tooling for incident investigation and change review, and I have ideas on how to use it in this role."
    ),
  ];

  const skills = [
    sectionHeading("Skills"),
    skillLine(
      "Store technology",
      "Cisco Meraki (certified), iPad POS on NewBlack, payment terminals, back-office Macs, MDM/Jamf (how it fits the estate), multi-site rollouts"
    ),
    skillLine("Network & security", "Cisco, NGFW, VPN, proxy, load balancer, WAF, WAN and data centre design, operational security"),
    skillLine("Cloud & identity", "Azure (Network Engineer Associate), AWS, Kubernetes, Entra ID, Datadog"),
    skillLine(
      "Ways of working",
      "ITIL / ITSM, Jira, Confluence, ServiceNow (store incident management), vendor and contract management, business cases and project documentation, C2M2 security maturity"
    ),
  ];

  const experience = [
    sectionHeading("Experience"),

    roleHeader("Platform Engineer", "Just Eat Takeaway", "Nov 2024 – Present"),
    bullet(
      "I work on an AWS and Kubernetes platform. When there is a production incident I trace it through infrastructure changes, Datadog, pull requests and CloudTrail until I have a clear root cause."
    ),
    bullet(
      "I built reusable AI agent skills that capture how we investigate incidents and review changes, so the next person does not start from scratch."
    ),
    bullet(
      "I managed Entra ID for internal users for about a year, until identity (Entra, network access and Okta) was brought together under one department."
    ),
    bullet(
      "I review infrastructure changes (DNS, IAM, access) before they are closed, and I use Jira and Confluence every day for documentation and task management."
    ),

    roleHeader("Principal Architect", "Suitsupply, as sub-contractor to CGI", "2022 – Oct 2024"),
    body(
      "I worked for myself as a sole proprietor (ZZP, Remoteconsulting.EU), mostly as a sub-contractor to CGI for Suitsupply. Alongside that I advised smaller retail, solar and financial services clients on design, monitoring and security maturity (C2M2) from my own Azure and Digital Ocean infrastructure.",
      { after: 40, keepNext: true }
    ),
    bullet(
      "Store technology architecture for Suitsupply, a second international retailer, so my retail experience is not based on Rituals alone."
    ),
    bullet(
      "The same kind of work as at CGI: standards, supportability and coordinating suppliers across store networking and the infrastructure around POS."
    ),

    roleHeader("Principal Architect", "CGI", "2021 – 2022 (8 months)"),
    body(
      "With my fellow team members I was responsible for 1000+ retail stores worldwide, primarily on Meraki network infrastructure with POS and payment terminals connecting to it. Most of the work was design and implementation, with handover to the support teams after.",
      { after: 40, keepNext: true }
    ),
    bullet("I project managed network hardware deployments for approximately 150 stores worldwide."),
    bullet(
      "I was part of the team that replaced Cowhills with NewBlack POS: iPads on the shop floor with a Mac in the back room."
    ),
    bullet(
      "I worked day to day with the Rituals partners: the CGI call centre and support model, Veducon on network design, and RSG in the stores."
    ),
    bullet(
      "I captured business requirements and wrote business cases, project scope and technical documents for the plan and support teams."
    ),
    bullet("I did CGI’s ServiceNow training when ServiceNow was rolled out to the stores for incident management."),

    roleHeader("Infrastructure Architect", "Allan Gray", "2006 – 2021 (15 years)"),
    body(
      "I was responsible for the networking infrastructure at the largest private asset management company in South Africa: 7 offices in South Africa, Botswana and Namibia and about 1500 employees. I reported to the Group Infrastructure Manager.",
      { after: 40, keepNext: true }
    ),
    bullet("I advised on the direction for IT infrastructure and built business cases for projects with my peers."),
    bullet("I managed the 3rd party vendors and contractors for the full 15 years: contracts, performance and escalations."),
    bullet(
      "I implemented security systems based on policy from risk and compliance. Cisco core, Radware WAF and load balancing, Raytheon proxy, VMware, with Azure and AWS from 2016."
    ),
    bullet("I did monitoring, troubleshooting and 3rd line support for the helpdesk and other departments."),
    bullet(
      "At the start of the 2020 lockdown I built an ISP redundant Cisco AnyConnect VPN in a very short time so everyone could work from home. It has had 100% uptime since March 2020."
    ),

    roleHeader("Systems Engineer", "Prudential Portfolio Managers", "2006 (1 year)"),
    bullet(
      "I was responsible for all network infrastructure (LAN, WAN, IP telephony and mail) across 3 branches. I replaced the PBX with an Asterisk IP telephony system and brought monitoring in-house with SolarWinds."
    ),

    roleHeader("Systems Engineer", "Abvest", "2001 – 2006"),
    bullet(
      "Networking, security and IT support for a small asset manager of about 30 people. I wrote an in-house system to read syslog from our PIX firewall to troubleshoot connectivity and manage ACLs."
    ),
  ];

  const education = [
    sectionHeading("Education, certifications and publication"),
    bullet("BCom (Hons) Information Systems, University of Cape Town"),
    bullet("Cisco Meraki Solutions Specialist  ·  Microsoft Azure Network Engineer Associate"),
    bullet(
      "African Journal of Business Management, 2014: “An exploratory investigation into using ITSM metrics to indicate the business value of IT in a South African financial services company”"
    ),
  ];

  const additional = [
    sectionHeading("Beyond work"),
    body(
      "I fly and build multirotor UAS (commercial RPL in South Africa, registered operator in NL). I am a keen hiker and am building a search and rescue vision app, running in Docker on a VPS, that works with the DJI platform to help find lost hikers."
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
        children: [...header, ...profile, ...strengths, ...skills, ...experience, ...education, ...additional],
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
      "I am applying for the Retail Technology IT Architect role. I know the Rituals store environment from the supplier side, and the work in this role is the work I have been doing for the last few years: store technology architecture, keeping partners to the standards, and making sure that when something breaks the fix goes into the standard and not just the ticket."
    ),
    p(
      "At CGI I was part of the team responsible for network architecture across 1000+ Rituals stores: Meraki networking, POS and payment terminals, rollouts to many stores at once and handover to support. I was part of the team that replaced Cowhills with NewBlack POS, with iPads on the floor and a Mac in the back room. I know how the CGI call centre works with the stores, I have worked with Veducon, and I know how the partners fit together: Veducon for network design, CGI with NewBlack for omnichannel, RSG for rollouts and break-fix in the stores. From 2022 to October 2024 I worked for myself, and most of that was as a sub-contractor to CGI for another retailer, Suitsupply, so my retail experience is not based on one brand."
    ),
    p(
      "Before that I spent 15 years at Allan Gray, the largest private asset manager in South Africa, where I was responsible for the network architecture and managed the 3rd party vendors and contractors. That is where I learned to set architecture principles, manage the lifecycle of infrastructure and hold suppliers to what they agreed to, rather than doing one-off designs."
    ),
    p(
      "Since November 2024 I have been a platform engineer at Just Eat Takeaway. I find the root cause of production incidents across AWS, Kubernetes, DNS and IAM, and I have built AI agent tooling that captures how we investigate so the same problem does not get solved twice. I also managed Entra ID for internal users for about a year, until identity was brought together under one department. I use Jira and Confluence every day, and I did CGI’s ServiceNow training when it was rolled out to the stores for incident management. On the Apple side I know how Jamf and MDM fit an iPad and Mac store estate; I would call that working knowledge rather than Jamf administration, and I would say so in the interview."
    ),
    p(
      "I live in Almere, close to Amsterdam, so being in the office most of the week is practical. I have a residence permit with arbeid vrij toegestaan, TWV niet vereist."
    ),
    p("I would welcome the chance to talk about the role."),
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
