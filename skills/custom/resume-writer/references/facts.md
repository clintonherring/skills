# Facts — Clinton Herring

Canonical fact base for every CV, résumé, cover letter and LinkedIn text. Pulled from the original CV (`Clinton Herring NL ENT ARCH CV.docx`), the Rituals CV produced in October 2026, and Clinton's corrections in chat. Use these values as they are. If a fact is not here, do not write it; ask Clinton or leave it out.

Each role has a **Brain dump** block (Result / What I did / How) in rough first-person notes, which is the raw material for bullets, and a **Numbers I can use** list. Numbers not listed do not exist; do not estimate them.

## Identity

| Field | Value |
|-------|-------|
| Name | Clinton Herring |
| Headline (general) | Enterprise Architect, Operational Security Specialist |
| Headline (retail roles) | Retail Technology Architect · store infrastructure, standards and vendor management |
| Location | Almere, Netherlands (near Amsterdam). Not Enschede (old CV). |
| Phone | +31 6 27517972 (0627517972) |
| Email | Clinton.herring@remoteconsulting.eu |
| Web | https://www.remoteconsulting.eu |
| Portfolio | None to link. The skills repo is **not** to be used as a portfolio or linked on a CV (Clinton's instruction). |
| Work status | Dutch residence permit, *Arbeid vrij toegestaan, TWV niet vereist* |
| Legal form | ZZP (sole proprietor), trading as Remoteconsulting.EU |
| Language | Native English |
| Office | Lives close to Amsterdam; being in an office most of the week is practical |

## Tenure

- More than 20 years in infrastructure (2001 – present); "20+ years" is fine on a CV
- 15 years at Allan Gray

## Career timeline (newest first)

| Period | Title | Organisation | How engaged |
|--------|-------|--------------|-------------|
| Nov 2024 – present | Platform Engineer | Just Eat Takeaway | Via ZZP / Remoteconsulting.EU |
| 2022 – 16 Oct 2024 | Principal Architect | Suitsupply, as sub-contractor to CGI | Self-employed; most of the period was this sub-contract. Other own-client work alongside. |
| 2021 – 2022 (8 months) | Principal Architect | CGI | Staff engagement; Rituals was the customer landscape |
| 2006 – 2021 (15 years) | Infrastructure Architect | Allan Gray | Employee |
| 2006 (1 year) | Systems Engineer | Prudential Portfolio Managers | Employee |
| 2001 – 2006 | Systems Engineer | Abvest | Employee |

Presentation rules (Clinton's decisions):

- Lead with Just Eat Takeaway as a top-level entry.
- 2022 – Oct 2024 is **one** entry titled Principal Architect — Suitsupply, as sub-contractor to CGI. Its intro sentence says he worked for himself and that Suitsupply was most of the work. Do not add a separate "Self-employed 2022 – present" row and do not show two "present" roles.
- Suitsupply matters because it is a **second retailer**: retail expertise is not based on Rituals alone.
- Spell it Principal; the old CV misspelled the title.

## Roles

### Platform Engineer — Just Eat Takeaway (Nov 2024 – present)

Brain dump:

- Result: production incidents get a clear root cause instead of a guess (problem management: find the cause, then make sure the fix goes into the standard, not just the ticket), and the way we investigate is written down as reusable AI agent skills so the next person does not start from scratch.
- What I did: I work on an AWS and Kubernetes platform. When there is a production incident I trace it through infrastructure changes, Datadog, pull requests and CloudTrail. I review infrastructure changes (DNS, IAM, access) before tickets are closed. I built AI agent skills for incident investigation and ticket review. I managed Entra ID for internal users for about a year until identity (Entra, network access, Okta) was brought together under one department.
- How: Jira and Confluence every day for documentation and task management. Evidence of the AI work is in this repo: `skills/custom/jet-pi-troubleshooter` (correlates Jira timeline, Datadog, GitHub PR history, AWS CloudTrail/Route53, Wiz; worked examples: IAM/ABAC auth, RDS IAM auth, DNS weighted-routing 404s, S3 replication tracing) and `skills/custom/ticket-reviewer` (checks DNS changes, GitHub permissions, change monitoring against independent evidence).

Numbers I can use: about one year on Entra ID. Nothing else (no incident counts, MTTR, team size or product names). Clinton confirmed the JET bullets are accurate and shareable.

### Principal Architect — Suitsupply, as sub-contractor to CGI (2022 – Oct 2024)

Brain dump:

- Result: a second international retailer where I did the same kind of store technology architecture work as at CGI.
- What I did: standards, supportability and coordinating suppliers across store networking and the infrastructure around POS. Alongside that I advised smaller retail, solar and financial services clients (Europe, UK, South Africa) on design, monitoring and security maturity (C2M2), and kept their infrastructure documentation for governance and compliance.
- How: I ran my own Azure and Digital Ocean infrastructure to host and monitor for clients. I worked with client teams from small groups to 30+ person support teams, and with business, application, engineering and support stakeholders.

Numbers I can use: ended 16 October 2024; client support teams of 30+. No Suitsupply store counts.

### Principal Architect — CGI (2021 – 2022, 8 months)

Brain dump:

- Result: 1000+ Rituals stores worldwide kept on a supportable Meraki network standard, and about 150 stores got new network hardware on my project plans.
- What I did: With my fellow team members I was responsible for network architecture across 1000+ retail stores, primarily Meraki, with POS and payment terminals connecting to it. I project managed network hardware deployments for approximately 150 stores worldwide. I captured business requirements and wrote business cases, project scope and technical documents for the plan and support teams. I was part of the team that replaced Cowhills with NewBlack POS (iPads on the shop floor, a Mac in the back room running the POS stack). I did CGI's ServiceNow training when ServiceNow was rolled out to the stores for incident management.
- How: The work ran across the full lifecycle of the network infrastructure we were responsible for (lifecycle management from requirements to handover). Most of it was design and implementation with handover to the support teams after. I worked day to day with the Rituals partners: the CGI call centre and support model, Veducon on network design, RSG in the stores.

Numbers I can use: 1000+ stores (team responsibility), approximately 150 stores (my rollouts), 8 months.

Rituals landscape knowledge (supplier side, never employment): iPad POS; back-room Mac runs NewBlack; Cowhills was the previous POS; vendor map as Clinton understands it — Veducon = network expertise and design, CGI = omnichannel via NewBlack, RSG = in-store changes, rollouts and break-fix. Jamf/MDM: knows how it fits an iPad-and-Mac store estate; **no Jamf certification or administration claim**. ServiceNow: peripheral involvement plus CGI training; **not an implementer or admin**.

### Infrastructure Architect — Allan Gray (2006 – 2021, 15 years)

Brain dump:

- Result: the network for the largest private asset manager in South Africa ran across 7 offices in 3 countries for 15 years, and when lockdown hit in March 2020 the whole company could work from home within days on a VPN that has had 100% uptime since.
- What I did: I was responsible for the networking infrastructure. I advised on the direction for IT infrastructure and built business cases with my peers. I managed the 3rd party vendors and contractors for the full 15 years: contracts, performance, escalations. I implemented security systems based on policy from risk and compliance. I did monitoring, troubleshooting and 3rd line support for the helpdesk and other departments. I built the ISP redundant Cisco AnyConnect VPN at the start of lockdown. We moved physical infrastructure DC to DC and then started moving workloads to Azure and AWS in 2016.
- How: Cisco core, Radware WAF and load balancing, Raytheon proxy and filtering, VMware, Azure and AWS. Reported to the Group Infrastructure Manager. Head office Cape Town; branches in South Africa, Botswana, Namibia.

Numbers I can use: 15 years; 7 offices; 3 countries; about 1500 employees; 100% VPN uptime since March 2020; cloud moves since 2016. LinkedIn post on the VPN: https://www.linkedin.com/feed/update/urn:li:activity:6653391138659020800/

### Systems Engineer — Prudential Portfolio Managers (2006, 1 year)

Brain dump: I was responsible for all network infrastructure (LAN, WAN, IP telephony, mail) across 3 branches, head office Cape Town, reporting to the head of IT. My largest project was replacing the traditional PBX with an Asterisk IP telephony system. I brought monitoring in-house with SolarWinds, replacing the ISP-managed system.

Numbers I can use: 3 branches.

### Systems Engineer — Abvest (2001 – 2006)

Brain dump: Networking, security and IT support for a small asset manager of about 30 people in one Cape Town office. I wrote an in-house system to read syslog from our PIX firewall to troubleshoot internet connectivity and manage ACLs.

Numbers I can use: about 30 people.

## Skills (only these)

| Group | Items |
|-------|-------|
| Store / retail technology | Cisco Meraki (CMSS certified), iPad POS on NewBlack, payment terminals, back-office Macs, MDM/Jamf (how it fits the estate), multi-site rollouts, handover to support |
| Network and security | Cisco (NGFW, VPN, AnyConnect, proxy, load balancer, WAF), Radware, Raytheon, WAN and data centre design, operational security, C2M2 |
| Cloud and platform | Azure (Network Engineer Associate), AWS (Certified Solutions Architect – Associate), Kubernetes, Datadog, CloudTrail, VMware, Digital Ocean |
| Identity | Entra ID administration for internal users (about a year, JET). Not identity architecture ownership; not Okta admin. |
| Ways of working | ITIL / ITSM, Jira, Confluence, ServiceNow (store incident management, CGI training), vendor and contract management, business cases, project and design documentation, stakeholder work across business, application, engineering and support |
| AI | Builds AI agent skills (Cursor) for incident investigation and change review. Do not link the skills repo. |
| Older / historical | Asterisk, SolarWinds, Cisco PIX |

## Education, certifications, publication

- BCom (Hons) Information Systems, University of Cape Town — a postgraduate (honours) degree; Clinton describes it as "a post graduate degree in information systems from UCT"

Certifications Clinton holds and **maintains (current)**:

- Microsoft Azure Network Engineer Associate
- Cisco Meraki Solutions Specialist (CMSS)
- AWS Certified Solutions Architect – Associate
- African Journal of Business Management, 2014: "An exploratory investigation into using ITSM metrics to indicate the business value of IT in a South African financial services company" (also on academia.edu)

Not held (do not add): Jamf 200/300, CCNA/CCNP, CISSP, TOGAF, ITIL certificate, ServiceNow certs.

## AI proof points (for rule 5 — prove, do not list)

- Wrote reusable AI agent skills at JET that capture how incidents are investigated and tickets reviewed: `jet-pi-troubleshooter`, `ticket-reviewer` (this repo).
- No portfolio link. Do not reference or link the skills repository on a CV or in a letter; describe the AI work in words and offer to walk through it in an interview.
- Has ideas for making an architect role AI-led (proactive and predictive operations from operational signal). Keep as a mindset line unless Clinton supplies specifics.
- Personal project: search-and-rescue vision app with the DJI platform to help find lost hikers, running in Docker on a VPS (not Azure; Azure hosts ZZP infrastructure, a separate thing).

## Personal

- Flies and builds multirotor UAS; commercial RPL (South Africa); registered operator (Netherlands); keen hiker.
- Frequently recognised as a top performer among peers (no named award on file).
- Intrinsically motivated; works well in a collegiate team.

## Open metric questions for Clinton (ask before drafting; move answers into the role brain dumps)

- CGI: the ~150-store rollout — over how many months, how many countries, on schedule or not, stores per week at peak?
- CGI: Cowhills → NewBlack — how many stores migrated during your time, over what period, any downtime figure?
- JET: AI agent skills — how long did an incident investigation take before versus with the skill; how many incidents or tickets has it been used on; how many engineers use it?
- JET: Entra ID — roughly how many internal users?
- Suitsupply: how many stores or countries; what did you deliver (a standard, a design, a rollout) and what did it change?
- Allan Gray: how many vendors or contracts did you manage; rough annual value; any SLA or renegotiation result?
- Allan Gray: the lockdown VPN — how many days to build; how many users did it carry? (Your LinkedIn post from April 2020 may say.)
- Allan Gray: cloud moves — how many workloads or what share of the estate moved to Azure/AWS?

## Numbers I do not have

Do not invent or estimate: revenue, budgets, cost savings, incident counts, MTTR, ticket volumes, team sizes at JET or CGI, Suitsupply store counts, uptime figures other than the VPN, customer satisfaction scores. If a JD wants a number here, ask Clinton for it before writing it.
