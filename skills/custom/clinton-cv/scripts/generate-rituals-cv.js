/**
 * Rituals-tailored CV for Clinton Herring.
 * Run: node generate-rituals-cv.js
 */
const fs = require("fs");
const path = require("path");
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
} = require("/tmp/clinton-cv-build/node_modules/docx");

const OUT = path.join(
  __dirname,
  "..",
  "assets",
  "Clinton_Herring_Rituals_Retail_Tech_Architect_CV.docx"
);

const ink = "1A2332";
const accent = "2C3E50";
const mute = "546E7A";

const thinRule = {
  bottom: { style: BorderStyle.SINGLE, size: 12, color: accent, space: 1 },
};

function sectionHeading(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    border: thinRule,
    spacing: { before: 280, after: 120 },
    children: [
      new TextRun({
        text: text.toUpperCase(),
        bold: true,
        size: 20,
        font: "Calibri",
        color: accent,
        characterSpacing: 60,
      }),
    ],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { after: opts.after ?? 80, before: opts.before ?? 0, line: 276 },
    children: [
      new TextRun({
        text,
        size: 20,
        font: "Calibri",
        color: ink,
      }),
    ],
  });
}

function bullet(text, ref = "cv-bullets") {
  return new Paragraph({
    numbering: { reference: ref, level: 0 },
    spacing: { after: 40, line: 276 },
    children: [
      new TextRun({ text, size: 20, font: "Calibri", color: ink }),
    ],
  });
}

function roleHeader(title, org, dates) {
  return new Paragraph({
    spacing: { before: 160, after: 40 },
    tabStops: [{ type: TabStopType.RIGHT, position: TabStopPosition.MAX }],
    children: [
      new TextRun({ text: title, bold: true, size: 21, font: "Calibri", color: ink }),
      new TextRun({ text: `  |  ${org}`, size: 21, font: "Calibri", color: accent }),
      new TextRun({ text: `\t${dates}`, size: 19, font: "Calibri", color: mute }),
    ],
  });
}

const doc = new Document({
  styles: {
    default: {
      document: {
        run: { font: "Calibri", size: 20, color: ink },
      },
    },
    paragraphStyles: [
      {
        id: "Heading1",
        name: "Heading 1",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 20, bold: true, font: "Calibri", color: accent },
        paragraph: { spacing: { before: 280, after: 120 }, outlineLevel: 0 },
      },
      {
        id: "Heading2",
        name: "Heading 2",
        basedOn: "Normal",
        next: "Normal",
        quickFormat: true,
        run: { size: 21, bold: true, font: "Calibri", color: ink },
        paragraph: { spacing: { before: 160, after: 40 }, outlineLevel: 1 },
      },
    ],
  },
  numbering: {
    config: [
      {
        reference: "cv-bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: { indent: { left: 360, hanging: 180 } },
            },
          },
        ],
      },
      {
        reference: "skill-bullets",
        levels: [
          {
            level: 0,
            format: LevelFormat.BULLET,
            text: "•",
            alignment: AlignmentType.LEFT,
            style: {
              paragraph: { indent: { left: 360, hanging: 180 } },
            },
          },
        ],
      },
    ],
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 11906, height: 16838 }, // A4
          margin: { top: 720, right: 720, bottom: 720, left: 720 },
        },
      },
      children: [
        // Header
        new Paragraph({
          alignment: AlignmentType.LEFT,
          spacing: { after: 40 },
          children: [
            new TextRun({
              text: "Clinton Herring",
              bold: true,
              size: 36,
              font: "Calibri",
              color: ink,
            }),
          ],
        }),
        new Paragraph({
          spacing: { after: 60 },
          children: [
            new TextRun({
              text: "Retail Technology Architect  ·  Store Infrastructure & Operations",
              size: 22,
              font: "Calibri",
              color: accent,
            }),
          ],
        }),
        new Paragraph({
          spacing: { after: 40 },
          border: thinRule,
          children: [
            new TextRun({ text: "Enschede, Netherlands  ·  ", size: 18, font: "Calibri", color: mute }),
            new TextRun({ text: "+31 6 27517972  ·  ", size: 18, font: "Calibri", color: mute }),
            new TextRun({ text: "Clinton.herring@remoteconsulting.eu  ·  ", size: 18, font: "Calibri", color: mute }),
            new ExternalHyperlink({
              link: "https://www.remoteconsulting.eu",
              children: [
                new TextRun({
                  text: "remoteconsulting.eu",
                  size: 18,
                  font: "Calibri",
                  color: "2B579A",
                  underline: {},
                }),
              ],
            }),
          ],
        }),
        new Paragraph({
          spacing: { before: 80, after: 40 },
          children: [
            new TextRun({
              text: "NL residence permit: Arbeid vrij toegestaan, TWV niet vereist  ·  ZZP (Remoteconsulting.EU)  ·  Native English",
              size: 17,
              font: "Calibri",
              color: mute,
              italics: true,
            }),
          ],
        }),

        sectionHeading("Profile"),
        body(
          "Retail technology architect with Principal Architect experience for large multi-country store estates. At CGI I worked with the team responsible for network and store connectivity across 1000+ retail locations (Meraki, POS, payment terminals) and operated inside the Rituals supplier landscape — store operations, CGI’s support/call-centre model, and providers such as Veducon. I was involved with the team that moved store POS off Cowhills onto the NewBlack stack (iPad POS with a back-room Mac). Since then I have done similar retail architecture for Suitsupply and platform engineering with Just Eat Takeaway, including AI-assisted ways of running and improving operations. I translate store pain into standards, lifecycle plans, and supportable designs."
        ),

        sectionHeading("Selected strengths for this role"),
        bullet("Architectural ownership of end-to-end store technology: networking, POS, payment terminals, and supplier interfaces", "skill-bullets"),
        bullet("Meraki and Cisco store networking; multi-site rollout, validation, and handover into support", "skill-bullets"),
        bullet("Retail POS landscape literacy: iPad POS, NewBlack, Cowhills migration, back-room Mac pattern; how Jamf/MDM fits Apple store devices (ecosystem knowledge — not a Jamf specialist)", "skill-bullets"),
        bullet("Technology lifecycle, standardisation, and working with outsourced partners (CGI, Veducon, and peer providers)", "skill-bullets"),
        bullet("ITSM-minded design and change documentation; published research on ITSM metrics and business value of IT", "skill-bullets"),
        bullet("Platform engineering at Just Eat Takeaway; practical ideas to move store tech toward proactive / AI-assisted operations", "skill-bullets"),
        bullet("Azure networking (Azure Network Engineer Associate); cloud and hybrid infrastructure since 2016", "skill-bullets"),

        sectionHeading("Experience"),

        roleHeader("Principal Architect / Platform Engineer", "Remoteconsulting.EU", "2022 – Present"),
        bullet("Advise retailers and other clients on architecture, processes, and implementation of network and store-related infrastructure across Europe, the UK, and South Africa."),
        bullet("Retail architecture engagement with Suitsupply — similar store-technology ownership pattern to large branded retail (standards, supportability, supplier coordination)."),
        bullet("Platform engineering with Just Eat Takeaway; apply an AI-informed, continuous-improvement mindset to reliability and operational signal — relevant to Rituals’ move toward proactive and predictive technology management."),
        bullet("Produce design documentation for cloud, DC, and WAN change under ITSM/governance expectations; advise on security maturity (C2M2)."),
        bullet("Operate own Azure and DigitalOcean platforms for client hosting and monitoring; work with stakeholders from small teams to 30+ person support organisations."),

        roleHeader("Principal Architect", "CGI", "2021 – 2022 (8 months)"),
        bullet("With the team, responsible for network architecture supporting 1000+ retail stores worldwide, primarily Meraki, including POS and payment-terminal connectivity."),
        bullet("Rituals supplier-side experience: store operations realities, CGI call-centre / support model, and direct dealings with Veducon."),
        bullet("Involved with the team that swapped store POS from Cowhills to the NewBlack-oriented model (iPads on the shop floor; Mac in the back room running POS)."),
        bullet("Project-managed network hardware deployments for approximately 150 stores; captured requirements, business cases, scope, and technical packs for plan and support teams."),
        bullet("Full lifecycle focus on design and implementation, then structured handover to support — standardisation and supportability over one-off builds."),

        roleHeader("Infrastructure Architect", "Allan Gray", "2006 – 2021 (15 years)"),
        bullet("Owned networking for South Africa’s largest private asset manager (~7 Southern African offices, ~1500 staff): Cisco core, WAF/load balancing, proxy, VMware, Azure and AWS from 2016."),
        bullet("Translated risk/compliance policy into security systems; vendor contract management, monitoring, and third-line support — architecture that operations can run."),

        roleHeader("Systems Engineer", "Prudential Portfolio Managers", "2006 (1 year)"),
        bullet("LAN, WAN, IP telephony, and mail across three branches; delivered Asterisk IP-PBX replacement and SolarWinds monitoring."),

        roleHeader("Systems Engineer", "Abvest", "2001 – 2006"),
        bullet("Networking, security, and IT support for a Cape Town asset manager; built tooling to use PIX firewall syslog for connectivity troubleshooting and ACL management."),

        sectionHeading("Education & certifications"),
        bullet("BCom (Hons) Information Systems — University of Cape Town"),
        bullet("Cisco Meraki Solutions Specialist"),
        bullet("Microsoft Azure Network Engineer Associate"),
        bullet("Publication: African Journal of Business Management, 2014 — “An exploratory investigation into using ITSM metrics to indicate the business value of IT in a South African financial services company”"),

        sectionHeading("Additional"),
        body(
          "UAS pilot and builder (commercial RPL South Africa; NL operator). Developing SAR computer-vision work on Azure with the DJI platform — evidence of applied AI interest outside core retail delivery."
        ),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buffer) => {
  fs.mkdirSync(path.dirname(OUT), { recursive: true });
  fs.writeFileSync(OUT, buffer);
  console.log("Wrote", OUT);
});
