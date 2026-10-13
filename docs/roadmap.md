# Commonstead portfolio roadmap

Research snapshot: 2026-10-12. Full Salesforce-portfolio outcomes remain the long-term scope. The initial CRM increment is a deliberately narrow working release and must never be described as a full replacement. This roadmap assigns every inventory row and every included alias to a dependency phase; phases are an ordering proposal, not dates or a promise of unattended work.

## Status rules

Use only `researched`, `planned`, `in progress`, `partial`, `verified`, or `blocked`. Research status and implementation status are separate: a publicly documented product may be researched while its Commonstead equivalent is planned. The portfolio CSV is a scope inventory. The implementation coverage matrix and actual test results govern release claims. A product family can remain partial even when one narrow workflow is verified. No percentage of portfolio completion is meaningful without a stable denominator and independent acceptance review.

A capability becomes **verified** only after it has real persistence, permission and tenant checks, useful failure handling, a user-visible outcome and linked test evidence. Tests must include authorized business flow, unauthorized/cross-tenant attempts, migration from the preceding release, restart/retry behavior when relevant and clean installation. An integration needs a separately labeled live authorized integration result; mocks are not that evidence. Every release records measured test results and any performance measurement's environment, data size and limitations.

## Dependency order and release gates

### R1 — Complete first CRM workflow

Local org registration, cookie sessions, owner/admin/member/viewer roles, invitation redemption, CSV contact import, accounts, lead management, opportunity stages, assigned activities and a reconciled report. The bounded CRM workflow is verified locally in0.1.0; lead conversion and advanced Sales Cloud outcomes remain planned. See the implementation coverage matrix for actual evidence.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| C01 | Sales Cloud | Agentforce Sales naming appears in official Help; Sales Data; Sales Analytics (advanced analytics tracked A03). | partial |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R2 — Strengthen shared platform

Custom fields/objects, permission-safe search and files, durable jobs/events, versioned workflow/rules, backup/restore, audit and scoped integration APIs. Reassess stdlib HTTP/auth and SQLite before untrusted network or larger multi-tenant deployment.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| I01 | MuleSoft Anypoint Platform | Anypoint Exchange; Code Builder; API Manager; API Governance; API Experience Hub; CloudHub; Runtime Fabric; Mule Runtime; Object Store v2; Anypoint MQ. | planned |
| I02 | MuleSoft for Flow / Composer | MuleSoft for Flow: Integration; Composer moving to end of sale per current docs; adapters are replaceable. | planned |
| P01 | Platform data, identity and access | Salesforce Platform; Lightning Platform; Identity; custom objects/fields; files; search; import/export; Salesforce Connect federation requires deeper research. | partial |
| P02 | Platform API and event services | Platform Events; Change Data Capture; Metadata API; reports API; no SOQL/Apex or Salesforce protocol compatibility in R1. | planned |
| P03 | Flow and orchestration | Flow Builder; Flow Orchestration; approvals; Action Launcher; Action Plans; Stage Management; Record Alerts; Timeline. | planned |
| P04 | Shield and Security Center | Platform Encryption; Event Monitoring; Field Audit Trail; Data Detect; Security Center; Compliant Data Sharing and Identity Verification tracked T03. | planned |
| P05 | Privacy Center and Own data protection | OwnBackup / Own Company; Backup & Recover; Archive; Data Mask & Seed; Salesforce Discover/Accelerate need deeper feature survey. Archive Console; Salesforce Discover; Salesforce Accelerate named in support terms; exact behavior remains unknown. | planned |
| T01 | Omnistudio and guided processes | OmniScripts; FlexCards; Integration Procedures; DataRaptors/Data Mappers require deeper parity study; Omnistudio Installation and Upgrade; Form Framework; Discovery Framework and Assessments. | planned |
| T02 | Business Rules Engine and data processing | Decision Tables; Batch Management; Data Processing Engine; Rollup Definitions; CSV Data Management. | planned |
| T03 | Compliant sharing and customer verification | Compliant Data Sharing; Identity Verification; baseline org roles alone are not equivalent. | planned |
| T05 | Relationships, context and record history | Actionable Relationship Center; Group Membership; Interest Tags; Context Service; Criteria-Based Search and Filter; Data Consumption Framework; Cross-Object Field History; Timeline. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R3 — Customer service and portals

Persistent cases/queues, knowledge, SLA timers, customer portals, scheduling and basic channel adapters. Implement one end-to-end customer request before adding media integrations.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| C09 | Starter Suite / Pro Suite / Foundations | Small Business; Salesforce Foundations; Agentforce Foundations; Foundation Suites; Customer 360 is an outcome/portfolio umbrella, not a separate product. | planned |
| S01 | Service Cloud | Customer Service Management; Self-Service; Knowledge; incident management; AI role variants are extensions in X01. | planned |
| S02 | Contact Center and Digital Channels | Service Cloud Voice; Digital Engagement; CCaaS integrations; Workforce Engagement Management; Engagement industries templates. | planned |
| S07 | Salesforce Scheduler and Virtual Calls | No separate aliases identified in this pass. | planned |
| P06 | Experience Cloud and Salesforce CMS | Experience Builder; Communities historical name; Site.com; original UI and no copied templates. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R4 — Consent-led marketing and content

Versioned content, audiences, suppression, campaigns and nurture; local spool/test adapter as default. Real delivery requires configured replaceable provider and authorized launch.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| C02 | Sales Engagement and Buyer Engagement | No separate aliases identified in this pass. Salesforce Inbox; Outlook/Gmail integrations; Einstein Activity Capture (mailbox synchronization behavior needs deeper research). | planned |
| C03 | Sales Programs | No separate aliases identified in this pass. | planned |
| S06 | Feedback Management | No separate aliases identified in this pass. | planned |
| M01 | Marketing Cloud Next | Agentforce Marketing naming; Campaign Agent; B2B/B2C agentic marketing umbrella; Small Business Marketing maps C09. | planned |
| M02 | Marketing Cloud Engagement | MCE; SFMC; former generic Marketing Cloud label; Marketing Cloud Engagement for Industries and Nonprofits. ExactTarget historical acquisition completed 2013-07-12. | planned |
| M03 | Marketing Cloud Account Engagement | Pardot; MCAE. | planned |
| M04 | Marketing Cloud Personalization | Interaction Studio; historic technology lineage needs deeper verification. Evergage appears in historic legal service documentation; precise lineage and migration remain research tasks. | planned |
| M06 | Marketing Cloud Advertising | Advertising Studio; Digital Advertising; no paid delivery dependency. Radian6; Buddy Media; Social.com appear in 2013 marketing acquisition context; lifecycle and migration only, not current-SKU assertions. | planned |
| M09 | Contentful | Acquisition completed 2026-09-01; overlaps Salesforce CMS and Experience Cloud. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R5 — Revenue and commerce

Deterministic money and pricing, catalog, quotes, approvals, subscription lifecycle, usage rating, order/inventory operations, storefronts, commissions, loyalty and partner workflows.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| C04 | Sales Performance Management and Spiff | Sales Planning; territories; quotas; sales mapping use case. Spiff acquisition completed 2024-02-01. | planned |
| C05 | Partner Cloud and Channel Revenue Management | Partner Relationship Management; PRM; Partners catalog category; Sales Innovations for Industries Clouds. | planned |
| C06 | Revenue Cloud and Agentforce Revenue Management | Revenue Lifecycle Management; CPQ; Contracts; Subscription Management; Asset Lifecycle Management. Legacy Salesforce CPQ/Billing and Vlocity CLM overlap but require separate migration mapping. | planned |
| C07 | m3ter | Acquisition completed 2026-07-01; overlaps revenue consumption billing. | planned |
| M07 | Loyalty Management | Global Promotions Management; rewards and recognition. | planned |
| E01 | B2B Commerce | No separate aliases identified in this pass. CloudCraze acquisition in April 2018 and B2B lineage confirmed by official 2018 product announcement. | planned |
| E02 | B2C and Composable Commerce | Commerce Cloud; headless storefronts; Agentforce Guided Shopping deferred X01. Demandware acquisition completed 2016-07-11; Commerce lineage. | planned |
| E03 | Order Management | Order Management for B2B; inventory services. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R6 — Operational service

Field dispatch, asset/warranty, employee requests, catalog-driven industry processes and optional point-of-sale/payment adapters. Observe races, offline conflict and reconciliation.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| S03 | Field Service and Operations | Field Service mobile; scheduling and optimization; Document Builder. | planned |
| S04 | Asset Service Lifecycle Management and Visual Remote Assistant | No separate aliases identified in this pass. | planned |
| S05 | IT Service and HR Service | Employee Service; AI Agents for Employees. | planned |
| E04 | Modern Point of Sale and Payments | No assertion of payment network certification; live gateway optional and disabled until configured. | planned |
| T08 | Industry commerce and service processes | Unified Catalog; Enterprise Product Catalog (EPC); Industries Order Management; Industries CPQ; Digital Commerce; Order Capture; Vlocity Contract Lifecycle Management; Service Process Studio; Integration Solutions With MuleSoft. | planned |
| C10 | Salesforce Maps | Sales mapping distinct from quota/territory planning C04; no optimal-routing guarantee. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R7 — Data engineering and analytics

Import adapters, lineage, master records, data quality, permission-aware visual analytics and preparations. Prove formula consistency and row-level access before adding broad connectors.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| M05 | Marketing Cloud Intelligence | Datorama; Intelligence Reports for Engagement; Marketing Analytics. | planned |
| D01 | Data 360 | Data Cloud renamed 2025-10-14; CDP; Data Cloud One; Data 360 Starter; zero copy; Clean Rooms; data shares. | planned |
| D02 | Informatica Data Integration & Engineering | Cloud Data Integration; Cloud Application Integration; API & App Integration; API Center; Cloud B2B Gateway; PowerCenter migration discovery. | planned |
| D03 | Informatica MDM & 360 Applications | Customer 360; Product 360; Finance 360; Supplier 360; multidomain MDM; reference data. | planned |
| D04 | Informatica Governance, Catalog and Marketplace | Data Catalog; Cloud Data Governance and Catalog; Data Lineage; Data Access Management; Governance & Privacy; Cloud Data Marketplace. | planned |
| D05 | Informatica Data Quality & Observability | Cloud Data Quality; Data Observability; Data as a Service; CLAIRE AI mapped X01. | planned |
| A01 | Tableau analytics authoring and distribution | Tableau Desktop; Cloud; Server; Public; Mobile; Reader; Embedded Analytics; Viewer/Explorer/Creator are roles/tiers; Tableau+ and Enterprise are bundles. | planned |
| A02 | Tableau Prep | Prep Builder; Prep Conductor; Data Management tier; shared execution with D02. | planned |
| A03 | CRM Analytics | Einstein Discovery and industry analytics are scoped extensions; first release report is only a narrow subset. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R8 — Collaboration and application tools

Persistent conversations and documents, independently deployable apps, governed extensions, document processing, process mining and bounded automation runners. Evaluate existing open-source foundations at each boundary.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| I03 | MuleSoft RPA | RPA Manager; Builder; Bot; Recorder. RPA moving to end of sale; migration use cases retained. | planned |
| I04 | MuleSoft Intelligent Document Processing | Anypoint IDP; MuleSoft for Flow: IDP; overlaps industries document automation. | planned |
| L01 | Slack | Slack Connect; public/private channels; direct and group messages; huddles require separate media research. | planned |
| L03 | Quip | Quip Advanced; Salesforce Anywhere Advanced; Quip Plus/Starter; shield/governance variants; Quip for Customer 360. | planned |
| P07 | Developer tooling and app lifecycle | DevOps Center; Agentforce Vibes; Agent Script Recipes; Lightning components; Apex metadata migration scope only; Sandboxes; MuleSoft Vibes. Mobile Publisher for Experience Cloud; app-store distribution requires account permissions; native/mobile offline behavior remains untested. | planned |
| P08 | Heroku | Managed data/services and buildpack/add-on breadth require separate survey; prefer existing open-source foundation over building orchestrator. | planned |
| P10 | AgentExchange / AppExchange and Customer Success | Trailhead and training-style learning outcomes; Success Plans and professional services represented as operating guidance, not software parity. | planned |
| T04 | Document services | Omnistudio Document Generation; Salesforce Document Generation; Document Checklist Items; Intelligent Document Automation; Intelligent Document Reader; Intelligent Form Reader. | planned |
| X04 | Apromore | Acquisition completed 2025-11-03; evaluate available open-source lineage and exact license independently. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R9 — Evaluated AI outcomes

Optional local-model inference, grounded retrieval, approval-aware tools, semantic querying, transparent simulations and measured evaluations. Pending acquisitions receive discovery gates first; no proprietary model copying or reliability assumption.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| C08 | Momentum | Acquisition completed 2026-03-02; sales conversation/meeting context. | planned |
| S08 | Fin | Formerly Intercom; acquisition completed 2026-09-10; proprietary model suite will not be reproduced. | planned |
| M08 | Qualified / Piper | Acquisition completed 2026-04-01; Agentic Demand Generation; Conversational Experiences. | planned |
| M10 | Palmata | No separate aliases identified in this pass. | planned |
| E05 | Cimulate | Acquisition completed 2026-03-03. | planned |
| A04 | Tableau Next, Semantics and Pulse | Agentforce Tableau; Concierge; Data Pro; Inspector; Tableau Pulse for Salesforce; Tableau in Slack. | planned |
| I05 | MuleSoft Agent Fabric | Omni Gateway; Omni Gateway Model Proxy; MuleSoft Vibes mapped P07. | planned |
| L02 | Slack work surfaces and AI | Slackbot; Today; Slackforce Surfaces; Slack Code; Workflow Builder; canvases/lists need deeper behavioral survey; Sales/Service/Marketing Cloud in Slack; CRM in Slack. | planned |
| X01 | Agentforce and Einstein capabilities | Agentforce Studio; Agent Builder; Prompt Builder; Testing Center; Einstein Trust Layer; AIforce/Claudeforce surfaces; Hunter; AI Sales Agents; Einstein Autofill; Relationship Insights; AI Relationship Research; AI Accelerator and Scoring Framework; CLAIRE AI. | planned |
| X02 | Doti | Acquisition completed 2025-12-01; overlaps Slack enterprise search. | planned |
| X03 | Spindle AI | Acquisition completed 2025-11-21; ClearGraph mentioned as founder history, not a separately researched current SKU. | planned |
| X05 | Regrello | Acquisition completed 2025-10-01; overlapping orchestration shares P03, not duplicate engine. | planned |
| X06 | Waii | Acquisition completed 2025-08-15; shares semantic layer A04. | planned |
| W01 | Loops | Pending acquisition, expected early November FY2027; not counted as completed acquisition. | planned |
| W02 | Listen Labs | Pending acquisition; no assumption that commercial panel or multilingual claims are reproducible. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

### R10 — Validated industry and deployment packs

Industry-specific schemas, permissions and end-to-end workflows; domain expert review; deployment profiles and independent assurance as needed. This phase is a family of releases, not one large parity milestone.

| ID | Product/capability group | Included names retained in scope | Implementation status |
|---|---|---|---|
| P09 | Hyperforce and Government Cloud | Government Cloud Plus; Government Cloud Plus Defense; Private Connect; Express Connect; Mobile App Plus; Enterprise networking profiles need research. | planned |
| V01 | Automotive Cloud | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V02 | Communications Cloud | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V03 | Consumer Goods Cloud | Retail Execution; Trade Promotion Management. | planned |
| V04 | Education Cloud / Agentforce Education | Admissions Connect; Education Data Architecture (EDA); K-12 Architecture Kit; Student Success Hub; Learning Wizard; Marketing Cloud Engagement for Industries. | planned |
| V05 | Energy & Utilities Cloud | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V06 | Financial Services Cloud | Digital Lending; Collections and Recovery tracked V18. | planned |
| V07 | Health Cloud | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V08 | Life Sciences Cloud | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V09 | Manufacturing Cloud | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V10 | Media Cloud | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V11 | Nonprofit Cloud | Nonprofit Success Pack (NPSP); Gift Entry Manager (GEM); Salesforce.org managed packages; Philanthropy/Work.com for Vaccines/Emergency Program Management require lifecycle research. | planned |
| V12 | Public Sector Solutions | Vlocity Government; public assistance; licensing, permitting, inspections; no claimed regulatory authority. | planned |
| V13 | Retail | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V14 | Technology | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V15 | Travel, Transportation & Hospitality | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V16 | Construction & Real Estate | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V17 | Professional Services | Agentforce for Industries extensions map X01; industry name does not imply distinct runnable product. | planned |
| V18 | Digital Insurance and Collections & Recovery | Insurance/benefit administration; separate permissions and domain review required. | planned |
| V19 | Net Zero Cloud | Former Sustainability Cloud; building/vehicle energy and waste footprints; no assurance opinion. | planned |
| T06 | Programs, outcomes and grantmaking | Program and Case Management; Outcome Management; Grantmaking; Grants Management Managed Package. | planned |
| T07 | Accounting Subledger | Gift Entry Manager maps V11; not a full general ledger. | planned |

Acceptance gate: complete the row-specific acceptance criteria in `portfolio-matrix.csv`, link implementation and test evidence, then revise the release coverage matrix. Prerequisites named in each row may move a sub-capability later than its family.

## Continuation instructions

1. Read the current README, release notes, progress notes and implementation coverage matrix before changing statuses. Run the documented local test suite from a clean directory. Preserve actual result logs.
2. For the next R2 increment, first inspect current platform behavior. Pick one bounded vertical workflow (suggestion: custom typed contact fields with safe CSV round-trip), document its original schema and accepted constraints, then implement and verify it end to end.
3. Before adopting an open-source component, review its exact version, SPDX license, transitive license obligations, maintenance, tenant/permission model and replaceable integration boundary. Record why adopted or deferred; do not copy proprietary vendor code/assets.
4. Keep operating costs explicit: software may be free; hosting, backup storage, email/SMS, payment processing, media transport and inference hardware may cost money. Core workflows must run without a mandatory paid service. No purchase or new charge is authorized by this roadmap.
5. Update both the inventory and this roadmap when discovery finds a new product. Use an alias of an existing outcome when justified; otherwise assign a stable new ID. Preserve pending/retired status and unknowns.
6. Before remote publication, inspect staged files and history for secrets, private data, copied assets and license conflicts. Use the user's exact GitHub destination when supplied; `[GITHUB_OWNER/REPO]` is a placeholder. Verify remote commit and CI independently. A passing local test is not a remote CI result.
7. End each work session with exact completed capabilities, test commands/results, remaining limits and next runnable command. Do not imply that roadmap work continues in the background.

## Discovery coverage boundary

The inventory covers the main catalog, the industry catalog, public brand directory, 65-group additional-products Help index, selected public API references, current acquired-brand announcements and documented transitions. It does not establish exhaustive SKUs, entitlement combinations, all historic acquisitions or every behavior. The next catalog pass must examine release notes, mobile/developer services, optional networking/identity/security products, legacy managed packages and regional variants. Product names in a source's unrelated news links or customer testimonials are not automatically independent portfolio entries.
