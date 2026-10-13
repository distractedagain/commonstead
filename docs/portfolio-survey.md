# Bounded Salesforce portfolio survey

Research date: 2026-10-12 (America/Chicago). This is a public-source reconnaissance pass for an independently written, self-hosted suite called Commonstead. It is not a claim to have found every Salesforce SKU, every acquisition, every regional edition or every externally observable behavior. No Salesforce tenant, trial, customer data, paid service, private source code or proprietary asset was accessed. Product demonstration indexes were reviewed; videos and gated interactive demonstrations were not executed.

The accompanying `portfolio-matrix.csv` is the inventory and target specification. Its **documented_purpose**, **evidence_depth**, **observed_public_interfaces**, **source_urls**, and **unknowns_and_access_limits** columns describe evidence. All columns beginning **proposed_**, the dependencies and acceptance criteria are original Commonstead design choices. The proposed data model is not a claim about Salesforce internal tables. A product page proves advertised scope; it does not prove correct behavior, availability in a particular account, performance, security or compatibility.

The initial inventory contains 95 product/capability groups. Groups intentionally consolidate renamed products, suite tiers and closely related add-ons; the names in `aliases_and_included_offerings` remain in scope. Parent and child capabilities overlap, so row count is not a distinct product count or a completion percentage. Pending acquisition watchlist entries are included for future review without treating their transactions as completed.

## Evidence and naming decisions

- The [main product catalog](https://www.salesforce.com/products/) supplies business-line entry points and distinguishes Customer 360 as an overall outcome rather than a single product. Starter, Pro and Foundations are bundle presets, not separate implementations of the same records.
- The [additional-products Help index](https://help.salesforce.com/s/products/additionalproducts?language=en_US) exposed 65 documentation groups. These are consolidated in the matrix and explicitly mapped in `help-index-map.csv`. Documentation groups are not assumed to be independently sold products.
- [Official Help](https://help.salesforce.com/s/articleView?id=sf.c360_a_data_cloud.htm&language=en_US) dates the Data Cloud → Data 360 rename to 2025-10-14. It remains one D01 capability family. Data 360 and Informatica address different but overlapping data outcomes.
- [Marketing product comparison](https://help.salesforce.com/s/articleView?id=001496483&language=en_US&type=1) distinguishes Next, Account Engagement and Engagement; these are separate workflow families. Pardot is Account Engagement. [An official Salesforce.org community announcement](https://trailhead.salesforce.com/trailblazer-community/feed/0D54S00000GffPcSAJ) records Interaction Studio → Personalization, Datorama → Intelligence and Advertising Studio → Advertising. That historical naming source is weaker than a current executable specification.
- Current [Sales](https://www.salesforce.com/sales/) and [Revenue](https://www.salesforce.com/sales/revenue-lifecycle-management/) pages coexist with Agentforce-prefixed names in Help and announcements. These are grouped by outcome. Legacy Salesforce CPQ/Billing and Vlocity packages are not assumed to have identical data models or migration paths.
- [Tableau's official overview](https://help.tableau.com/current/tableau-next/en-us/tableau_next_tableau_product_overview.htm) separates traditional authoring/server/cloud tooling from Next and semantic/agent capabilities. License roles and bundles are not standalone feature families.
- [Quip's retirement notice](https://help.salesforce.com/s/articleView?id=005299603&language=en_US&type=1) says new accounts stopped on 2026-02-17 and subscriptions become nonrenewable after 2027-03-01. Document migration remains on the roadmap.
- [MuleSoft's current credit documentation](https://docs.mulesoft.com/general/mulesoft-automation-credits-3-0) says Composer and RPA are moving to end of sale. Their user outcomes remain represented alongside MuleSoft for Flow; a documented transition is not evidence of feature-equivalent migration.
- The [industry catalog](https://www.salesforce.com/industries/) includes cloud products and broader solution sectors. Construction & Real Estate, Professional Services, Retail, Technology, and Travel/Transportation/Hospitality are retained as solution packs without assuming each is a separate SKU. Healthcare's proposed care coordination workflow requires domain review and is not medical decision software.

## Acquired brands and transaction evidence

Salesforce's [brand directory](https://www.salesforce.com/company/our-brands/) names Tableau, Slack, MuleSoft and Heroku. Current primary pages additionally establish the following. Dates below are transaction dates explicitly reported by the sources, not dates inferred from an initial agreement headline.

| Brand | Observed state | Matrix groups |
|---|---|---|
| [Spiff](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-spiff/) | Completed 2024-02-01 | C04 |
| [Own](https://help.salesforce.com/s/articleView?id=004634031&language=en_US&type=1) | Current FAQ describes integration into Salesforce; closing date not researched here | P05 |
| [Informatica](https://www.salesforce.com/news/press-releases/2025/11/18/salesforce-completes-acquisition-of-informatica/) | Completed 2025-11-18 | D02–D05 |
| [Regrello](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-regrello/) | Completed 2025-10-01 | X05 |
| [Apromore](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-apromore/) | Completed 2025-11-03 | X04 |
| [Waii](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-waii/) | Completed 2025-08-15 | X06 |
| [Spindle AI](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-spindle-ai/) | Completed 2025-11-21 | X03 |
| [Doti](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-doti/) | Completed 2025-12-01 | X02 |
| [Momentum](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-momentum/) | Completed 2026-03-02 | C08 |
| [Cimulate](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-cimulate/) | Completed 2026-03-03 | E05 |
| [Qualified](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-qualified/) | Completed 2026-04-01 | M08 |
| [m3ter](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-m3ter/) | Completed 2026-07-01 | C07 |
| [Contentful](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-contentful/) | Completed 2026-09-01 | M09 |
| [Fin, formerly Intercom](https://www.salesforce.com/news/press-releases/2026/09/10/salesforce-completes-acquisition-of-fin/) | Completed 2026-09-10 | S08 |
| [Loops](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-loops/) | Agreement announced 2026-10-12; closing pending | W01 |
| [Listen Labs](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-listen-labs/) | Agreement announced 2026-09-29; closing pending | W02 |

Vlocity-branded offerings appear in current and historical industry documentation and are grouped with their industry outcomes. Quip remains a migration target. Palmata is a marketing-page mention with insufficient transaction or behavioral evidence. Acquisition does not establish that the acquired feature is generally available, integrated, or independently sold. Selected historic lineage is retained in aliases: ExactTarget, Demandware and CloudCraze have primary acquisition/product evidence; Evergage appears in legal service records; Radian6, Buddy Media and Social.com are historical marketing references with lifecycle unknowns. The remaining acquisition genealogy is not claimed complete.

## Public interfaces and compatibility boundary

The [REST API reference](https://developer.salesforce.com/docs/platform/api-rest/guide/resources-list.html) and [platform API overview](https://developer.salesforce.com/blogs/2024/04/accessing-object-data-with-salesforce-platform-apis) establish versioned object/query/composite/bulk and related resources. [Pub/Sub documentation](https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html) establishes an event API using gRPC and Avro. [Slack conversations documentation](https://docs.slack.dev/apis/web-api/using-the-conversations-api/) establishes scope-filtered channel and DM operations. These are research inputs, not compatibility claims.

Commonstead's first release uses its own HTTP API and its own schemas. Salesforce integrations, SOQL/SOSL, Apex, Lightning metadata, Slack clients, Tableau workbooks, MuleSoft flows, industry packages and proprietary models are **not** supported by resemblance alone. Every eventual adapter needs a separate public contract, license review, authorized test environment, versioned fixture set, rate-limit strategy and live integration result.

## Limits and next discovery pass

Research used accessible HTML and search-indexed official documentation. Some Help pages displayed CSS/loading errors alongside usable text. We did not bypass access controls. Pricing, contractual entitlements, uptime, marketing ROI, vendor resolution rates and vendor compliance statements are not adopted as Commonstead claims. Live pages are mutable; this survey records what was retrievable on the research date, not an immutable archive of all historical versions.

Next pass: enumerate current release notes and downloadable add-on catalog, follow each family into its public object/API reference, separate general availability from beta/pilot, validate acquired-brand lifecycle and migrations, and write one observed-workflow specification per planned increment. Refresh pending acquisitions before moving them into product scope. Investigate regional editions, sovereign environments, accessibility behavior, API quotas, mobile offline conflict semantics and legacy-product retirements. No background research is implied by this document.

## Source register

Every URL below was retrieved directly or surfaced in official-domain search during this pass; scope varies as recorded per matrix row. Research date for all entries: 2026-10-12. The index is a continuation aid, not an assertion that every linked subpage was fully reviewed.

- **catalog**: [catalog](https://www.salesforce.com/products/)
- **brands**: [brands](https://www.salesforce.com/company/our-brands/)
- **industry**: [industry](https://www.salesforce.com/industries/)
- **help**: [help](https://help.salesforce.com/s/products/additionalproducts?language=en_US)
- **sales**: [sales](https://www.salesforce.com/sales/)
- **revenue**: [revenue](https://www.salesforce.com/sales/revenue-lifecycle-management/)
- **service**: [service](https://www.salesforce.com/service/)
- **field**: [field](https://www.salesforce.com/service/field-service-management/)
- **marketing**: [marketing](https://www.salesforce.com/marketing/)
- **commerce**: [commerce](https://www.salesforce.com/commerce/)
- **platform**: [platform](https://www.salesforce.com/platform/)
- **shield**: [shield](https://www.salesforce.com/platform/shield/)
- **privacy**: [privacy](https://www.salesforce.com/platform/privacy-center/)
- **own**: [own](https://help.salesforce.com/s/articleView?id=004634031&language=en_US&type=1)
- **data**: [data](https://help.salesforce.com/s/articleView?id=sf.c360_a_data_cloud.htm&language=en_US)
- **data-actions**: [data-actions](https://help.salesforce.com/s/articleView?id=data.c360_a_act_on_data.htm&language=en_US&type=5)
- **marketing-types**: [marketing-types](https://help.salesforce.com/s/articleView?id=001496483&language=en_US&type=1)
- **marketing-aliases**: [marketing-aliases](https://trailhead.salesforce.com/trailblazer-community/feed/0D54S00000GffPcSAJ)
- **analytics**: [analytics](https://www.salesforce.com/analytics/)
- **tableau**: [tableau](https://help.tableau.com/current/tableau-next/en-us/tableau_next_tableau_product_overview.htm)
- **mulesoft**: [mulesoft](https://www.salesforce.com/mulesoft/)
- **mule-usage**: [mule-usage](https://docs.mulesoft.com/general/usage-reports)
- **mule-retire**: [mule-retire](https://docs.mulesoft.com/general/mulesoft-automation-credits-3-0)
- **rpa**: [rpa](https://docs.mulesoft.com/rpa-manager/)
- **idp**: [idp](https://docs.mulesoft.com/idp/)
- **composer**: [composer](https://docs.mulesoft.com/composer/ms_composer_reference)
- **slack**: [slack](https://www.salesforce.com/slack/)
- **slack-api**: [slack-api](https://docs.slack.dev/apis/web-api/using-the-conversations-api/)
- **quip**: [quip](https://help.salesforce.com/s/articleView?id=sf.quip.htm&language=en_US&type=5)
- **quip-retire**: [quip-retire](https://help.salesforce.com/s/articleView?id=005299603&language=en_US&type=1)
- **heroku**: [heroku](https://www.salesforce.com/heroku/)
- **netzero**: [netzero](https://www.salesforce.com/net-zero/)
- **informatica**: [informatica](https://www.informatica.com/products.html/1000.html)
- **info-catalog**: [info-catalog](https://www.informatica.com/products/data-catalog.html/)
- **info-quality**: [info-quality](https://www.informatica.com/products/data-quality.html)
- **info-metadata**: [info-metadata](https://www.informatica.com/products/informatica-platform/metadata-management.html)
- **info-integration**: [info-integration](https://www.informatica.com/products/cloud-integration.html.html.html.html.html)
- **info-mdm**: [info-mdm](https://www.informatica.com/content/dam/informatica-com/en/collateral/data-sheet/informatica-multidomain-mdm-saas_data-sheet_4305en.pdf)
- **rest**: [rest](https://developer.salesforce.com/docs/platform/api-rest/guide/resources-list.html)
- **api-overview**: [api-overview](https://developer.salesforce.com/blogs/2024/04/accessing-object-data-with-salesforce-platform-apis)
- **pubsub**: [pubsub](https://developer.salesforce.com/docs/platform/pub-sub-api/guide/intro.html)
- **prompt**: [prompt](https://help.salesforce.com/s/articleView?id=sf.prompt_builder_intro.htm&language=en_US)
- **agent-test**: [agent-test](https://help.salesforce.com/s/articleView?id=ai.agent_testing_center.htm&language=en_US&type=5)
- **chatter**: [chatter](https://help.salesforce.com/s/articleView?id=xcloud.limits_mobile_sf1_chatter.htm&language=en_US&type=5)
- **experience**: [experience](https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/communities.pdf)
- **action**: [action](https://help.salesforce.com/s/articleView?id=ind.the_action_launcher_component.htm&language=en_US&type=5)
- **rules**: [rules](https://help.salesforce.com/s/articleView?id=ind.business_rules_engine.htm&language=en_US&type=5)
- **sharing**: [sharing](https://help.salesforce.com/s/articleView?id=ind.fsc_admin_cds.htm&language=en_US&type=5)
- **history**: [history](https://help.salesforce.com/s/articleView?id=ind.industries_cross_object_history_container.htm&language=en_US&type=5)
- **consume**: [consume](https://help.salesforce.com/s/articleView?id=ind.consumption_framework.htm&language=en_US&type=5)
- **docgen**: [docgen](https://help.salesforce.com/s/articleView?id=ind.doc_gen_foundation_document_generation_overview_389381.htm&language=en_US&type=5)
- **form**: [form](https://help.salesforce.com/s/articleView?id=ind.grmk_form_framework.htm&language=en_US&type=5)
- **groups**: [groups](https://help.salesforce.com/s/articleView?id=ind.group_membership.htm&language=en_US&type=5)
- **docauto**: [docauto](https://help.salesforce.com/s/articleView?id=ind.document_automation.htm&language=en_US&type=5)
- **outcome**: [outcome](https://help.salesforce.com/s/articleView?id=ind.outcome_management.htm&language=en_US&type=5)
- **program**: [program](https://help.salesforce.com/s/articleView?id=ind.prog_case_mgmt.htm&language=en_US&type=5)
- **process**: [process](https://help.salesforce.com/s/articleView?id=ind.service_process_studio.htm&language=en_US&type=5)
- **catalog-service**: [catalog-service](https://help.salesforce.com/s/articleView?id=ind.unified_catalog_intro.htm&language=en_US&type=5)
- **subledger**: [subledger](https://help.salesforce.com/s/articleView?id=sfdo.accounting_subledger.htm&language=en_US&type=5)
- **education**: [education](https://help.salesforce.com/s/articleView?id=sfdo.education_cloud.htm&language=en_US&type=5)
- **grants**: [grants](https://help.salesforce.com/s/articleView?id=ind.grmk_grantmaking.htm&language=en_US&type=5)
- **omni**: [omni](https://help.salesforce.com/s/articleView?id=xcloud.os_omnistudio_standard.htm&language=en_US&type=5)
- **gov**: [gov](https://help.salesforce.com/s/articleView?id=000396813&language=en_US&type=1)
- **industries-dev**: [industries-dev](https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_industries_dev_guide.pdf)
- **industry-release**: [industry-release](https://help.salesforce.com/s/articleView?id=release-notes.rn_industries.htm&language=en_US&release=248&type=5)
- **acquisitions**: [acquisitions](https://www.salesforce.com/news/topics/mergers-and-acquisitions/)
- **fin**: [fin](https://www.salesforce.com/news/press-releases/2026/09/10/salesforce-completes-acquisition-of-fin/)
- **info-close**: [info-close](https://www.salesforce.com/news/press-releases/2025/11/18/salesforce-completes-acquisition-of-informatica/)
- **demos**: [demos](https://www.salesforce.com/products/demos/)
- **spiff**: [spiff](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-spiff/)
- **loops**: [loops](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-loops/)
- **listen-labs**: [listen-labs](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-listen-labs/)
- **m3ter**: [m3ter](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-m3ter/)
- **contentful**: [contentful](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-contentful/)
- **momentum**: [momentum](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-momentum/)
- **cimulate**: [cimulate](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-cimulate/)
- **qualified**: [qualified](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-qualified/)
- **doti**: [doti](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-doti/)
- **spindle-ai**: [spindle-ai](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-spindle-ai/)
- **apromore**: [apromore](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-apromore/)
- **regrello**: [regrello](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-regrello/)
- **waii**: [waii](https://www.salesforce.com/news/stories/salesforce-signs-definitive-agreement-to-acquire-waii/)
- **maps**: [maps](https://help.salesforce.com/s/articleView?id=sf.salesforce_maps_setup_maps.htm&language=en_US&type=5)
- **inbox**: [inbox](https://help.salesforce.com/s/articleView?id=email_int_setup_inbox_parent.htm&language=en_US)
- **demandware**: [demandware](https://www.salesforce.com/news/press-releases/2016/07/11/salesforce-completes-acquisition-of-demandware/)
- **exacttarget**: [exacttarget](https://www.salesforce.com/news/press-releases/2013/07/12/salesforce-com-completes-acquisition-of-exacttarget/)
- **cloudcraze**: [cloudcraze](https://www.salesforce.com/blog/introducing-salesforce-b2b-commerce-blog/)
- **historic-services**: [historic-services](https://www.salesforce.com/en-us/wp-content/uploads/sites/4/documents/legal/misc/trust-and-compliance-change-log.pdf)
- **mobile-publisher**: [mobile-publisher](https://help.salesforce.com/s/articleView?id=xcloud.branded_apps_gather_private_ios_invite_sfdc.htm&language=en_US&type=5)
- **own-terms**: [own-terms](https://www.salesforce.com/en-us/wp-content/uploads/sites/4/documents/legal/Agreements/product-specific-terms/own-support-plan.pdf)
