# Held-out labelling packet

6 companies × 4 criteria = 24 items. **Research material, not financial advice.** The passages come from each company's latest Form 10-K and were picked by a fixed keyword retrieval, not by the analysis tool.

## How to label

1. For each item read the question and the rubric, then the passages. A passage is only a starting point: open the filing at the SEC link if you need more, and judge what the **filing** shows, not only what the passages show.
2. Pick one verdict for the item: `found`, `weak` or `insufficient`, using the rubric's meanings and applying the latest-fiscal-year rule where it is given.
3. Write it on the **Verdict:** line (replace `…`), with an optional note on the **Note:** line. Do not change anything else in the file.
4. Do not look at the website's verdicts for these companies until every item is labelled. If you have already seen some, say so in the first note of the file.
5. When all items are done, run `python scripts/label_packet.py --ingest docs/labelling/heldout_packet.md` to write `eval/heldout_labels.json`.

List frozen 2026-10-12 (`eval/heldout.json`).

---

## AAPL

Form 10-K, accession 0000320193-25-000079, filed 2025-10-31, period 2025-09-27. [Open the filing on sec.gov](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

### AAPL · understandable_business

**Understandable business.** Can the business be explained simply: what the company sells, to whom, and how it makes money?

- **found** ("evidence found"): The filing names specific products or services, the customers or markets they are sold to, and how revenue is earned (for example segments with figures, a pricing or sales model), in plain terms.
- **weak** ("evidence weak"): The business is described only in general or promotional terms (a 'leading provider of solutions'), or the filing says what is sold but not who buys it or how it earns money.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what the company sells or how it earns money, or the Business section is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1), in filing order:

**[0000320193-25-000079:1:1]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Item 1. Business
> Company Background
> The Company designs, manufactures and markets smartphones, personal computers, tablets, wearables and accessories, and sells a variety of related services. The Company's fiscal year is the 52- or 53-week period that ends on the last Saturday of September.
> Products
> iPhone
> iPhone® is the Company's line of smartphones based on its iOS operating system. The iPhone line includes iPhone 17 Pro, iPhone Air™, iPhone 17, iPhone 16 and iPhone 16e.
> Mac
> Mac® is the Company's line of personal computers based on its macOS® operating system. The Mac line includes laptops MacBook Air® and MacBook Pro®, as well as desktops iMac®, Mac mini®, Mac Studio® and Mac Pro®.
> iPad
> iPad® is the Company's line of multipurpose tablets based on its iPadOS® operating system. The iPad line includes iPad Pro®, iPad Air®, iPad and iPad mini®.
> Wearables, Home and Accessories

**[0000320193-25-000079:1:3]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company's cloud services store and keep customers' content up-to-date and available across multiple Apple devices and Windows personal computers.
> Digital Content
> The Company operates various platforms, including the App Store®, that allow customers to discover and download applications and digital content, such as books, music, video, games and podcasts.
> The Company also offers digital content through subscription-based services, including Apple Arcade®, a game service; Apple Fitness+®, a personalized fitness service; Apple Music®, which offers users a curated listening experience with on-demand radio stations; Apple News+®, a news and magazine service; and Apple TV®, which offers exclusive original content and live sports.
> Payment Services
> The Company offers payment services, including Apple Card®, a co-branded credit card, and Apple Pay®, a cashless payment service.
> Segments

**[0000320193-25-000079:1:4]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company manages its business primarily on a geographic basis. The Company's reportable segments consist of the Americas, Europe, Greater China, Japan and Rest of Asia Pacific. Americas includes both North and South America. Europe includes European countries, as well as India, the Middle East and Africa. Greater China includes China mainland, Hong Kong and Taiwan. Rest of Asia Pacific includes Australia, New Zealand and those Asian countries not included in the Company's other reportable segments. Although the reportable segments provide similar hardware and software products and similar services, each one is managed separately to better align with the location of the Company's customers and distribution partners and the unique market dynamics of each geographic region.
> Markets and Distribution

**[0000320193-25-000079:1:5]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company's customers are primarily in the consumer, small and mid-sized business, education, enterprise and government markets. The Company sells its products and resells third-party products in most of its major markets directly to customers through its retail and online stores and its direct sales force. The Company sells its services in the same markets through its various service platforms. The Company also employs a variety of indirect distribution channels, such as third-party cellular network carriers and other resellers, for the sale of its products and certain of its services. During 2025, the Company's net sales through its direct and indirect distribution channels accounted for 40% and 60%, respectively, of total net sales.
> Competition

**[0000320193-25-000079:1:7]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company's ability to compete successfully depends heavily on ensuring the continuing and timely introduction of innovative new products, services and technologies to the marketplace. The Company designs and develops nearly the entire solution for its products, including the hardware, operating system, numerous software applications and related services. Principal competitive factors important to the Company include price, product and service features (including security features), relative price and performance, product and service quality and reliability, design and technology innovation, a strong third-party software and accessories ecosystem, marketing and distribution capability, service and support, corporate reputation, and the ability to effectively protect and enforce the Company's intellectual property rights.

**[0000320193-25-000079:1:11]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Because the industries in which the Company competes are characterized by rapid technological advances, the Company's ability to compete successfully depends heavily upon its ability to ensure a continual and timely flow of competitive products, services and technologies to the marketplace. The Company continues to develop new technologies to enhance existing products and services, and to expand the range of its offerings through research and development ("R&D"), licensing of intellectual property and acquisition of third-party businesses and technology.
> Intellectual Property
> The Company currently holds a broad collection of intellectual property rights relating to certain aspects of its hardware, software and services. This includes patents, designs, copyrights, trademarks, trade secrets and other forms of intellectual property rights in the U.S. and various foreign countries. Although the Company believes the ownership of such intellectual property rights is an important factor in differentiating its business and that its success does depend in part on such ownership, the Company relies primarily on the innovative skills, technical competence and marketing abilities of its personnel.

**[0000320193-25-000079:1:13]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company has historically experienced higher net sales in its first quarter compared to other quarters in its fiscal year due in part to seasonal holiday demand. Additionally, new product and service introductions can significantly impact net sales, cost of sales and operating expenses. The timing of product introductions can also impact the Company's net sales to its indirect distribution channels as these channels are filled with new inventory following a product launch, and channel inventory of an older product often declines as the launch of a newer product approaches. Net sales can also be affected when consumers and distributors anticipate a product introduction.
> Human Capital
> The Company believes that its people play an important role in its success, and strives to attract, develop and retain the best talent. The Company works to create a culture of collaboration, one where people with a broad range of backgrounds and perspectives can come together to innovate and do the best work of their lives. The Company is an equal opportunity employer committed to inclusion and to providing a workplace free of harassment or discrimination. As of September 27, 2025, the Company had approximately 166,000 full-time equivalent employees.

**[0000320193-25-000079:1:14]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company believes that compensation should be competitive and equitable, and offers discretionary cash and equity awards to enable employees to share in the Company's success. The Company recognizes its people are most likely to thrive when they have the resources to meet their needs and the time and support to succeed in their professional and personal lives. In support of this, the Company offers a wide variety of benefits for employees around the world, including health, wellness and time away.
> The Company invests in resources to help its people develop and achieve their career goals. The Company offers programs through Apple University on leadership, management and influence, as well as Apple culture and values. Team members can also take advantage of online classes for business, technical and personal development.
> The Company believes that open and honest communication among team members, managers and leaders helps create an open, collaborative work environment where everyone can contribute, grow and succeed. Team members are encouraged to come to their managers with questions, feedback or concerns, and the Company conducts surveys that gauge employee sentiment in areas like career development, manager performance and inclusion.

**Verdict:** Found

**Note:** 

### AAPL · durable_competitive_advantage

**Durable competitive advantage.** Does the filing give concrete evidence of an advantage that protects the company's profits from competitors over many years (for example a brand, scale or cost position, switching costs, a network, patents, or a regulated franchise)?

- **found** ("evidence found"): The filing states a source of advantage AND a checkable specific for it: a market share or rank figure; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated network size. A statement that an asset exists or matters (brand, trade secrets, patents, 'strong' distribution) without a measure is not enough.
- **weak** ("evidence weak"): The advantage is only asserted, or an asset is named as important (brand, trade secrets, patents, scale) without any measure; or the specifics are offset by the filing's own statements that competitors or customers can readily erode the position.
- **insufficient** ("insufficient evidence"): The retrieved text says nothing about the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1, Item 1A), in filing order:

**[0000320193-25-000079:1:6]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The markets for the Company's products and services are highly competitive and are characterized by aggressive price competition, downward pressure on gross margins, continual improvement in product performance, and price sensitivity on the part of consumers and businesses. The markets in which the Company competes are further defined by frequent introduction of new products and services, short product life cycles, evolving industry standards, and rapid adoption of technological advancements by competitors. Many of the Company's competitors seek to compete primarily through aggressive pricing and very low cost structures, and by imitating the Company's products and infringing on its intellectual property.
> Apple Inc. | 2025 Form 10-K | 2

**[0000320193-25-000079:1:11]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Because the industries in which the Company competes are characterized by rapid technological advances, the Company's ability to compete successfully depends heavily upon its ability to ensure a continual and timely flow of competitive products, services and technologies to the marketplace. The Company continues to develop new technologies to enhance existing products and services, and to expand the range of its offerings through research and development ("R&D"), licensing of intellectual property and acquisition of third-party businesses and technology.
> Intellectual Property
> The Company currently holds a broad collection of intellectual property rights relating to certain aspects of its hardware, software and services. This includes patents, designs, copyrights, trademarks, trade secrets and other forms of intellectual property rights in the U.S. and various foreign countries. Although the Company believes the ownership of such intellectual property rights is an important factor in differentiating its business and that its success does depend in part on such ownership, the Company relies primarily on the innovative skills, technical competence and marketing abilities of its personnel.

**[0000320193-25-000079:1:14]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company believes that compensation should be competitive and equitable, and offers discretionary cash and equity awards to enable employees to share in the Company's success. The Company recognizes its people are most likely to thrive when they have the resources to meet their needs and the time and support to succeed in their professional and personal lives. In support of this, the Company offers a wide variety of benefits for employees around the world, including health, wellness and time away.
> The Company invests in resources to help its people develop and achieve their career goals. The Company offers programs through Apple University on leadership, management and influence, as well as Apple culture and values. Team members can also take advantage of online classes for business, technical and personal development.
> The Company believes that open and honest communication among team members, managers and leaders helps create an open, collaborative work environment where everyone can contribute, grow and succeed. Team members are encouraged to come to their managers with questions, feedback or concerns, and the Company conducts surveys that gauge employee sentiment in areas like career development, manager performance and inclusion.

**[0000320193-25-000079:1A:10]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company's ability to compete successfully depends heavily on ensuring the continuing and timely introduction of innovative new products, services and technologies to the marketplace. The Company designs and develops nearly the entire solution for its products, including the hardware, operating system, numerous software applications and related services. As a result, the Company must make significant investments in R&D. These investments may not achieve expected returns, and the Company may not be able to develop and market new products and services successfully.
> The Company's ability to compete successfully also depends on the effective protection and enforcement of its intellectual property rights. Regulatory requirements, government investigations and litigation can force the Company to withdraw from, or modify its products and services for, certain countries and limit its ability to derive value from, or to enjoin others from using, its intellectual property rights. Additionally, they may require the Company to share its innovations with competitors. Any of these outcomes can have a negative impact on the Company's competitive advantage and materially adversely affect its business, results of operations, financial condition and stock price.

**[0000320193-25-000079:1A:11]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company currently holds a significant number of patents, trademarks and copyrights and has registered, and applied to register, additional patents, trademarks and copyrights. In contrast, many of the Company's competitors seek to compete primarily through aggressive pricing and very low cost structures, and by imitating the Company's products and infringing on its intellectual property. Effective intellectual property protection is not consistently available in every country in which the Company operates. If the Company is unable to continue to develop and sell innovative new products with attractive margins or if competitors infringe on the Company's intellectual property, the Company's ability to maintain a competitive advantage could be materially adversely affected.

**[0000320193-25-000079:1A:23]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company's products and services include technology or intellectual property that must be licensed from third parties. In addition, because of technological changes in the industries in which the Company currently competes or in the future may compete, current extensive intellectual property coverage and the rapid rate of new intellectual property rights generation, the Company's products and services may be alleged to infringe existing intellectual property rights of others. This risk may be exacerbated by the use of new and emerging technologies, including machine learning and artificial intelligence, which can involve, among other things, the acquisition and use of copyrighted materials for training as well as the potential reproduction of copyrighted materials in their outputs. From time to time, the Company has been notified that it may be infringing certain intellectual property rights of third parties. The Company is not always able to obtain all necessary licenses to third-party intellectual property rights on commercially reasonable terms or at all. Failure to obtain the right to use third-party intellectual property, or to use such intellectual property on commercially reasonable terms, can require the Company to modify certain products, services or features or preclude the Company from selling certain products or services and expose the Company to significant licensing costs, all of which can materially adversely affect the Company's business, reputation, results of operations, financial condition and stock price.

**[0000320193-25-000079:1A:28]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Much of the Company's future success depends on the talents and efforts of its team members and the continued availability and service of key personnel, including its Chief Executive Officer, executive team and other highly skilled employees. Experienced personnel in the technology industry are in high demand and competition for their talents is intense, especially in Silicon Valley, where most of the Company's key personnel are located. Periods of intense competition for talent in particular fields can lead to increased costs as the Company seeks to offer competitive compensation to recruit and retain highly skilled employees. In addition to competition for talent, workforce dynamics are constantly evolving and the Company must navigate changes effectively in order to achieve its strategic initiatives. Laws and regulations, including immigration, labor and employment laws and export controls, among others, can materially adversely affect the Company's ability to recruit and retain a highly skilled, global workforce. If the Company does not effectively manage changing workforce dynamics and regulatory requirements, it could materially adversely affect the Company's culture, operational flexibility, strategy and costs, all of which can materially adversely affect the Company's business, reputation, results of operations, financial condition and stock price.

**[0000320193-25-000079:1A:42]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Compliance with these laws and regulations is onerous and expensive. New and changing laws, regulations, executive orders, directives, and enforcement priorities can adversely affect the Company's business by increasing the Company's costs, limiting the Company's ability to offer a product, service or feature to customers, imposing changes to the design of the Company's products and services, impacting customer demand for the Company's products and services, and requiring changes to the Company's business or supply chain. New and changing laws, regulations, executive orders, directives, and enforcement priorities can also create uncertainty about how such laws and regulations will be interpreted and applied. If the Company is found to have violated such laws and regulations, it could materially adversely affect the Company's business, reputation, results of operations, financial condition and stock price.
> Risks and costs related to new and changing laws, regulations, executive orders, directives, and enforcement priorities increase as the Company's products and services are introduced into specialized applications, including health and financial services, or as the Company expands the use of technologies, such as machine learning and artificial intelligence features, and must navigate new legal, regulatory and ethical considerations relating to such technologies.

**Verdict:** found 

**Note:** 

### AAPL · candid_management

**Candid management.** Does management openly discuss setbacks, mistakes, declines and uncertainty in its own words, rather than only successes?

- **found** ("evidence found"): Management's own account of a setback that it attributes at least partly to the company's own decisions or execution; or a target or guidance of its own that was missed; or an acknowledged material weakness, restatement or write-down of something management chose (an acquisition, investment or project), stated plainly.
- **weak** ("evidence weak"): Declines or charges explained only by external factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even when quantified; or generic caution ('results may fluctuate', 'we face risks'); or a setback mentioned without explanation.
- **insufficient** ("insufficient evidence"): The retrieved text is promotional or boilerplate and gives nothing to judge candour either way, or MD&A and Risk Factors are missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.
- **Limitation:** Limitation: 10-K text is reviewed by lawyers, and candour is better judged from shareholder letters (outside this tool's scope). Do not read polished or detailed prose as candour;

Passages (Item 7, Item 1A), in filing order:

**[0000320193-25-000079:1A:1]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Item 1A. Risk Factors
> The following summarizes factors that could have a material adverse effect on the Company's business, reputation, results of operations, financial condition and stock price. The Company may not be able to accurately predict, control or mitigate these risks. Statements in this section are based on the Company's beliefs and opinions regarding matters that could materially adversely affect the Company in the future and are not representations as to whether such matters have or have not occurred previously. The risks and uncertainties described below are not exhaustive and should not be considered a complete statement of all potential risks or uncertainties that the Company faces or may face in the future.
> This section should be read in conjunction with Part II, Item 7, "Management's Discussion and Analysis of Financial Condition and Results of Operations" and the consolidated financial statements and accompanying notes in Part II, Item 8, "Financial Statements and Supplementary Data" of this Form 10-K.
> Macroeconomic and Industry Risks
> The Company's operations and performance depend significantly on global and regional economic conditions and adverse economic conditions can materially adversely affect the Company's business, results of operations, financial condition and stock price.

**[0000320193-25-000079:1A:21]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company is exposed to the risk of write-downs on the value of its inventory and other assets, in addition to purchase commitment cancellation risk.
> The Company records a write-down for product and component inventories if cost exceeds net realizable value. The Company reviews other assets, including capital assets held at its suppliers' facilities, inventory prepayments and other long-lived assets, for impairment whenever events or circumstances indicate the assets may not be recoverable. Although the Company believes its inventory, capital assets, inventory prepayments and other assets are currently recoverable, the Company may incur write-downs, impairments and other charges given the rapid and unpredictable pace of product obsolescence in the industries in which the Company competes.

**[0000320193-25-000079:1A:36]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company has invested, and in the future may invest, in new business strategies, commercial relationships and acquisitions. Such endeavors may involve significant risks and uncertainties, including distraction of management from current operations, greater-than-expected liabilities and expenses, economic, political, legal and regulatory challenges associated with operating in new businesses, regions or countries, inadequate return on capital, potential impairment of tangible and intangible assets, and significant write-offs. Some transactions, including investments and acquisitions, are exposed to additional risks, including failing to obtain required regulatory approvals on a timely basis or at all, a counterparty's failure to perform or deliver as anticipated, or the imposition of onerous conditions that could delay or prevent the Company from completing a transaction or otherwise limit the Company's ability to fully realize the anticipated benefits of a transaction. New business strategies and ventures are inherently risky and may not be successful. The Company's business strategies and investments may not be successful, which could materially adversely affect the Company's business, reputation, results of operations, financial condition and stock price.
> Legal and Regulatory Compliance Risks
> The Company's business, results of operations and financial condition could be adversely impacted by unfavorable results of legal proceedings or government investigations.

**[0000320193-25-000079:1A:42]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Compliance with these laws and regulations is onerous and expensive. New and changing laws, regulations, executive orders, directives, and enforcement priorities can adversely affect the Company's business by increasing the Company's costs, limiting the Company's ability to offer a product, service or feature to customers, imposing changes to the design of the Company's products and services, impacting customer demand for the Company's products and services, and requiring changes to the Company's business or supply chain. New and changing laws, regulations, executive orders, directives, and enforcement priorities can also create uncertainty about how such laws and regulations will be interpreted and applied. If the Company is found to have violated such laws and regulations, it could materially adversely affect the Company's business, reputation, results of operations, financial condition and stock price.
> Risks and costs related to new and changing laws, regulations, executive orders, directives, and enforcement priorities increase as the Company's products and services are introduced into specialized applications, including health and financial services, or as the Company expands the use of technologies, such as machine learning and artificial intelligence features, and must navigate new legal, regulatory and ethical considerations relating to such technologies.

**[0000320193-25-000079:1A:44]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Various stakeholders, including governments, regulators, investors, employees, customers and others, have differing expectations about a wide range of social and other issues related to the Company's business. The Company makes statements about its values, including the environmental and societal impact of its business, through various reports, information provided on the Company's website, and in press statements and other communications. The Company also pursues environmental and other goals and initiatives that involve risks and uncertainties, require investments, and depend in part on third-party performance or data that is outside the Company's control, and the Company may not be able to fully achieve all of its goals and initiatives. Efforts by the Company to advance its business and values, or achieve its goals and further its initiatives, or to align with stakeholders' expectations, or comply with evolving, varied and at times conflicting federal, state and international laws, executive orders, regulations and standards, or any failure or perceived failure to do so, can result in adverse reactions by consumers and other stakeholders, including the commencement of legal and regulatory proceedings against the Company, and can materially adversely affect the Company's business, reputation, results of operations, financial condition and stock price.

**[0000320193-25-000079:1A:57]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company's investments can be negatively affected by changes in liquidity, credit deterioration, financial results, market and economic conditions, political risk, sovereign risk, interest rate fluctuations or other factors. As a result, the value and liquidity of the Company's cash, cash equivalents and marketable securities may fluctuate substantially. Although the Company has not realized significant losses on its cash, cash equivalents and marketable securities, future fluctuations in their value could result in significant losses and could have a material adverse impact on the Company's results of operations, financial condition and stock price.
> The Company is exposed to credit risk on its trade accounts receivable, vendor non-trade receivables and prepayments related to long-term supply agreements, and this risk is heightened during periods when economic conditions worsen.

**[0000320193-25-000079:1A:61]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company's stock has experienced substantial price volatility in the past and may continue to do so in the future. Additionally, the Company, the technology industry and the stock market as a whole have, from time to time, experienced extreme stock price and volume fluctuations that have affected stock prices in ways that may have been unrelated to these companies' operating performance. Price volatility may cause the average price at which the Company repurchases its stock in a given period to exceed the stock's price at a given point in time. The Company believes the price of its stock should reflect expectations of future growth and profitability. The Company also believes the price of its stock should reflect expectations that its cash dividend will continue at current levels or grow, and that its current share repurchase program will be fully consummated. Future dividends are subject to declaration by the Company's Board of Directors ("Board"), and the Company's share repurchase program does not obligate it to acquire any specific number of shares. If the Company fails to meet expectations related to future growth, profitability, dividends, share repurchases or other market expectations, the price of the Company's stock may decline significantly, which could have a material adverse impact on investor confidence and employee retention.

**[0000320193-25-000079:7:18]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company is subject to various legal proceedings and claims that arise in the ordinary course of business, the outcomes of which are inherently uncertain. The Company records a liability when it is probable a loss has been incurred and the amount is reasonably estimable, the determination of which requires significant judgment. Resolution of legal matters in a manner inconsistent with management's expectations could have a material impact on the Company's financial condition and operating results.

**Verdict:** found

**Note:** 

### AAPL · rational_capital_allocation

**Rational capital allocation.** Does the filing show what management does with the cash the business generates (reinvestment, acquisitions, buybacks, dividends, debt repayment) and explain it? You judge whether it is documented concretely, not whether prices paid were good.

- **found** ("evidence found"): The filing quantifies at least one past action in the fiscal year (share repurchases, dividends, acquisitions, capital expenditure or debt repayment, with an amount) AND states a policy, priority or rationale for how cash is used. Not every action needs an amount.
- **weak** ("evidence weak"): Forward-looking plans only; or actions with no amount at all; or amounts with no stated policy, priority or rationale.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what was done with cash, or MD&A is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.

Passages (Item 7), in filing order:

**[0000320193-25-000079:7:1]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
> The following discussion should be read in conjunction with the consolidated financial statements and accompanying notes included in Part II, Item 8 of this Form 10-K. This Item generally discusses 2025 and 2024 items and year-to-year comparisons between 2025 and 2024. Discussions of 2023 items and year-to-year comparisons between 2024 and 2023 are not included, and can be found in "Management's Discussion and Analysis of Financial Condition and Results of Operations" in Part II, Item 7 of the Company's Annual Report on Form 10-K for the fiscal year ended September 28, 2024.
> Product, Service and Software Announcements
> The Company announces new product, service and software offerings at various times during the year. Significant announcements during fiscal year 2025 included the following:
> First Quarter 2025:
> •MacBook Pro
> •Mac mini
> •iMac
> •iPad mini
> Second Quarter 2025:
> •iPhone 16e
> •iPad Air
> •iPad
> •MacBook Air
> •Mac Studio
> Third Quarter 2025:
> •iOS 26, macOS Tahoe 26, iPadOS 26, watchOS 26, visionOS 26 and tvOS 26
> Fourth Quarter 2025:
> •iPhone 17, iPhone Air, iPhone 17 Pro and iPhone 17 Pro Max

**[0000320193-25-000079:7:2]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> •Apple Watch Series 11, Apple Watch SE 3 and Apple Watch Ultra 3
> •AirPods Pro 3
> Fiscal Period
> The Company's fiscal year is the 52- or 53-week period that ends on the last Saturday of September. An additional week is included in the first fiscal quarter every five or six years to realign the Company's fiscal quarters with calendar quarters, which occurred in the first quarter of 2023. The Company's fiscal years 2025 and 2024 spanned 52 weeks each, whereas fiscal year 2023 spanned 53 weeks.
> Macroeconomic Conditions
> Macroeconomic conditions, including inflation, interest rates and currency fluctuations, have directly and indirectly impacted, and could in the future materially impact, the Company's results of operations and financial condition.
> Apple Inc. | 2025 Form 10-K | 21
> Tariffs and Other Measures

**[0000320193-25-000079:7:3]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Beginning in the second quarter of 2025, new U.S. Tariffs were announced, including additional tariffs on imports from China, India, Japan, South Korea, Taiwan, Vietnam and the EU, among others. In response, several countries have imposed, or threatened to impose, reciprocal tariffs on imports from the U.S. and other retaliatory measures. Various modifications to the U.S. Tariffs have been announced and further changes could be made in the future, which may include additional sector-based tariffs or other measures. For example, the U.S. Department of Commerce has initiated an investigation under Section 232 of the Trade Expansion Act of 1962, as amended, into, among other things, imports of semiconductors, semiconductor manufacturing equipment, and their derivative products, including downstream products that contain semiconductors. Tariffs and other measures that are applied to the Company's products or their components can have a material adverse impact on the Company's business, results of operations and financial condition, including impacting the Company's supply chain, the availability of rare earths and other raw materials and components, pricing and gross margin. The ultimate impact remains uncertain and will depend on several factors, including whether additional or incremental U.S. Tariffs or other measures are announced or imposed, to what extent other countries implement tariffs or other retaliatory measures in response, and the overall magnitude and duration of these measures. Trade and other international disputes can have an adverse impact on the overall macroeconomic environment and result in shifts and reductions in consumer spending and negative consumer sentiment for the Company's products and services, all of which can further adversely affect the Company's business and results of operations.

**[0000320193-25-000079:7:4]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Segment Operating Performance
> The following table shows net sales by reportable segment for 2025, 2024 and 2023 (dollars in millions):
> 2025 | Change | 2024 | Change | 2023
> Americas | $ | 178,353 | 7 | % | $ | 167,045 | 3 | % | $ | 162,560
> Europe | 111,032 | 10 | % | 101,328 | 7 | % | 94,294
> Greater China | 64,377 | (4) | % | 66,952 | (8) | % | 72,559
> Japan | 28,703 | 15 | % | 25,052 | 3 | % | 24,257
> Rest of Asia Pacific | 33,696 | 10 | % | 30,658 | 4 | % | 29,615
> Total net sales | $ | 416,161 | 6 | % | $ | 391,035 | 2 | % | $ | 383,285
> Americas
> Americas net sales increased during 2025 compared to 2024 primarily due to higher net sales of iPhone and Services. The weakness in foreign currencies relative to the U.S. dollar had an unfavorable year-over-year impact on Americas net sales during 2025.
> Europe
> Europe net sales increased during 2025 compared to 2024 primarily due to higher net sales of Services, iPhone and Mac.

**[0000320193-25-000079:7:10]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company's effective tax rate for 2025 was lower than the statutory federal income tax rate primarily due to a lower effective tax rate on foreign earnings, including the impact of changes in unrecognized tax benefits, the impact of the U.S. federal R&D credit, and tax benefits from share-based compensation, partially offset by a change in valuation allowance and state income taxes.
> The Company's effective tax rate for 2025 was lower compared to 2024 due to a $10.7 billion year-over-year decrease in the provision for income taxes related to the State Aid Decision (refer to Note 7, "Income Taxes" in the Notes to Consolidated Financial Statements in Part II, Item 8 of this Form 10-K) and the impact of changes in unrecognized tax benefits, partially offset by a change in valuation allowance and a higher effective tax rate on foreign earnings.
> Liquidity and Capital Resources
> The Company believes its balances of cash, cash equivalents and marketable securities, which totaled $132.4 billion as of September 27, 2025, along with cash generated by ongoing operations and continued access to debt markets, will be sufficient to satisfy its cash requirements and capital return program over the next 12 months and beyond.

**[0000320193-25-000079:7:12]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> Other Purchase Obligations
> The Company's other purchase obligations primarily consist of noncancelable obligations to acquire capital assets, including assets related to product manufacturing, and noncancelable obligations related to supplier arrangements, licensed intellectual property and content, and distribution rights. As of September 27, 2025, the Company had other purchase obligations of $14.8 billion, with $7.0 billion payable within 12 months.
> Deemed Repatriation Tax Payable
> As of September 27, 2025, the balance of the deemed repatriation tax payable imposed by the U.S. Tax Cuts and Jobs Act of 2017 ("TCJA") was $8.8 billion, which was payable within 12 months.
> Apple Inc. | 2025 Form 10-K | 25
> Capital Return Program
> In addition to its contractual cash requirements, the Company has an authorized share repurchase program. The program does not obligate the Company to acquire a minimum amount of shares. As of September 27, 2025, the Company's quarterly cash dividend was $0.26 per share. The Company intends to increase its dividend on an annual basis, subject to declaration by the Board.

**[0000320193-25-000079:7:13]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> In May 2025, the Company announced a new share repurchase program of up to $100 billion and raised its quarterly dividend from $0.25 to $0.26 per share beginning in May 2025. During 2025, the Company repurchased $89.3 billion of its common stock and paid dividends and dividend equivalents of $15.4 billion.
> Recent Accounting Pronouncements
> Internal-Use Software
> In September 2025, the Financial Accounting Standards Board ("FASB") issued Accounting Standards Update ("ASU") No. 2025-06, Intangibles—Goodwill and Other—Internal-Use Software (Subtopic 350-40): Targeted Improvements to the Accounting for Internal-Use Software ("ASU 2025-06"), which modernizes the accounting for internal-use software. ASU 2025-06 removes all references to software development stages and requires capitalization of software costs when management has committed to the software project and it is probable the software will be completed and perform its intended use. ASU 2025-06 will be effective for the Company in its first quarter of 2029, and early adoption is permitted. The Company is currently evaluating the timing and method of its adoption of ASU 2025-06.
> Disaggregation of Income Statement Expenses

**[0000320193-25-000079:7:18]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm)

> The Company is subject to various legal proceedings and claims that arise in the ordinary course of business, the outcomes of which are inherently uncertain. The Company records a liability when it is probable a loss has been incurred and the amount is reasonably estimable, the determination of which requires significant judgment. Resolution of legal matters in a manner inconsistent with management's expectations could have a material impact on the Company's financial condition and operating results.

**Verdict:**  Found

**Note:** 
Text here only mentions gains and buybacks. The company is investing heavily in R&D, but it isnt capture in these paragraphs. 

## MSFT

Form 10-K, accession 0001193125-26-323660, filed 2026-07-29, period 2026-06-30. [Open the filing on sec.gov](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

### MSFT · understandable_business

**Understandable business.** Can the business be explained simply: what the company sells, to whom, and how it makes money?

- **found** ("evidence found"): The filing names specific products or services, the customers or markets they are sold to, and how revenue is earned (for example segments with figures, a pricing or sales model), in plain terms.
- **weak** ("evidence weak"): The business is described only in general or promotional terms (a 'leading provider of solutions'), or the filing says what is sold but not who buys it or how it earns money.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what the company sells or how it earns money, or the Business section is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1), in filing order:

**[0001193125-26-323660:1:2]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> This report includes estimates, projections, statements relating to our business plans, objectives, and expected operating results that are "forward-looking statements" within the meaning of the Private Securities Litigation Reform Act of 1995, Section 27A of the Securities Act of 1933, and Section 21E of the Securities Exchange Act of 1934. Forward-looking statements may appear throughout this report, including the following sections: "Business" (Part I, Item 1 of this Form 10-K), "Risk Factors" (Part I, Item 1A of this Form 10-K), and "Management's Discussion and Analysis of Financial Condition and Results of Operations" (Part II, Item 7 of this Form 10-K). These forward-looking statements generally are identified by the words "believe," "project," "expect," "anticipate," "estimate," "intend," "strategy," "future," "opportunity," "plan," "may," "should," "will," "would," "could," "will be," "will continue," "will likely result," and similar expressions. Forward-looking statements are based on current expectations and assumptions that are subject to risks and uncertainties that may cause actual results to differ materially. We describe risks and uncertainties that could cause actual results and events to differ materially in "Risk Factors," "Management's Discussion and Analysis of Financial Condition and Results of Operations," and "Quantitative and Qualitative Disclosures About Market Risk" (Part II, Item 7A of this Form 10-K). Readers are cautioned not to place undue reliance on forward-looking statements, which speak only as of the date they are made. We undertake no obligation to update or revise publicly any forward-looking statements, whether because of new information, future events, or otherwise.

**[0001193125-26-323660:1:6]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> We are focused on helping customers use the breadth and depth of the Microsoft Cloud to get the most value out of their digital spend while leading the AI platform wave across our solution areas. We continue to develop complete, intelligent solutions for our customers that empower people to be productive and collaborate, while safeguarding businesses and simplifying IT management. Our goal is to lead the industry in several distinct areas of technology over the long term, which we expect will translate to sustained growth. We are investing significant resources in:
> •
> Tackling security from all angles with our integrated, end-to-end solutions spanning security, compliance, identity, and management, across all clouds and platforms.
> •
> Transforming the workplace to deliver new, modern, modular business applications, drive deeper insights, and improve how people communicate, collaborate, learn, work, and interact with one another.
> •
> Building and running cloud-based services in ways that utilize ubiquitous computing to unleash new experiences and opportunities for businesses and individuals.
> •
> Applying AI and ambient intelligence to drive insights, revolutionize many types of work and business processes, and provide substantive productivity gains using Microsoft 365 Copilot and agents.
> •

**[0001193125-26-323660:1:7]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Helping customers drive frontier transformation by applying frontier AI capabilities, engineering expertise, and trusted platforms to reinvent how their organizations operate, improve decision-making, create new value, and deliver measurable business outcomes from AI.
> •
> Providing a unified intelligence layer for enterprise AI to ground AI in a continuously evolving understanding of an organization's data.
> •
> Providing training on generative AI and greater access to digital learning and resources through skilling programs and initiatives, grants, and LinkedIn learning pathways.
> •
> Inventing new gaming experiences that bring people together around their shared love for games on any device and pushing the boundaries of innovation with console and PC gaming.
> •
> Leveraging Windows to fuel our cloud business, grow our share of the PC market, and drive increased engagement with our services like Microsoft Edge, Bing, Copilot, Microsoft Teams, Microsoft 365 Consumer, XBOX Game Pass, and more.
> Our future growth depends on our ability to transcend current product category definitions, business models, and sales motions.
> 4
> PART I
> Item 1
> Commitment to Sustainability

**[0001193125-26-323660:1:8]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Microsoft is committed to sustainability and our approach to addressing climate change starts with the sustainability of our own business. In 2020, we announced goals to become a carbon negative, water positive, and zero waste company by 2030. Since announcing these goals, we have seen major changes in both the technology sector and in our understanding of what it will take to meet our goals. More information about our progress toward these goals can be found in our annual Environmental Sustainability Report.
> OPERATING SEGMENTS
> We operate our business and report our financial performance using three segments: Productivity and Business Processes, Intelligent Cloud, and More Personal Computing. Our segments provide management with a comprehensive financial view of our key businesses. The segments enable the alignment of strategies and objectives across the development, sales, marketing, and services organizations, and they provide a framework for timely and rational allocation of resources within businesses.
> Additional information on our operating segments and geographic and product information is contained in Note 18 – Segment Information and Geographic Data of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).
> Our reportable segments are described below.
> Productivity and Business Processes

**[0001193125-26-323660:1:14]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Our Enterprise Mobility + Security offerings compete with products from a range of competitors including identity vendors, security solution vendors, and numerous other security point solution vendors.
> LinkedIn faces competition from online professional networks; recruiting, talent management, and human resource services companies; job boards; companies that provide learning and development products and services; online and offline outlets that generate revenue from advertisers and marketers; and online and offline outlets for companies with lead generation and customer intelligence and insights.
> Dynamics competes with cloud-based and on-premises business solution providers.
> Intelligent Cloud
> Our Intelligent Cloud segment consists of our public, private, and hybrid server products and cloud services that power modern business and developers. This segment primarily comprises:
> •
> Server products and cloud services, including Azure and other cloud services, comprising cloud and AI consumption-based services, GitHub cloud services, Health and Life Sciences cloud services (formerly Nuance Healthcare cloud services), virtual desktop offerings, and other cloud services; and Server products, comprising SQL Server, Windows Server, Visual Studio, System Center, related Client Access Licenses ("CALs"), and other on-premises offerings.
> •
> Enterprise and partner services, including Enterprise Support Services, Industry Solutions, Microsoft Partner Network, and Learning Experience.
> 6
> PART I
> Item 1

**[0001193125-26-323660:1:15]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Server Products and Cloud Services
> Azure is a comprehensive set of cloud services that offer developers, IT professionals, and enterprises freedom to build, deploy, and manage applications on any platform or device. Customers can use Azure through our global network of datacenters for computing, networking, storage, mobile and web application services, AI, and Internet of Things. Azure enables customers to devote more resources to development and use of applications that benefit their organizations, rather than managing on-premises hardware and software. Azure revenue is mainly affected by infrastructure-as-a-service and platform-as-a-service consumption-based services.
> Azure AI offerings provide a competitive advantage as companies seek ways to optimize and scale their business with AI. We offer supercomputing power for AI at scale to run large workloads, complemented by our rapidly expanding portfolio of AI cloud services (including the latest models) and hardware, which includes custom-built silicon and strong partnerships with chip manufacturers. Azure AI Foundry is a unified platform for developers to design, customize, and manage AI applications and agents.

**[0001193125-26-323660:1:19]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Our Enterprise and partner services business competes with a wide range of companies that provide strategy and business planning, application development, and infrastructure services, including multinational consulting firms and small niche businesses focused on specific technologies.
> More Personal Computing
> Our More Personal Computing segment consists of products and services that put customers at the center of the experience with our technology. This segment primarily comprises:
> •
> Windows and Devices, including Windows OEM licensing (Windows Pro and non-Pro licenses sold through the OEM channel) and Devices, comprising Surface and PC accessories.
> •
> XBOX (formerly Gaming), including XBOX hardware and XBOX content and services, comprising first- and third-party content (including games and in-game content), XBOX Game Pass and other subscriptions, XBOX Cloud Gaming, advertising, and other cloud services.
> •
> Search advertising (formerly Search and news advertising), comprising Bing, Copilot, Microsoft News, Microsoft Edge, and third-party affiliates.
> Windows and Devices

**[0001193125-26-323660:1:21]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> We design and sell devices, such as Surface (including Copilot+ PCs) and PC accessories. Our devices are designed to enable people and organizations to connect to the people and content that matter most using Windows and integrated Microsoft products and services. Surface is designed to help organizations, students, and consumers be more productive. Growth in Devices is dependent on total PC shipments, the ability to attract new customers, our product roadmap, and expanding into new categories.
> XBOX
> Microsoft is expanding how billions of people globally access and play video games on PC, console, mobile, and cloud. Our game content is developed through a collection of first-party studios creating iconic and differentiated gaming experiences. We continue to invest in gaming studios and content to expand our intellectual property roadmap and leverage new content creators. These unique gaming experiences are the cornerstone of XBOX Game Pass, a subscription service and gaming community with access to a curated library of first- and third-party titles.
> 8
> PART I
> Item 1

**Verdict:** Found

**Note:** 

### MSFT · durable_competitive_advantage

**Durable competitive advantage.** Does the filing give concrete evidence of an advantage that protects the company's profits from competitors over many years (for example a brand, scale or cost position, switching costs, a network, patents, or a regulated franchise)?

- **found** ("evidence found"): The filing states a source of advantage AND a checkable specific for it: a market share or rank figure; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated network size. A statement that an asset exists or matters (brand, trade secrets, patents, 'strong' distribution) without a measure is not enough.
- **weak** ("evidence weak"): The advantage is only asserted, or an asset is named as important (brand, trade secrets, patents, scale) without any measure; or the specifics are offset by the filing's own statements that competitors or customers can readily erode the position.
- **insufficient** ("insufficient evidence"): The retrieved text says nothing about the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1, Item 1A), in filing order:

**[0001193125-26-323660:1:15]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Server Products and Cloud Services
> Azure is a comprehensive set of cloud services that offer developers, IT professionals, and enterprises freedom to build, deploy, and manage applications on any platform or device. Customers can use Azure through our global network of datacenters for computing, networking, storage, mobile and web application services, AI, and Internet of Things. Azure enables customers to devote more resources to development and use of applications that benefit their organizations, rather than managing on-premises hardware and software. Azure revenue is mainly affected by infrastructure-as-a-service and platform-as-a-service consumption-based services.
> Azure AI offerings provide a competitive advantage as companies seek ways to optimize and scale their business with AI. We offer supercomputing power for AI at scale to run large workloads, complemented by our rapidly expanding portfolio of AI cloud services (including the latest models) and hardware, which includes custom-built silicon and strong partnerships with chip manufacturers. Azure AI Foundry is a unified platform for developers to design, customize, and manage AI applications and agents.

**[0001193125-26-323660:1:30]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> We protect our intellectual property investments in a variety of ways. We work actively in the U.S. and internationally to ensure the enforcement of copyright, patent, trademark, trade secret, and other protections that apply to our software and hardware products, services, business plans, and branding. While we employ much of our internally-developed intellectual property in our products and services, we also engage in outbound licensing of specific patented technologies that are incorporated into licensees' products. From time to time, we enter into broader cross-license agreements with other technology companies covering entire groups of patents. We may also purchase or license technology that we incorporate into our products and services. At times, we make select intellectual property broadly available at no or low cost to achieve a strategic objective, such as promoting industry standards, advancing interoperability, supporting societal and/or environmental efforts, or attracting and enabling our external development community. Our engagement with open-source software also causes us to license our intellectual property rights broadly in certain situations.

**[0001193125-26-323660:1A:8]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Our cloud and AI strategy requires substantial investments and depends on evolving customer demand, technological developments, competitive dynamics, and regulatory conditions, any of which could adversely affect our business, financial condition, and results of operations. We have made and are continuing to make significant capital and operational investments to develop, train, deploy, and support AI models and related cloud-based services, including building and expanding datacenters, acquiring necessary components, and securing energy resources. These investments are being made at significant scale and on an accelerated timeline, require substantial and increasing capital expenditures and continued access to capital, and are in advance of fully developed revenue streams. The associated revenue may not be realized in the expected timeframes or at expected levels. Our capital and operational investments are complex and involve projects in multiple locations around the world that expose us to increased compliance risks and political challenges, among others. Our ability to fund these investments depends on our ability to generate sufficient cash flows and obtain financing on acceptable terms. Adverse changes in interest rates, credit markets, investor sentiment, our credit ratings, or other factors affecting capital availability could increase our cost of capital or limit our ability to execute our infrastructure strategy. The financial success of these investments depends on a number of uncertain factors, including customer demand for cloud-based and AI products and services and continued customer use of Azure to build, train, deploy, and run AI workloads, our ability to price and monetize those services at levels sufficient to recover our costs, competitive dynamics affecting pricing, and the pace of adoption of AI. Customers may reduce, delay, or shift AI workloads to competing platforms, on-premises or local deployments, or other alternatives. If adoption of our AI services develops more slowly than expected, or if customers do not continue to utilize Azure for AI workloads at anticipated levels, we may not realize the expected returns on our investments.

**[0001193125-26-323660:1A:9]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> 15
> PART I
> Item 1A
> Demand for cloud-based and AI products and services is evolving and difficult to forecast. Overestimation of demand or misalignment of capacity investments may result in underutilization of infrastructure and may lead to impairment of assets on our balance sheet. Conversely, demand exceeding available capacity limits our ability to meet customer needs in a timely manner.
> The cost structure for AI products and services is subject to significant uncertainty, including with respect to model training and inference costs, the availability and pricing of components, and energy costs. If these costs increase, remain elevated, or fail to decline, or if pricing for AI products and services declines as a result of competition, commoditization, or other market forces, our margins, financial condition, and results of operations could be adversely affected.

**[0001193125-26-323660:1A:39]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> The availability, reliability, and cost of electrical power are critical to the operation and expansion of our datacenters. In many regions, electricity generation, transmission, and distribution infrastructure is experiencing increasing demand and capacity constraints. Limitations in power availability, delays in obtaining power connections, outages, shortages, increased energy costs, or requirements imposed by utilities, regulators, or other market participants could restrict our ability to develop or expand datacenter capacity. In addition, alternative energy sources and other emerging solutions may not be available in sufficient quantities, may not timely scale to meet our requirements, or may be available only at higher costs. If we are unable to secure adequate power resources on commercially reasonable terms, our ability to support customer demand and execute our growth strategy could be adversely affected.

**[0001193125-26-323660:1A:60]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> We earn a significant amount of our operating income outside the U.S. A change in the mix of earnings and losses in countries with differing statutory tax rates, changes in our business or structure, or the expiration of or disputes about certain tax agreements in a particular country may result in higher effective tax rates for the company. In addition, changes in U.S. federal and state or international tax laws applicable to corporate multinationals, other global fundamental law changes currently being considered by many countries, including in the U.S., and changes in taxing jurisdictions' administrative interpretations, decisions, policies, and positions could adversely affect our financial condition and results of operations.
> INTELLECTUAL PROPERTY RISKS
> We face risks related to the protection and utilization of our intellectual property that may result in our business and operating results being harmed. Protecting our intellectual property rights and combating unlicensed copying and use of our software, source code, trade secrets, and other intellectual property on a global basis is difficult. Similarly, the absence of harmonized patent laws makes it more difficult to ensure consistent respect for patent rights.

**[0001193125-26-323660:1A:61]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Source code, the detailed program commands for our software programs, is critical to our business. Unauthorized access to or disclosure of source code or other intellectual property may negatively impact future trade secret protection for that intellectual property. It may then become easier for third parties to compete with our products by copying functionality, which could adversely affect our results of operations. Unauthorized access to or disclosure of source code or other intellectual property also increases the security risks described elsewhere in these risk factors.

**[0001193125-26-323660:1A:64]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Social media may increase the likelihood, speed, and magnitude of negative brand events. If our brands or reputation are damaged, it could adversely affect our business, results of operations, or ability to attract the most highly qualified employees.
> Adverse economic or market conditions could harm our business. Worsening economic conditions, including inflation, recession, pandemic, or other changes in economic conditions, periods of economic uncertainty, evolution of customer demand, technology investment cycles, interest rates, foreign exchange rates, or the timing and mix of customer spending, may cause lower or delayed IT spending and adversely affect our results of operations. If demand for computing power, PCs, servers, and other computing devices declines, or consumer or business spending for those products declines, our results of operations could be adversely affected.
> Our product distribution system relies on an extensive partner and retail network. OEMs building devices that run our software have also been a significant means of distribution. The impact of economic conditions on our partners, such as the bankruptcy of a major distributor, OEM, or retailer, could cause sales channel disruption.

**Verdict:** found

**Note:** 

### MSFT · candid_management

**Candid management.** Does management openly discuss setbacks, mistakes, declines and uncertainty in its own words, rather than only successes?

- **found** ("evidence found"): Management's own account of a setback that it attributes at least partly to the company's own decisions or execution; or a target or guidance of its own that was missed; or an acknowledged material weakness, restatement or write-down of something management chose (an acquisition, investment or project), stated plainly.
- **weak** ("evidence weak"): Declines or charges explained only by external factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even when quantified; or generic caution ('results may fluctuate', 'we face risks'); or a setback mentioned without explanation.
- **insufficient** ("insufficient evidence"): The retrieved text is promotional or boilerplate and gives nothing to judge candour either way, or MD&A and Risk Factors are missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.
- **Limitation:** Limitation: 10-K text is reviewed by lawyers, and candour is better judged from shareholder letters (outside this tool's scope). Do not read polished or detailed prose as candour;

Passages (Item 7, Item 1A), in filing order:

**[0001193125-26-323660:1A:10]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Our AI strategy also depends in part on strategic relationships with third parties that provide technologies, models, products, and services that enhance our offerings. These relationships may change over time, and many of these partners compete with us with respect to certain products and services. Changes in strategic priorities, contractual arrangements, our access to third-party technologies, or key commercial relationships could adversely affect the competitiveness of our AI products and services. In some cases, these parties are significant customers of Azure and other cloud services. The economic benefits we expect to derive from these relationships, including through commercial arrangements, technology access, and Azure consumption, may not be realized or sustained. As we manage infrastructure capacity constraints and evolving customer demand, we may modify capacity allocations, deployment priorities, pricing, or other commercial arrangements. Strategic partners and other customers may likewise adjust their purchasing decisions, deployment strategies, workloads, or anticipated use of our products and services. As a result, expected consumption or anticipated demand may not materialize, may be delayed or reduced, or may decline over time. Any such developments could adversely affect our business, financial condition, and results of operations.

**[0001193125-26-323660:1A:14]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> We make significant investments in products and services that may not achieve expected returns. We will continue to make significant investments in research, development, and marketing for existing products, services, and technologies, including AI-based products and services. We also invest in the development and acquisition of a variety of hardware for productivity, communication, and entertainment, including PCs, tablets, and gaming devices. Investments in new technology are speculative. Commercial success depends on many factors, including innovation, developer support, and effective distribution and marketing. If customers do not perceive our latest offerings as providing significant new functionality or other value, they may reduce their purchases of new software and hardware products or upgrades, unfavorably affecting revenue. We may not achieve significant revenue from new product, service, and distribution channel investments for several years, if at all. New products and services may not be profitable or may not achieve operating margins as high as we have experienced historically. We may not get engagement in certain features that drive post-sale monetization opportunities. Our data-handling practices across our products and services will continue to be under scrutiny. Perceptions of mismanagement, driven by regulatory activity or negative public reaction to our practices or product experiences, could negatively impact product and feature adoption. Developing new technologies is complex. It can require long development and testing periods. We could experience significant delays in new releases or significant problems in creating new products or services. These factors could adversely affect our business, financial condition, and results of operations.

**[0001193125-26-323660:1A:15]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Acquisitions, joint ventures, and strategic alliances could have an adverse effect on our business. We expect to continue making acquisitions and entering into joint ventures and strategic alliances as part of our long-term business strategy. For example, in October 2023 we completed our acquisition of Activision Blizzard, Inc. Additionally, we have a long-term strategic partnership with OpenAI. Acquisitions and other transactions and arrangements involve significant challenges and risks, including that they do not advance our business strategy, that we get an unsatisfactory return on our investment, that they raise new compliance-related obligations and challenges, that we have difficulty integrating and retaining new employees, business systems, and technology, that they distract management from our other businesses, or that announced transactions may not be completed. If an arrangement fails to adequately anticipate changing circumstances and interests of a party, it may result in early termination or renegotiation of the arrangement. We also have limited ability to control or influence third parties with whom we have arrangements, which may impact our ability to realize the anticipated benefits. The success of these transactions and arrangements depend in part on our ability to leverage them to enhance our existing products and services or develop compelling new ones, as well as the acquired companies' ability to meet our policies and processes in areas such as data governance, privacy, digital safety, responsible AI, and cybersecurity. It may take longer than expected to realize the full economic benefits from these transactions and arrangements, such as increased revenue or enhanced efficiencies, or the benefits may ultimately be smaller than we expected, which could cause an impairment of goodwill or intangibles. We have recorded, and may in the future be required to record, a significant charge in our consolidated financial statements during the period in which any impairment of our goodwill or amortizable intangible assets is determined, negatively affecting our results of operations. In addition, these transactions and arrangements have been and may be subject to legal and regulatory challenge. These events could adversely affect our business, operations, financial condition, and results of operations.

**[0001193125-26-323660:1A:55]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> How these laws and regulations apply to our business is often unclear, subject to change, and sometimes may conflict or be inconsistent from jurisdiction to jurisdiction. In addition, governments' approach to enforcement, and our products and services, are continuing to evolve. Compliance with existing, expanding, or new laws and regulations may involve significant costs and operational efforts, or require changes in products or business practices that could adversely affect our results of operations. Noncompliance could result in the imposition of penalties, criminal sanctions, or orders to cease the alleged noncompliant activity. If our products do not meet customer expectations or legal requirements, we could face regulatory or legal actions, and our business, operations, financial condition, and results of operations could be adversely affected.

**[0001193125-26-323660:1A:65]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Challenging economic conditions also may impair the ability of our customers to pay for products and services they have purchased. As a result, allowances for doubtful accounts and write-offs of accounts receivable may increase.
> We maintain an investment portfolio of various holdings, types, and maturities. These investments are subject to general credit, liquidity, market, and interest rate risks, which may be exacerbated by market downturns or events that affect global financial markets. A significant part of our investment portfolio consists of U.S. government securities. If global financial markets decline for long periods, or if there is a downgrade of the U.S. government credit rating due to an actual or threatened default on government debt, our investment portfolio could be adversely affected and we could determine that more of our investments have experienced a decline in fair value, requiring impairment charges that could adversely affect our financial condition and results of operations.

**[0001193125-26-323660:7:1]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Item 7
> ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS
> The following Management's Discussion and Analysis of Financial Condition and Results of Operations ("MD&A") is intended to help the reader understand the results of operations and financial condition of Microsoft Corporation. MD&A is provided as a supplement to, and should be read in conjunction with, our consolidated financial statements and the accompanying Notes to Financial Statements (Part II, Item 8 of this Form 10-K). This section generally discusses the results of our operations for the year ended June 30, 2026 compared to the year ended June 30, 2025. For a discussion of the year ended June 30, 2025 compared to the year ended June 30, 2024, please refer to Part II, Item 7, "Management's Discussion and Analysis of Financial Condition and Results of Operations" in our Annual Report on Form 10-K for the year ended June 30, 2025.
> OVERVIEW

**[0001193125-26-323660:7:6]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Our success is highly dependent on our ability to attract and retain qualified employees. We hire a mix of university and industry talent worldwide. We compete for talented individuals globally by offering an exceptional working environment, broad customer reach, scale in resources, the ability to grow one's career across many different products and businesses, and competitive compensation and benefits.
> Our international operations provide a significant portion of our total revenue and expenses. Many of these revenue and expenses are denominated in currencies other than the U.S. dollar. As a result, changes in foreign exchange rates may significantly affect revenue and expenses. Fluctuations in the U.S. dollar relative to certain foreign currencies increased reported revenue and did not have a material impact on reported expenses from our international operations in fiscal year 2026.
> Further, global, regional, and local economic developments and changes in global trade policies such as restrictions on international trade, including tariffs and other controls on imports or exports, could result in increased supply chain challenges, cost volatility, and consumer and economic uncertainty which may adversely affect our results of operations.

**[0001193125-26-323660:7:41]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> We review debt investments quarterly for credit losses and impairment. If the cost of an investment exceeds its fair value, we evaluate, among other factors, general market conditions, credit quality of debt instrument issuers, and the extent to which the fair value is less than cost. This determination requires significant judgment. In making this judgment, we employ a systematic methodology that considers available quantitative and qualitative evidence in evaluating potential impairment of our investments. In addition, we consider specific adverse conditions related to the financial health of, and business outlook for, the investee. If we have plans to sell the security or it is more likely than not that we will be required to sell the security before recovery, then a decline in fair value below cost is recorded as an impairment charge in other income (expense), net and a new cost basis in the investment is established. If market, industry, and/or investee conditions deteriorate, we may incur future impairments.

**Verdict:** Found

**Note:** 

### MSFT · rational_capital_allocation

**Rational capital allocation.** Does the filing show what management does with the cash the business generates (reinvestment, acquisitions, buybacks, dividends, debt repayment) and explain it? You judge whether it is documented concretely, not whether prices paid were good.

- **found** ("evidence found"): The filing quantifies at least one past action in the fiscal year (share repurchases, dividends, acquisitions, capital expenditure or debt repayment, with an amount) AND states a policy, priority or rationale for how cash is used. Not every action needs an amount.
- **weak** ("evidence weak"): Forward-looking plans only; or actions with no amount at all; or amounts with no stated policy, priority or rationale.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what was done with cash, or MD&A is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.

Passages (Item 7), in filing order:

**[0001193125-26-323660:7:1]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Item 7
> ITEM 7. MANAGEMENT'S DISCUSSION AND ANALYSIS OF FINANCIAL CONDITION AND RESULTS OF OPERATIONS
> The following Management's Discussion and Analysis of Financial Condition and Results of Operations ("MD&A") is intended to help the reader understand the results of operations and financial condition of Microsoft Corporation. MD&A is provided as a supplement to, and should be read in conjunction with, our consolidated financial statements and the accompanying Notes to Financial Statements (Part II, Item 8 of this Form 10-K). This section generally discusses the results of our operations for the year ended June 30, 2026 compared to the year ended June 30, 2025. For a discussion of the year ended June 30, 2025 compared to the year ended June 30, 2024, please refer to Part II, Item 7, "Management's Discussion and Analysis of Financial Condition and Results of Operations" in our Annual Report on Form 10-K for the year ended June 30, 2025.
> OVERVIEW

**[0001193125-26-323660:7:22]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Interest and dividends income increased primarily due to higher portfolio balances and higher yields on debt securities. Interest expense increased primarily due to higher finance lease interest expense, offset in part by higher capitalization of debt interest expense. Net recognized gains on investments increased primarily due to higher gains on equity securities and lower impairments in the current period. Net gains on derivatives increased primarily due to gains on equity derivatives in the current period as compared to losses in the prior period. Other, net primarily reflects net recognized gains on equity method investments, including OpenAI.
> INCOME TAXES
> Effective Tax Rate
> Our effective tax rate for fiscal years 2026 and 2025 was 19% and 18%, respectively. The increase in our effective tax rate was primarily due to changes in the mix of our earnings and tax expenses between the U.S. and foreign countries.
> Our effective tax rate was lower than the U.S. federal statutory rate, primarily due to earnings taxed at lower rates in foreign jurisdictions resulting from producing and distributing our products and services through our foreign regional operations center in Ireland.

**[0001193125-26-323660:7:26]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> We expect existing cash, cash equivalents, short-term investments, cash flows from operations, and access to capital markets to continue to be sufficient to fund our operating activities and cash commitments for investing and financing activities, such as dividends, share repurchases, debt maturities, and material capital expenditures, for at least the next 12 months and thereafter for the foreseeable future.
> 42
> PART II
> Item 7
> Cash, Cash Equivalents, and Investments

**[0001193125-26-323660:7:30]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Cash from operations increased $46.8 billion to $182.9 billion for fiscal year 2026, primarily due to an increase in cash received from customers and a decrease in cash used to pay income taxes, offset in part by an increase in cash paid to suppliers. Cash used in financing increased $847 million to $52.5 billion for fiscal year 2026, primarily due to a $6.0 billion decrease in cash used for repayments of debt, offset in part by a $3.9 billion increase in common stock repurchases and a $2.4 billion increase in dividends paid. Cash used in investing increased $66.9 billion to $139.5 billion for fiscal year 2026, primarily due to a $51.4 billion increase in additions to property and equipment and a $22.2 billion increase in cash used in other investing primarily to facilitate the purchase of components, offset in part by a $4.2 billion decrease in cash used in the acquisition of companies, net of cash acquired and divestitures, and purchases of intangible and other assets and a $2.4 billion decrease in cash used in net investment purchases, sales, and maturities.
> Debt Proceeds

**[0001193125-26-323660:7:31]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> We issue debt to take advantage of favorable pricing and liquidity in the debt markets, reflecting our credit rating. The proceeds of these issuances were or will be used for general corporate purposes, which may include, among other things, funding for working capital, capital expenditures, repurchases of capital stock, acquisitions, and repayment of existing debt. Refer to Note 10 – Debt of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).
> 43
> PART II
> Item 7
> Unearned Revenue
> Unearned revenue comprises mainly unearned revenue related to volume licensing programs, which may include cloud services and Software Assurance ("SA"). Unearned revenue is generally invoiced annually at the beginning of each contract period for multi-year agreements and recognized ratably over the coverage period. Unearned revenue also includes payments for other offerings for which we have been paid in advance and earn the revenue when we transfer control of the product or service. Refer to Note 1 – Accounting Policies of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).
> The following table outlines the expected future recognition of unearned revenue as of June 30, 2026:
> (In millions)
> Three Months Ending

**[0001193125-26-323660:7:33]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Total | $ | 241,922 | $ | 501,899 | $ | 743,821
> (a)
> Refer to Note 10 – Debt of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).
> (b)
> Refer to Note 6 – Property and Equipment of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).
> (c)
> Refer to Note 13 – Leases of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).
> (d)
> Purchase commitments primarily relate to datacenters and include open purchase orders and take-or-pay contracts that are not presented as construction commitments above.
> Share Repurchases
> During fiscal years 2026 and 2025, we repurchased 36 million shares and 31 million shares of our common stock for $16.7 billion and $13.0 billion, respectively, through our share repurchase program. All repurchases were made using cash resources. As of June 30, 2026, $40.6 billion remained of our $60 billion share repurchase program. Refer to Note 15 – Stockholders' Equity of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).
> 44
> PART II
> Item 7
> Dividends

**[0001193125-26-323660:7:34]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> During fiscal years 2026 and 2025, our Board of Directors declared dividends totaling $27.0 billion and $24.7 billion, respectively. We intend to continue returning capital to shareholders in the form of dividends, subject to declaration by our Board of Directors. Refer to Note 15 – Stockholders' Equity of the Notes to Financial Statements (Part II, Item 8 of this Form 10-K).
> Other Planned Uses of Capital
> We will continue to invest in sales, marketing, product support infrastructure, and existing and advanced areas of technology, as well as acquisitions that align with our business strategy. Additions to property and equipment will continue, including new facilities, datacenters, and computer systems for research and development, sales and marketing, support, and administrative staff. We will continue to invest in capital expenditures to support growth in our cloud offerings and our investments in AI training and other infrastructure. We have operating and finance leases for datacenters and related infrastructure, servers and network equipment, corporate offices, and research and development facilities. We have not engaged in any related party transactions or arrangements with unconsolidated entities or other persons that are reasonably likely to materially affect liquidity or the availability of capital resources.
> RECENT ACCOUNTING GUIDANCE

**[0001193125-26-323660:7:44]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm)

> Application of the goodwill impairment test requires judgment, including the identification of reporting units, assignment of assets and liabilities to reporting units, assignment of goodwill to reporting units, and determination of the fair value of each reporting unit. The fair value of each reporting unit is estimated primarily through the use of a discounted cash flow methodology. This analysis requires significant judgments, including estimation of future cash flows, which is dependent on internal forecasts, estimation of the long-term rate of growth for our business, the period over which cash flows are expected to be generated, and determination of our weighted average cost of capital.
> The estimates used to calculate the fair value of a reporting unit change from year to year based on operating results, market conditions, and other factors. Changes in these estimates and assumptions could materially affect the determination of fair value and goodwill impairment for each reporting unit.
> Research and Development Costs

**Verdict:** Found

**Note:** 

---

## PG

Form 10-K, accession 0000080424-26-000103, filed 2026-08-04, period 2026-06-30. [Open the filing on sec.gov](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

### PG · understandable_business

**Understandable business.** Can the business be explained simply: what the company sells, to whom, and how it makes money?

- **found** ("evidence found"): The filing names specific products or services, the customers or markets they are sold to, and how revenue is earned (for example segments with figures, a pricing or sales model), in plain terms.
- **weak** ("evidence weak"): The business is described only in general or promotional terms (a 'leading provider of solutions'), or the filing says what is sold but not who buys it or how it earns money.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what the company sells or how it earns money, or the Business section is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1), in filing order:

**[0000080424-26-000103:1:2]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> The Company's Annual Report on Form 10-K, quarterly reports on Form 10-Q and current reports on Form 8-K, and amendments thereto, are filed electronically with the SEC. The SEC maintains an internet site that contains these reports at: www.sec.gov. Reports can also be accessed and downloaded through links from our website at: www.pginvestor.com. P&G includes the website link solely as a textual reference and the information on our website is not incorporated by reference into this report. Copies of these reports are also available, without charge, by contacting EQ Shareowner Services, 1100 Centre Pointe Curve, Suite 101, Mendota, MN 55120-4100.
> Financial Information about Segments
> Information about our reportable segments can be found in the MD&A and Note 2 to our Consolidated Financial Statements.
> Narrative Description of Business

**[0000080424-26-000103:1:3]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Business Model. Our business model is focused on delivering sustainable value creation by driving balanced top- and bottom-line growth. We create, manufacture, market and distribute a diversified portfolio of daily-use products to delight consumers with irresistible superiority across five key vectors - product performance, packaging, brand communication, retail execution and value. We invest in research and development and consumer insights to invent new categories or products and innovate our existing products, ensuring they meet evolving consumer needs and preferences. We leverage marketing strategies including advertising, promotions and endorsements to drive brand awareness and loyalty among consumers. The Company utilizes various distribution channels, including retail stores, digital commerce platforms and direct-to-consumer platforms to deliver our products. Our business model relies on continued productivity improvements to fuel investments in research and development and marketing and deliver value creation. Our objective is to deliver sustainable and balanced top- and bottom-line growth while serving the needs of all stakeholders — consumers, customers, employees, society and shareowners.
> Key Product Categories. Information on key product categories can be found in the MD&A and Note 2 to our Consolidated Financial Statements.

**[0000080424-26-000103:1:5]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Sources and Availability of Materials. Almost all of the raw and packaging materials used by the Company are purchased from third parties, some of whom are single-source suppliers. We produce certain raw materials, primarily chemicals, for further use in the manufacturing process. In addition, fuel, natural gas and derivative products are important commodities consumed in our manufacturing processes and in the transportation of input materials and finished products. The prices we pay for materials and other commodities are subject to fluctuation including new or increased tariffs. When prices for these items change, we may or may not pass the change to our customers. The Company purchases a substantial variety of other raw and packaging materials, none of which are material to our business taken as a whole.
> Trademarks and Patents. We own or have rights to patents and trademarks, which are used in connection with our activity in all businesses. Our patents cover a range of product features, including significant product formulation and processes used to manufacture our products. The trademarks are important to the overall marketing and branding of our products. In part, our success can be attributed to the existence and continued protection of these trademarks and patents.

**[0000080424-26-000103:1:6]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Competitive Condition. The markets in which our products are sold are highly competitive. Our products compete against similar products from a broad range of companies, both large and small, both established and new, including well-known global competitors. In many of the markets and industry segments, we compete against other branded products as well as retailers' private-label brands. In this highly competitive setting, we are well positioned in the industry segments and markets in which we operate, often holding a leadership or significant market share position. Our integrated strategy and our focus on driving superiority across product, packaging, brand communication, retail execution and value are key differentiators in the marketplace.
> 2 The Procter & Gamble Company

**[0000080424-26-000103:1:8]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> The Company has in place compliance programs and internal and external experts to help guide our business in complying with these and other existing laws and regulations that apply to us around the globe; and we have made, and plan to continue making, necessary expenditures for compliance with these laws and regulations. We also expect that our many suppliers, consultants and other third parties working on our behalf share our commitment to compliance, and we have policies and procedures in place to manage these relationships, though they inherently involve a lesser degree of control over operations and governance. We do not expect that the Company's expenditures for compliance with current government regulations, including current environmental regulations, will have a material effect on our total capital expenditures, earnings or competitive position in fiscal year 2027 as compared to prior periods.
> Human Capital. Our employees are a key source of competitive advantage. Their actions, guided by our Purpose, Values and Principles (PVPs), are critical to the long-term success of our business. We aim to retain our talented employees by offering competitive compensation and benefits, strong career development and a respectful and inclusive culture that provides equal opportunity for all.

**[0000080424-26-000103:1:9]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Our Board of Directors, through the Compensation and Leadership Development Committee (C&LD Committee), provides oversight of the Company's policies and strategy relating to talent, including equality and inclusion, as well as the Company's compensation principles and practices. The C&LD Committee also evaluates and approves the Company's compensation plans, policies and programs applicable to our senior executives.
> Employees
> As of June 30, 2026, the Company had approximately 104,000 employees, a decrease of 4% versus the prior year due to the ongoing restructuring program. See Note 3 for further details on the restructuring program. The total number of employees is an estimate of total Company employees excluding interns, co-ops, contractors and employees of joint ventures. 49% of our employees are in manufacturing roles and 28% of our employees are located in the United States. 42% of our global employees are women and 33% of our U.S. employees identify as multicultural.
> Training and Development

**[0000080424-26-000103:1:11]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> As a global consumer products company, P&G serves consumers around the world with operations in approximately 65 countries. We believe that it is good for business that our workforce is drawn from the best available talent from communities worldwide, with insights about, connectivity to and understanding of all our consumers. Further, a foundational component of P&G's strategy and success has been to foster an inclusive work environment, in which we develop and advance the very best capabilities that all our people have to offer. Globally, we aspire to reflect the diversity of the consumers we serve in the communities where we operate and are committed to creating a superior employee experience for all. Our aspiration is founded on our longstanding values and principles for equal opportunity and compliance with the law.
> Compensation and Benefits

**[0000080424-26-000103:1:12]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Market-competitive compensation and reward programs are critical elements of our employee value equation to attract and retain the best talent. Our total rewards programs are based on the principles of paying for performance, paying competitively versus peer companies that we compete with for talent in the marketplace and focusing on long-term success through a combination of short-term and long-term incentive programs. We also offer competitive benefit programs, including retirement plans and health insurance, in line with local country practices, with flexibility to accommodate the needs of a diverse workforce.
> Sustainability. Environmental sustainability is integrated into our business strategy. We are focused on designing and manufacturing irresistibly superior products that are more sustainable. We aim to reduce our own environmental footprint and
> The Procter & Gamble Company 3
> enable our consumers to reduce their footprint without compromising on the performance of the products they use. We develop and license technologies that can be used across industries to improve environmental sustainability at a broader scale.
> Combined, this approach intends to positively impact the total environmental impact of the Company while driving market growth and value creation.

**Verdict:** Found

**Note:** 


### PG · durable_competitive_advantage

**Durable competitive advantage.** Does the filing give concrete evidence of an advantage that protects the company's profits from competitors over many years (for example a brand, scale or cost position, switching costs, a network, patents, or a regulated franchise)?

- **found** ("evidence found"): The filing states a source of advantage AND a checkable specific for it: a market share or rank figure; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated network size. A statement that an asset exists or matters (brand, trade secrets, patents, 'strong' distribution) without a measure is not enough.
- **weak** ("evidence weak"): The advantage is only asserted, or an asset is named as important (brand, trade secrets, patents, scale) without any measure; or the specifics are offset by the filing's own statements that competitors or customers can readily erode the position.
- **insufficient** ("insufficient evidence"): The retrieved text says nothing about the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1, Item 1A), in filing order:

**[0000080424-26-000103:1:5]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Sources and Availability of Materials. Almost all of the raw and packaging materials used by the Company are purchased from third parties, some of whom are single-source suppliers. We produce certain raw materials, primarily chemicals, for further use in the manufacturing process. In addition, fuel, natural gas and derivative products are important commodities consumed in our manufacturing processes and in the transportation of input materials and finished products. The prices we pay for materials and other commodities are subject to fluctuation including new or increased tariffs. When prices for these items change, we may or may not pass the change to our customers. The Company purchases a substantial variety of other raw and packaging materials, none of which are material to our business taken as a whole.
> Trademarks and Patents. We own or have rights to patents and trademarks, which are used in connection with our activity in all businesses. Our patents cover a range of product features, including significant product formulation and processes used to manufacture our products. The trademarks are important to the overall marketing and branding of our products. In part, our success can be attributed to the existence and continued protection of these trademarks and patents.

**[0000080424-26-000103:1:6]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Competitive Condition. The markets in which our products are sold are highly competitive. Our products compete against similar products from a broad range of companies, both large and small, both established and new, including well-known global competitors. In many of the markets and industry segments, we compete against other branded products as well as retailers' private-label brands. In this highly competitive setting, we are well positioned in the industry segments and markets in which we operate, often holding a leadership or significant market share position. Our integrated strategy and our focus on driving superiority across product, packaging, brand communication, retail execution and value are key differentiators in the marketplace.
> 2 The Procter & Gamble Company

**[0000080424-26-000103:1:8]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> The Company has in place compliance programs and internal and external experts to help guide our business in complying with these and other existing laws and regulations that apply to us around the globe; and we have made, and plan to continue making, necessary expenditures for compliance with these laws and regulations. We also expect that our many suppliers, consultants and other third parties working on our behalf share our commitment to compliance, and we have policies and procedures in place to manage these relationships, though they inherently involve a lesser degree of control over operations and governance. We do not expect that the Company's expenditures for compliance with current government regulations, including current environmental regulations, will have a material effect on our total capital expenditures, earnings or competitive position in fiscal year 2027 as compared to prior periods.
> Human Capital. Our employees are a key source of competitive advantage. Their actions, guided by our Purpose, Values and Principles (PVPs), are critical to the long-term success of our business. We aim to retain our talented employees by offering competitive compensation and benefits, strong career development and a respectful and inclusive culture that provides equal opportunity for all.

**[0000080424-26-000103:1:12]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Market-competitive compensation and reward programs are critical elements of our employee value equation to attract and retain the best talent. Our total rewards programs are based on the principles of paying for performance, paying competitively versus peer companies that we compete with for talent in the marketplace and focusing on long-term success through a combination of short-term and long-term incentive programs. We also offer competitive benefit programs, including retirement plans and health insurance, in line with local country practices, with flexibility to accommodate the needs of a diverse workforce.
> Sustainability. Environmental sustainability is integrated into our business strategy. We are focused on designing and manufacturing irresistibly superior products that are more sustainable. We aim to reduce our own environmental footprint and
> The Procter & Gamble Company 3
> enable our consumers to reduce their footprint without compromising on the performance of the products they use. We develop and license technologies that can be used across industries to improve environmental sustainability at a broader scale.
> Combined, this approach intends to positively impact the total environmental impact of the Company while driving market growth and value creation.

**[0000080424-26-000103:1A:13]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Our businesses face cost fluctuations and pressures that could affect our results.
> Our costs are subject to fluctuations, particularly due to changes in the prices of commodities (including certain petroleum-derived materials like resins and paper-based materials like pulp), raw and packaging materials and the costs of labor, tariffs, transportation (including trucks and containers), energy, pensions and healthcare. Inflation pressures sometimes result in increases in these input costs. Therefore, our business results depend, in part, on our continued ability to manage these fluctuations through pricing actions, cost saving projects and sourcing decisions, while maintaining and improving margins and market share. Failure to manage these fluctuations and to anticipate consumer reaction to our management of these fluctuations could adversely impact our results of operations or cash flows.
> The ability to achieve our business objectives depends on how well we can compete with our local and global competitors in new and existing markets and channels.

**[0000080424-26-000103:1A:24]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> A breach of our data security systems or digital customer products, such as connected devices, or failure of our IT/OT databases and systems and those of our third-parties may have a material adverse impact on our business operations and financial results. If the IT/OT systems, networks or service providers we rely upon fail to function properly or cause operational outages or aberrations, or if we or one of our third-party providers suffer significant unavailability of key operations, or inadvertent disclosure of, lack of integrity of, or loss of our sensitive business or stakeholder information, including personal information, due to any number of causes, including catastrophic events, natural disasters, power outages, computer and telecommunications failures, improper data handling, viruses, phishing attempts, cyber-attacks, malware and ransomware attacks, security incidents, misuse or malicious use of AI or employee error or malfeasance, and our business continuity plans do not effectively address these failures on a timely basis, we may suffer interruptions in our ability to manage operations and be exposed to reputational, competitive, operational, financial and business harm as well as litigation and regulatory action. If our critical IT systems or back-up systems or those of our third-party vendors are damaged or cease to function properly, we may have to make a significant investment to repair or replace them.

**[0000080424-26-000103:1A:27]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> We are a consumer products company that relies on continued global demand for our brands and products, and consumer expectations and purchasing habits are evolving at an accelerating pace. Achieving our business results depends, in part, on successfully developing, introducing and marketing new products and on making significant improvements to our equipment and manufacturing processes. The success of such innovation depends on our ability to correctly anticipate customer and consumer acceptance and trends at the pace at which they are evolving, to obtain, maintain and enforce necessary intellectual property protections and to avoid infringing upon the intellectual property rights of others and to continue to deliver efficient and effective marketing across evolving and more fragmented media and mobile platforms with dynamic and increasingly more restrictive privacy requirements. We must also successfully respond to technological advances made by, and intellectual property rights granted to, competitors, customers and vendors. Failure to continually innovate, improve and respond to competitive moves, changing consumer habits and platform evolution, including the timely, responsible and effective adoption of emerging technologies such as AI, could compromise our competitive position and adversely impact our financial condition, results of operations or cash flows.

**[0000080424-26-000103:1A:30]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Our financial projections assume certain new and ongoing productivity improvements and cost savings, including staffing adjustments and employee departures. Failure to deliver these planned productivity improvements and cost savings, while continuing to invest in business growth, could adversely impact our results of operations and cash flows. Additionally, successfully executing organizational change, management transitions at leadership levels of the Company and motivation and retention of key employees is critical to our business success. Factors that may affect our ability to attract and retain sufficient numbers of qualified employees include: employee morale; our reputation; the impacts of political, social and geopolitical polarization; competition from other employers and availability of qualified individuals. Our success depends on identifying, developing and retaining key employees to provide uninterrupted leadership and direction for our business. This includes developing and retaining organizational capabilities in key growth markets where the depth of skilled or experienced employees may be limited and competition for these resources is intense as well as continuing the development and execution of robust leadership succession plans. It also includes continuing to attract, develop and retain employees that adapt to new ways of working and new technologies in a rapidly changing environment.
> LEGAL & REGULATORY RISKS

**Verdict:** insufficient

**Note:** 

### PG · candid_management

**Candid management.** Does management openly discuss setbacks, mistakes, declines and uncertainty in its own words, rather than only successes?

- **found** ("evidence found"): Management's own account of a setback that it attributes at least partly to the company's own decisions or execution; or a target or guidance of its own that was missed; or an acknowledged material weakness, restatement or write-down of something management chose (an acquisition, investment or project), stated plainly.
- **weak** ("evidence weak"): Declines or charges explained only by external factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even when quantified; or generic caution ('results may fluctuate', 'we face risks'); or a setback mentioned without explanation.
- **insufficient** ("insufficient evidence"): The retrieved text is promotional or boilerplate and gives nothing to judge candour either way, or MD&A and Risk Factors are missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.
- **Limitation:** Limitation: 10-K text is reviewed by lawyers, and candour is better judged from shareholder letters (outside this tool's scope). Do not read polished or detailed prose as candour;

Passages (Item 7, Item 1A), in filing order:

**[0000080424-26-000103:1A:9]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> For example, the ongoing war between Russia and Ukraine has negatively impacted, and the situation it generates may continue to negatively impact, our operations. Future impacts to the Company are difficult to predict due to the high level of uncertainty as to how the overall situation will continue to evolve. We may reduce further or discontinue our operations in Russia due to significant and cumulative sanctions and export controls and counter-sanctions, monetary, currency or payment controls, restrictions on data transfers or access to financial institutions and services, supply and transportation challenges or other circumstances and considerations. In addition to operational disruptions, these factors could result in loss of assets or impairments of our manufacturing plants and fixed assets or write-downs of other operating assets and working capital.
> The conflict in the Middle East could also adversely impact our financial results and operations due to, for example, volatility in global energy markets, supply chain disruptions, inflationary pressures or trade restrictions.

**[0000080424-26-000103:1A:12]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Our ability to meet our customers' needs and achieve cost targets depends on our ability to maintain key manufacturing and supply arrangements, including execution of supply chain optimizations and certain sole supplier or sole manufacturing plant arrangements. The loss or disruption of such manufacturing and supply arrangements, including for issues such as labor disputes or controversies, loss or impairment of key manufacturing sites, discontinuity or disruptions in our internal information and data systems or those of our suppliers, cybersecurity incidents including but not limited to ransomware attacks, misuse of artificial intelligence (AI) and machine learning technologies, inability to procure sufficient raw or input materials (including water, recycled materials and materials that meet our labor standards), significant changes in trade policy, natural disasters, increasing severity or frequency of extreme weather events due to climate change or otherwise, acts of war or terrorism, disease outbreaks (including epidemics, pandemics or similar widespread public health concerns) or other external factors over which we have no control, have at times interrupted and could interrupt product supply and, if not effectively managed and remedied, have an adverse impact on our business, financial condition, results of operations or cash flows.

**[0000080424-26-000103:1A:28]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> We must successfully manage ongoing acquisition, joint venture and divestiture activities.
> As a company that manages a portfolio of consumer brands, our ongoing business model includes a certain level of acquisition, joint venture and divestiture activities. We must be able to successfully manage the impacts of these activities, while at the same time delivering against our business objectives. Specifically, our financial results have been and could be adversely impacted by the dilutive impacts from the loss of earnings associated with divested brands or dissolution of joint ventures. Our results of operations and cash flows have been and could be impacted by acquisitions or joint venture activities, if: 1) changes in the cash flows or other market-based assumptions cause the value of acquired assets to fall below book value, or 2) we are not able to deliver the expected cost and growth synergies associated with such acquisitions and joint ventures, including as a result of integration and collaboration challenges, which could also result in an impairment of goodwill and intangible assets.
> 8 The Procter & Gamble Company

**[0000080424-26-000103:1A:36]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> In December 2021, the Organisation for Economic Co-operation and Development (OECD) issued "Pillar Two" model rules which established a global minimum corporate tax rate of 15% for large multinational corporations. Many countries have implemented or are in the process of implementing Pillar Two legislation into their respective domestic laws. The implementation of the Pillar Two global minimum top-up tax did not have a material impact to our financial condition, results of operations, cash flows or effective tax rate for the fiscal year ended 2026. Based on current legislation and available guidance, including the January 5, 2026 Pillar Two "Side-by-Side Package", we do not anticipate the Pillar Two global minimum top-up tax to have a material impact to our financial condition, results of operations, cash flows or effective tax rate in future years. The Company continues to assess the overall impact of potential changes as developments occur, consistent
> The Procter & Gamble Company 9
> with our practice to monitor all changes in tax laws. As the Pillar Two global minimum tax and other tax laws and related regulations are revised, enacted and implemented, a material impact to our financial condition, results of operations, cash flows or effective tax rate may occur.

**[0000080424-26-000103:7:9]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Management also uses certain market share and market consumption estimates to evaluate performance relative to competition despite some limitations on the availability and comparability of share and consumption information. References to market share and consumption in the MD&A are based on a combination of vendor-purchased traditional brick-and-mortar and online data in key markets as well as internal estimates. All market share references represent the percentage of sales of our products in dollar terms on a constant currency basis relative to all product sales in the category. The Company measures market shares through the most recent period for which market share data is available, which typically reflects a lag time of one or two months as compared to the end of the reporting period. Management also uses unit volume growth to evaluate drivers of changes in net sales. Organic volume growth reflects year-over-year changes in unit volume excluding the impacts of acquisitions and divestitures and certain one-time items, if applicable, and is used to explain changes in organic sales. In our presentation of data in tables or other charts, certain columns and rows may not add due to rounding.
> OVERVIEW

**[0000080424-26-000103:7:56]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Net financing activities used $14.5 billion of cash in 2026, mainly due to dividends to shareholders and treasury stock purchases, partially offset by the impact of stock options and other.
> The Procter & Gamble Company 27
> Liquidity
> At June 30, 2026, our current liabilities exceeded current assets by $12.5 billion, largely due to accounts payable, short-term borrowings and debt due within one year. We anticipate being able to support our short-term liquidity and operating needs largely through cash generated from operations. The Company regularly assesses its cash needs and the available sources to fund these needs. As of June 30, 2026, the Company had $8.9 billion of cash and cash equivalents related to foreign subsidiaries, primarily in various European and Asian countries. We did not have material cash and cash equivalents related to any country subject to exchange controls that significantly restrict our ability to access or repatriate the funds. Under current law, we do not expect restrictions or taxes on repatriation of cash held outside of the U.S. to have a material effect on our overall liquidity, financial condition or the results of operations for the foreseeable future.

**[0000080424-26-000103:7:78]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Currency Rate Exposure. Because we manufacture and sell products and finance operations in a number of countries throughout the world, we are exposed to movements in currency exchange rates. We leverage the Company's diversified portfolio of exposures as a natural hedge. Corporate policy prescribes the range of allowable hedging activity. To manage the exchange rate risk associated with the financing of our operations, we primarily use forward contracts and currency swaps with maturities of less than 18 months.
> Based on our currency rate exposure on derivative and other instruments as of and during the fiscal year ended June 30, 2026, we believe, at a 95% confidence level based on historical currency rate movements, the impact on such instruments of a near-term change in currency rates would not materially affect our financial statements.
> Commodity Price Exposure. We use raw materials that are subject to price volatility caused by weather, supply conditions, political and economic variables and other unpredictable factors. We may use futures, options and swap contracts to manage the volatility related to the above exposures. During the fiscal years ended June 30, 2026 and 2025, we did not have any financial commodity hedging activity.
> The Procter & Gamble Company 31

**[0000080424-26-000103:7:79]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Measures Not Defined By U.S. GAAP
> In accordance with the SEC's Regulation S-K Item 10(e), the following provides definitions of non-GAAP measures and a reconciliation to the most closely related GAAP measure. We believe that these measures provide useful perspective on underlying business trends (i.e., trends excluding non-recurring or unusual items) and results and provide a supplemental measure of year-on-year results. The non-GAAP measures described below are used by management in making operating decisions, allocating financial resources and for business strategy purposes. These measures may be useful to investors, as they provide supplemental information about business performance and provide investors with a view of our business results through the eyes of management. These measures are also used to evaluate senior management and are a factor in determining their at-risk compensation. These non-GAAP measures are not intended to be considered by the user in place of the related GAAP measures but rather as supplemental information to our business results. These non-GAAP measures may not be the same as similar measures used by other companies due to possible differences in method and in the items or events being adjusted.

**Verdict:**  weak 

**Note:** 

### PG · rational_capital_allocation

**Rational capital allocation.** Does the filing show what management does with the cash the business generates (reinvestment, acquisitions, buybacks, dividends, debt repayment) and explain it? You judge whether it is documented concretely, not whether prices paid were good.

- **found** ("evidence found"): The filing quantifies at least one past action in the fiscal year (share repurchases, dividends, acquisitions, capital expenditure or debt repayment, with an amount) AND states a policy, priority or rationale for how cash is used. Not every action needs an amount.
- **weak** ("evidence weak"): Forward-looking plans only; or actions with no amount at all; or amounts with no stated policy, priority or rationale.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what was done with cash, or MD&A is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.

Passages (Item 7), in filing order:

**[0000080424-26-000103:7:9]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Management also uses certain market share and market consumption estimates to evaluate performance relative to competition despite some limitations on the availability and comparability of share and consumption information. References to market share and consumption in the MD&A are based on a combination of vendor-purchased traditional brick-and-mortar and online data in key markets as well as internal estimates. All market share references represent the percentage of sales of our products in dollar terms on a constant currency basis relative to all product sales in the category. The Company measures market shares through the most recent period for which market share data is available, which typically reflects a lag time of one or two months as compared to the end of the reporting period. Management also uses unit volume growth to evaluate drivers of changes in net sales. Organic volume growth reflects year-over-year changes in unit volume excluding the impacts of acquisitions and divestitures and certain one-time items, if applicable, and is used to explain changes in organic sales. In our presentation of data in tables or other charts, certain columns and rows may not add due to rounding.
> OVERVIEW

**[0000080424-26-000103:7:25]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> •Operating income decreased $703 million, or 3%, to $19.7 billion as the net sales increase was more than offset by a decrease in operating margin.
> •Net earnings increased $79 million to $16.1 billion as the decrease in operating income was offset by higher non-operating restructuring charges in the prior year, primarily driven by the non-cash charge for accumulated foreign currency translation losses due to the substantial liquidation of operations in Argentina.
> •Net earnings attributable to Procter & Gamble increased $72 million to $16.0 billion.
> •Diluted EPS increased 2% to $6.62 due to an increase in net earnings and a reduction in shares outstanding. Core EPS, which excludes the gain from the dissolution of the Glad joint venture business and incremental restructuring charges, increased 1% to $6.89.
> •Cash flow from operating activities was $19.6 billion.
> ◦ Adjusted free cash flow, which is defined as operating cash flow less capital expenditures and excluding payments for the transitional tax resulting from the 2017 U.S. Tax Act, was $15.8 billion.
> ◦ Adjusted free cash flow productivity, which is defined as adjusted free cash flow as a percentage of net earnings excluding the gain from the dissolution of the Glad joint venture business, was 100%.

**[0000080424-26-000103:7:35]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> •Other non-operating income/(expense), net increased $922 million to $1.1 billion primarily driven by the non-cash charge for accumulated foreign currency translation losses due to the substantial liquidation of operations in Argentina in the prior year and the gain from the dissolution of the Glad joint venture business in the current year period.
> Income Taxes
> The effective income tax rate for fiscal year ended June 30, 2026, was 20.8%, compared to 20.3% for the fiscal year ended June 30, 2025. The increase in the effective tax rate was primarily driven by lower excess tax benefits of share-based compensation in the current year and unfavorable geographic mix impacts, partially offset by a decrease from discrete impacts related to uncertain tax positions and the prior year charge for accumulated foreign currency translation losses due to the substantial liquidation of operations in Argentina.
> Net Earnings

**[0000080424-26-000103:7:52]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Savings generated from the Company's restructuring program are difficult to estimate, given the nature of the activities, the timing of the execution and the degree of reinvestment. In addition to our restructuring programs, we have additional ongoing savings efforts in our supply chain, marketing and overhead areas that yield additional benefits to our operating margins. Refer to Note 3 to the Consolidated Financial Statements for more details on the restructuring program.
> CASH FLOW, FINANCIAL CONDITION AND LIQUIDITY
> We believe our financial condition continues to be of high quality, as evidenced by our ability to generate substantial cash from operations and to readily access capital markets at competitive rates.
> Operating cash flow provides the primary source of cash to fund operating needs and capital expenditures. Excess operating cash is used first to fund shareholder dividends. Other discretionary uses include share repurchases and acquisitions to complement our portfolio of businesses, brands and geographies. As necessary, we may supplement operating cash flow with debt to fund these activities. The overall cash position of the Company reflects our strong business results and a global cash management strategy that takes into account liquidity management, economic factors and tax considerations.
> Cash Flow Analysis

**[0000080424-26-000103:7:54]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Operating cash flow was $19.6 billion in 2026, a 10% increase versus the prior year. Net earnings, adjusted for certain non-cash items (depreciation and amortization, share-based compensation expense, deferred income taxes and (gain)/loss on sale of assets) generated approximately $19.5 billion of operating cash flow. Working capital and other impacts generated $29 million of cash in the period. Accounts receivable decreased, resulting in $84 million of cash flow help. Days sales outstanding decreased by one day. Total inventories increased, consuming $641 million of cash, driven primarily by increased safety stock levels and new product initiatives. Days inventory on hand increased by two days. Accounts payable increased, generating $919 million of cash, driven primarily by increased supply chain activity in line with the increase in inventory and increased marketing support activity. Other impacts reduced cash by $333 million primarily driven by the final payment of the transitional tax related to the 2017 U.S. Tax Act and a reduction in postretirement benefit accruals, partially offset by tax accruals in excess of estimated payments and accrued marketing expense.

**[0000080424-26-000103:7:55]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> Adjusted Free Cash Flow. We view adjusted free cash flow as an important non-GAAP measure because it is a factor impacting the amount of cash available for dividends, share repurchases, acquisitions and other discretionary investments. It is defined as operating cash flow less capital expenditures and excluding payments for the transitional tax resulting from the 2017 U.S. Tax Act. Adjusted free cash flow is one of the measures used to evaluate senior management and determine their at-risk compensation.
> Adjusted free cash flow was $15.8 billion in 2026, an increase of 8% versus the prior year. The increase was primarily driven by the increase in operating cash flows as discussed above. Adjusted free cash flow productivity, defined as the ratio of adjusted free cash flow to net earnings excluding the gain from the dissolution of the Glad joint venture business, was 100% in 2026.
> Investing Cash Flow
> Net investing activities used $4.6 billion of cash in 2026, primarily due to capital expenditures and the settlement of net investment hedges, partially offset by proceeds from the dissolution of the Glad joint venture business.
> Financing Cash Flow

**[0000080424-26-000103:7:73]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> The discount rate is based on a weighted average cost of capital that is likely to be expected by a market participant, including consideration of both debt and equity components of the capital structure. Our discount rate may be impacted by adverse changes in the macroeconomic environment, volatility in the equity and debt markets or other country specific factors, such as further devaluation of currencies against the U.S. dollar. Spot rates as of the fair value measurement date are utilized in our fair value estimates for cash flows outside the U.S.
> 30 The Procter & Gamble Company
> The royalty rate used to determine the estimated fair value for the Gillette indefinite-lived intangible asset is driven by historical and estimated future profitability of the underlying Gillette business. The royalty rate may be impacted by significant adverse changes in long-term operating margins.

**[0000080424-26-000103:7:81]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/80424/000008042426000103/pg-20260630.htm)

> TOTAL COMPANY | 3 | % | (2) | % | — | % | 1 | %
> (1)Acquisition & Divestiture Impact/Other includes the volume and mix impact of acquisitions and divestitures and rounding impacts necessary to reconcile net sales to organic sales.
> Adjusted Free Cash Flow. Adjusted free cash flow is defined as operating cash flow less capital spending and excluding payments for the transitional tax resulting from the 2017 U.S. Tax Act. Adjusted free cash flow represents the cash that the Company is able to generate after taking into account planned maintenance and asset expansion. We view adjusted free cash flow as an important measure because it is one factor used in determining the amount of cash available for dividends, share repurchases, acquisitions and other discretionary investments.
> The following table provides a numerical reconciliation of adjusted free cash flow ($ millions):
> Operating Cash Flow | Capital Spending | 2017 U.S. Tax Act Payments | Adjusted Free Cash Flow
> 2026 | $ | 19,556 | $ | (4,409) | $ | 688 | $ | 15,835
> 2025 | $ | 17,817 | $ | (3,773) | $ | 562 | $ | 14,606

**Verdict:** Found 

**Note:** 

---

## NEE

Form 10-K, accession 0000753308-26-000015, filed 2026-02-13, period 2025-12-31. [Open the filing on sec.gov](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

### NEE · understandable_business

**Understandable business.** Can the business be explained simply: what the company sells, to whom, and how it makes money?

- **found** ("evidence found"): The filing names specific products or services, the customers or markets they are sold to, and how revenue is earned (for example segments with figures, a pricing or sales model), in plain terms.
- **weak** ("evidence weak"): The business is described only in general or promotional terms (a 'leading provider of solutions'), or the filing says what is sold but not who buys it or how it earns money.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what the company sells or how it earns money, or the Business section is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1), in filing order:

**[0000753308-26-000015:1:1]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Item 1. Business
> OVERVIEW
> NEE is one of the largest electric power and energy infrastructure companies in North America. As of December 31, 2025, NEE had approximately 80 gigawatts of net generation and storage capacity from a diverse portfolio of assets, primarily including natural gas, wind, solar and nuclear generation facilities and battery storage facilities. NEE has two principal businesses, FPL and NEER. FPL is the largest electric utility in Florida and the U.S. FPL's strategic focus is centered on investing in generation, storage, transmission and distribution facilities to deliver on its value proposition of keeping customer bills low and delivering high reliability, outstanding customer service and energy from diverse generation sources for the benefit of its more than six million customer accounts. NEER is one of the largest energy infrastructure developers in the U.S. NEER's strategic focus is centered on the development, construction and operation of long-term contracted generation facilities, including renewables, nuclear and natural gas, as well as battery storage facilities. NEER also builds and owns regulated electric and gas transmission assets, is a leading gas and power supplier, and delivers integrated energy and technology solutions to utilities and businesses across the U.S.

**[0000753308-26-000015:1:2]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE seeks to create value in its two principal businesses by meeting customer needs more economically and reliably than its competitors. NEE's strategy has resulted in profitable growth over sustained periods at both FPL and NEER. Management seeks to grow each business (see Note 15 – Commitments) in a manner consistent with the varying opportunities available to it; however, management believes that the diversification and balance represented by FPL and NEER is a valuable characteristic of the enterprise and recognizes that each business contributes to NEE's financial strength in different ways. FPL and NEER share a common platform with the objective of lowering costs, creating efficiencies and encouraging innovative ideas for their businesses. NEE and its subsidiaries, with employees totaling approximately 17,400 as of December 31, 2025, continue to develop and implement enterprise-wide initiatives, including deploying advanced technologies such as artificial intelligence and proprietary tools, focused on improving processes, lowering costs and driving growth.
> NEE's reportable segments for financial reporting purposes are FPL and NEER (see Note 16). NEECH, a wholly owned subsidiary of NEE, owns and provides funding for NEE's operating subsidiaries, other than FPL and its subsidiaries. The following diagram depicts NEE's simplified ownership structure:
> 4

**[0000753308-26-000015:1:7]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Because any customer may elect to provide its own electric services, FPL effectively must compete for an individual customer's business. As a practical matter, few customers provide their own service at the present time since FPL's cost of service is lower than the cost of self-generation for a significant majority of customers. Changing technology (particularly the increasing efficiency of solar power generation), tax incentives, economic conditions, regulatory changes and other factors could alter the favorable relative cost position that FPL currently enjoys; however, FPL seeks as a matter of strategy to ensure that it delivers superior value in the form of low customer bills, high reliability, outstanding customer service and energy from diverse generation sources.
> In addition to self-generation by residential, commercial and industrial customers, FPL also faces competition from other suppliers of electrical energy to wholesale and industrial customers and from alternative energy sources. In 2025, 2024 and 2023, annual operating revenues from wholesale and industrial electric customers combined represented approximately 5% of FPL's total operating revenues.
> 6
> Table of Contents

**[0000753308-26-000015:1:27]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEER, one of the largest energy infrastructure developers in the U.S., is comprised of NEE's competitive energy and regulated transmission businesses. NEER is a diversified energy business with a strategy that emphasizes the development, construction and operation of long-term contracted generation facilities and builds and owns regulated electric and gas transmission assets. NEER also provides gas and power solutions through its customer supply business. NEER's strategy focuses on providing cost-effective differentiated solutions to its customers, including emerging large-load opportunities, and on lowering costs and driving growth, including through the use of advanced technologies, such as artificial intelligence and proprietary tools. NEE reports NextEra Energy Resources and NEET, a rate-regulated electric transmission business, on a combined basis for segment reporting purposes, and the combined segment is referred to as NEER.

**[0000753308-26-000015:1:30]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Through its customer supply business, NEER engages in energy-related commodity marketing and trading activities, including entering into financial and physical contracts. These contracts primarily involve power and fuel commodities and their related products for the purpose of providing full energy and capacity requirements services, primarily to distribution utilities in certain markets. They are also used to offer customized power and fuel and related risk management services to wholesale customers, including services provided under natural gas asset management agreements, as well as to hedge the production from NEER's generation assets that is not sold under long-term power supply agreements. In addition, NEER participates in natural gas, natural gas liquids and oil production through operating and non-operating ownership interests. NEER hedges the expected output from its natural gas and oil production assets to protect against price movements.
> 11
> Table of Contents
> OPERATIONS
> NEER sells products associated with its generation and battery storage facilities (energy, capacity, RECs and ancillary services) in competitive markets in regions where those facilities are located. Customer transactions may be supplied from NEER generation and battery storage facilities or from purchases in the wholesale markets, or from a combination thereof. See Markets and Competition below.

**[0000753308-26-000015:1:45]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> (b) In January 2026, NextEra Energy Resources increased its ownership interest to 36.02%.
> 17
> Table of Contents
> Other Operations
> Customer Supply – NEER provides commodities-related products to customers, including municipal utilities and cooperatives, engages in energy-related commodity marketing and trading activities and includes the operations of a retail electricity provider and ownership interests in natural gas and oil shale formations located primarily in the South region of the U.S. Through NextEra Energy Resources' subsidiary, NextEra Energy Marketing, LLC, NEER:
> •manages risk associated with fluctuating commodity prices and optimizes the value of NEER's power generation and natural gas and oil production assets through the use of swaps, options, futures and forwards;
> •sells output from NEER's plants that is not sold under long-term contracts and procures fuel for use by NEER's generation fleet;
> •provides full energy and capacity requirements to customers; and
> •markets and trades energy-related commodity products, including power and fuel, as well as marketing and trading services to customers.
> In January 2026, a wholly owned subsidiary of NextEra Energy Resources acquired Symmetry Energy Solutions, a commercial and industrial natural gas business. See Note 6 – Symmetry Acquisition.
> MARKETS AND COMPETITION

**[0000753308-26-000015:1:47]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> The degree and nature of competition is different in wholesale markets than in retail markets. A majority of NEER's revenues are derived from sales of energy, capacity, credits and ancillary products under long-term PPAs to customers located in wholesale electricity markets. Wholesale power generation is a capital-intensive, commodity-driven business with numerous industry participants. NEER primarily competes on the basis of price, but believes that its track record of completing projects on schedule, creditworthiness, operating scale and ability to offer and manage reliable customized risk solutions to wholesale customers are competitive advantages. Wholesale power generation is a regional business that is highly fragmented relative to many other commodity industries and diverse in terms of industry structure. As such, there is a wide variation in terms of the capabilities, resources, nature and identity of the companies NEER competes with depending on the market. In wholesale markets, customers' needs are met through a variety of means, including long-term bilateral contracts, standardized bilateral products such as full requirements service and customized supply and risk management services.

**[0000753308-26-000015:1:52]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Certain facilities within the NEER wind and solar generation portfolio produce RECs and other environmental attributes which are typically sold along with the energy from the plants under long-term contracts, or may be sold separately from wind and solar generation not sold under long-term contracts. The purchasing party is solely entitled to the reporting rights and ownership of the environmental attributes.
> While the majority of NEER's revenue is derived from the output of its generation facilities, NEER is also an active competitor in several regions in the wholesale full requirements business and in providing structured and customized power and fuel products and services to a variety of customers. In the full requirements service, typically, the supplier agrees to meet the customer's needs for a full range of products for every hour of the day, at a fixed price, for a predetermined period of time, thereby assuming the risk of fluctuations in the customer's volume requirements.
> 19
> Table of Contents

**Verdict:** found 

**Note:** 

### NEE · durable_competitive_advantage

**Durable competitive advantage.** Does the filing give concrete evidence of an advantage that protects the company's profits from competitors over many years (for example a brand, scale or cost position, switching costs, a network, patents, or a regulated franchise)?

- **found** ("evidence found"): The filing states a source of advantage AND a checkable specific for it: a market share or rank figure; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated network size. A statement that an asset exists or matters (brand, trade secrets, patents, 'strong' distribution) without a measure is not enough.
- **weak** ("evidence weak"): The advantage is only asserted, or an asset is named as important (brand, trade secrets, patents, scale) without any measure; or the specifics are offset by the filing's own statements that competitors or customers can readily erode the position.
- **insufficient** ("insufficient evidence"): The retrieved text says nothing about the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1, Item 1A), in filing order:

**[0000753308-26-000015:1:27]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEER, one of the largest energy infrastructure developers in the U.S., is comprised of NEE's competitive energy and regulated transmission businesses. NEER is a diversified energy business with a strategy that emphasizes the development, construction and operation of long-term contracted generation facilities and builds and owns regulated electric and gas transmission assets. NEER also provides gas and power solutions through its customer supply business. NEER's strategy focuses on providing cost-effective differentiated solutions to its customers, including emerging large-load opportunities, and on lowering costs and driving growth, including through the use of advanced technologies, such as artificial intelligence and proprietary tools. NEE reports NextEra Energy Resources and NEET, a rate-regulated electric transmission business, on a combined basis for segment reporting purposes, and the combined segment is referred to as NEER.

**[0000753308-26-000015:1:47]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> The degree and nature of competition is different in wholesale markets than in retail markets. A majority of NEER's revenues are derived from sales of energy, capacity, credits and ancillary products under long-term PPAs to customers located in wholesale electricity markets. Wholesale power generation is a capital-intensive, commodity-driven business with numerous industry participants. NEER primarily competes on the basis of price, but believes that its track record of completing projects on schedule, creditworthiness, operating scale and ability to offer and manage reliable customized risk solutions to wholesale customers are competitive advantages. Wholesale power generation is a regional business that is highly fragmented relative to many other commodity industries and diverse in terms of industry structure. As such, there is a wide variation in terms of the capabilities, resources, nature and identity of the companies NEER competes with depending on the market. In wholesale markets, customers' needs are met through a variety of means, including long-term bilateral contracts, standardized bilateral products such as full requirements service and customized supply and risk management services.

**[0000753308-26-000015:1A:31]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> The productivity increases and competitive advantages NEE and FPL plan to achieve through the use of artificial intelligence (AI) technologies may not be realized and the use of and reliance on AI may present certain risks, both of which could materially adversely affect their business, financial condition, results of operations and prospects.

**[0000753308-26-000015:1A:39]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE and FPL generally are not fully insured against all significant losses. For example, NEE, including FPL, does not have property insurance coverage for a substantial portion of its transmission and distribution property and natural gas pipeline assets. A loss for which NEE or FPL is not fully insured could have a material adverse effect on NEE's and FPL's business, financial condition, results of operations and prospects.
> NEE invests in natural gas and oil production assets which are exposed to fluctuating market prices of natural gas, natural gas liquids, oil and other energy commodities. A prolonged period of low natural gas and oil prices, disrupted production or unsuccessful drilling efforts could impact NEER's natural gas and oil production operations and cause NEER to delay or cancel certain natural gas and oil production projects and could result in certain assets becoming impaired, which could materially adversely affect NEE's business, financial condition, results of operations and prospects.

**[0000753308-26-000015:1A:41]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> If supply costs necessary to provide NEER's full energy and capacity requirements services are not favorable, operating costs could increase and materially adversely affect NEE's business, financial condition, results of operations and prospects.
> NEER provides full energy and capacity requirements services primarily to distribution utilities, which include load-following services and various ancillary services, to satisfy all or a portion of such utilities' power supply obligations to their customers. The supply costs for these transactions may be affected by a number of factors, including, but not limited to, weather conditions, transmission constraints, fluctuating prices for, and locational disconnects in, energy and ancillary services, and the ability of the distribution utilities' customers to elect to receive service from competing suppliers. If any of these factors materialize, costs to supply services may exceed revenues generated or be below expected return levels, which could have a material adverse effect on NEE's business, financial condition, results of operations and prospects.

**[0000753308-26-000015:1A:43]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE is an active participant in energy markets. Liquidity in energy markets can be described as the degree to which a product, such as electricity, gas or transmission rights, can be quickly bought or sold without significantly affecting its price and without incurring significant transaction costs. It can be driven in part by the number of active market participants and is an important factor in NEE's ability to manage risks in its participation in these markets. Liquidity in the energy markets can be adversely affected by price volatility, restrictions on the availability of credit, inflation, rising interest rates and other factors, and any reduction in the liquidity of energy markets could have a material adverse effect on NEE's business, financial condition, results of operations and prospects.
> NEE's and FPL's hedging and trading procedures and associated risk management tools may not protect against significant losses.

**[0000753308-26-000015:1A:53]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE and FPL execute transactions in derivative instruments on either recognized exchanges or through the OTC markets, depending on management's assessment of the most favorable credit and market execution factors. Transactions executed on OTC markets have the potential for greater volatility and less liquidity than transactions on recognized exchanges. As a result, NEE and FPL may not be able to execute desired OTC transactions due to such heightened volatility and limited liquidity.
> In the absence of actively quoted market prices and pricing information from external sources, the valuation of derivative instruments involves management's judgment and use of estimates. As a result, changes in the underlying assumptions or use of alternative valuation methods could affect the reported fair value of these derivative instruments and have a material adverse effect on NEE's and FPL's business, financial condition, results of operations and prospects.
> NEE and FPL may be materially adversely affected by negative publicity.

**[0000753308-26-000015:1A:71]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE has invested in various joint ventures and equity method investments where it does not have full control over operations, management or decision-making. In many cases, NEE shares control rights with its partners, but may lack influence or be dependent on their business priorities. This situation can lead to decisions that differ from NEE's preferences, potentially impacting the profitability and value of these investments. Furthermore, if a joint venture partner becomes insolvent or bankrupt or is otherwise unable to meet its obligations, NEE may be responsible for meeting certain obligations of the joint ventures as stipulated in its governing documents or applicable law. NEE's joint venture partners may not always share NEE's business priorities which may have a material adverse effect on NEE's liquidity, financial condition and results of operations.
> NEE may be unable to meet its ongoing and future financial obligations and to pay dividends on its common stock if its subsidiaries are unable to pay upstream dividends, make distributions or repay funds to NEE.

**Verdict:** insufficient

**Note:** 

### NEE · candid_management

**Candid management.** Does management openly discuss setbacks, mistakes, declines and uncertainty in its own words, rather than only successes?

- **found** ("evidence found"): Management's own account of a setback that it attributes at least partly to the company's own decisions or execution; or a target or guidance of its own that was missed; or an acknowledged material weakness, restatement or write-down of something management chose (an acquisition, investment or project), stated plainly.
- **weak** ("evidence weak"): Declines or charges explained only by external factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even when quantified; or generic caution ('results may fluctuate', 'we face risks'); or a setback mentioned without explanation.
- **insufficient** ("insufficient evidence"): The retrieved text is promotional or boilerplate and gives nothing to judge candour either way, or MD&A and Risk Factors are missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.
- **Limitation:** Limitation: 10-K text is reviewed by lawyers, and candour is better judged from shareholder letters (outside this tool's scope). Do not read polished or detailed prose as candour;

Passages (Item 7, Item 1A), in filing order:

**[0000753308-26-000015:1A:1]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Item 1A. Risk Factors
> Risks Relating to NEE's and FPL's Business
> The business, financial condition, results of operations and prospects of NEE and FPL are subject to a variety of risks, many of which are beyond the control of NEE and FPL. These risks, whether or not expressly stated with respect to any particular risk factor, as well as additional risks and uncertainties either not presently known or that are currently believed to not be material to the business, may materially adversely affect the business, financial condition, results of operations and prospects of NEE and FPL and may cause actual results of NEE and FPL to differ substantially from those that NEE or FPL currently expects or seeks. In that event, the market price for the securities of NEE or FPL could decline. Accordingly, the risks described below should be carefully considered together with the other information set forth in this report and in future reports that NEE and FPL file with the SEC.
> Regulatory, Legislative and Legal Risks
> NEE's and FPL's business, financial condition, results of operations and prospects may be materially adversely affected by the extensive regulation of their business.

**[0000753308-26-000015:1A:30]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Growth in customer accounts and growth of customer usage each directly influence the demand for electricity and the need for additional power generation and power delivery facilities, as well as the need for energy-related commodities, such as natural gas. Customer growth and customer usage are affected by a number of factors outside the control of NEE and FPL, such as mandated energy efficiency measures, demand side management requirements, installation of distributed generation technologies and economic and demographic conditions, such as population changes, job and income growth, housing starts, new business formation, expanded use of data centers, inflation and the overall level of economic activity. A lack of growth, or a decline, in the number of customers or in customer demand for electricity or natural gas and other fuels may cause NEE and FPL to fail to fully realize benefits from pending and planned future investments and expenditures and could have a material adverse effect on NEE's and FPL's growth, business, financial condition, results of operations and prospects.

**[0000753308-26-000015:1A:53]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE and FPL execute transactions in derivative instruments on either recognized exchanges or through the OTC markets, depending on management's assessment of the most favorable credit and market execution factors. Transactions executed on OTC markets have the potential for greater volatility and less liquidity than transactions on recognized exchanges. As a result, NEE and FPL may not be able to execute desired OTC transactions due to such heightened volatility and limited liquidity.
> In the absence of actively quoted market prices and pricing information from external sources, the valuation of derivative instruments involves management's judgment and use of estimates. As a result, changes in the underlying assumptions or use of alternative valuation methods could affect the reported fair value of these derivative instruments and have a material adverse effect on NEE's and FPL's business, financial condition, results of operations and prospects.
> NEE and FPL may be materially adversely affected by negative publicity.

**[0000753308-26-000015:1A:70]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE holds certain assets and investments where changes in the fair value affect NEE's financial results. In some cases there may be no observable market values for these assets and investments, requiring fair value estimates to be based on other valuation techniques. This type of analysis requires significant judgment and the actual values realized in a sale of these assets and investments could differ materially from those estimated. A sale of an asset or investment below previously estimated value, or other decline in the fair value of an asset or investment, could result in losses or the write-off of such asset or investment, and may have a material adverse effect on NEE's liquidity, financial condition and results of operations.

**[0000753308-26-000015:1A:71]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE has invested in various joint ventures and equity method investments where it does not have full control over operations, management or decision-making. In many cases, NEE shares control rights with its partners, but may lack influence or be dependent on their business priorities. This situation can lead to decisions that differ from NEE's preferences, potentially impacting the profitability and value of these investments. Furthermore, if a joint venture partner becomes insolvent or bankrupt or is otherwise unable to meet its obligations, NEE may be responsible for meeting certain obligations of the joint ventures as stipulated in its governing documents or applicable law. NEE's joint venture partners may not always share NEE's business priorities which may have a material adverse effect on NEE's liquidity, financial condition and results of operations.
> NEE may be unable to meet its ongoing and future financial obligations and to pay dividends on its common stock if its subsidiaries are unable to pay upstream dividends, make distributions or repay funds to NEE.

**[0000753308-26-000015:7:20]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> In 2025, the change in gains on disposal of businesses/assets – net is the result of lower disposal gains in the current year as compared to the prior year. See Note 1 – Disposal of Businesses for a discussion of gains related to the September 2024 sales of ownership interests in connection with the pipeline joint venture and the renewable assets joint venture.
> Interest Expense
> NEER's interest expense for 2025 increased $569 million primarily reflecting approximately $351 million of unfavorable impacts related to changes in the fair value of interest rate derivative instruments as well as higher average debt balances driven by growth in the business.
> 43
> Table of Contents
> Equity in Losses of Equity Method Investees
> NEER recognized $193 million and $267 million of equity in losses of equity method investees in 2025 and 2024, respectively. The change in 2025 primarily reflects the impact of an impairment charge of approximately $0.7 billion ($0.5 billion after tax) compared to a 2024 impairment charge of $0.8 billion ($0.6 billion after tax) related to the investment in XPLR (see Note 4 – Nonrecurring Fair Value Measurements).
> Income Taxes

**[0000753308-26-000015:7:58]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Expected long-term rate of return | 0.5% | $ | 26 | $ | 15
> Discount rate | (0.5)% | $ | 1 | $ | 1
> Salary increase | 0.5% | $ | (2) | $ | (1)
> NEE also utilizes actuarial assumptions about mortality to help estimate obligations of the pension plan. NEE has adopted the latest mortality tables released by the Society of Actuaries and an actuarially adjusted mortality improvement scale that incorporates recent experience. The annual update to the mortality assumptions did not have a material impact on the pension plan's obligation.
> See Note 12.
> 52
> Table of Contents
> Carrying Value of Long-Lived Assets
> NEE evaluates long-lived assets for impairment when events or changes in circumstances indicate that the carrying amount may not be recoverable.
> Nature of Accounting Estimates

**[0000753308-26-000015:7:61]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> An impairment loss is required to be recognized if the impairment is deemed to be other than temporary. Assessment of whether an investment is other than temporarily impaired involves, among other factors, consideration of the length of time that the fair value is below the carrying value, current expected performance relative to the expected performance when the investment was initially made, performance relative to peers, industry performance relative to the economy, credit rating, regulatory actions and legal and permitting challenges. If management is unable to reasonably assert that an impairment is temporary or believes that there will not be full recovery of the carrying value of its investment, then the impairment is considered to be other than temporary. Investments that are other than temporarily impaired are written down to their estimated fair value and cannot subsequently be written back up for increases in estimated fair value. Impairment losses are recorded in equity in losses of equity method investees in NEE's consolidated statements of income. See Note 4 – Nonrecurring Fair Value Measurements.
> Decommissioning and Dismantlement

**Verdict:** found 

**Note:** 

### NEE · rational_capital_allocation

**Rational capital allocation.** Does the filing show what management does with the cash the business generates (reinvestment, acquisitions, buybacks, dividends, debt repayment) and explain it? You judge whether it is documented concretely, not whether prices paid were good.

- **found** ("evidence found"): The filing quantifies at least one past action in the fiscal year (share repurchases, dividends, acquisitions, capital expenditure or debt repayment, with an amount) AND states a policy, priority or rationale for how cash is used. Not every action needs an amount.
- **weak** ("evidence weak"): Forward-looking plans only; or actions with no amount at all; or amounts with no stated policy, priority or rationale.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what was done with cash, or MD&A is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.

Passages (Item 7), in filing order:

**[0000753308-26-000015:7:1]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Item 7. Management's Discussion and Analysis of Financial Condition and Results of Operations
> OVERVIEW
> NEE's operating performance is driven primarily by the operations of its two principal businesses, FPL, which serves more than six million customer accounts in Florida and is the largest electric utility in the U.S., and NEER, which together with affiliated entities is one of the largest energy infrastructure developers in the U.S. The table below presents net income (loss) attributable to NEE and earnings (loss) per share attributable to NEE, assuming dilution, by reportable segment, FPL and NEER. Corporate and Other is primarily comprised of the operating results of other business activities, as well as other income and expense items, including interest expense, and eliminating entries, and may include the net effect of rounding. See Note 16 for additional segment information. The following discussion should be read in conjunction with the Notes to Consolidated Financial Statements contained herein and all comparisons are with the corresponding items in the prior year.
> Net Income (Loss) Attributable to NEE | Earnings (Loss) Per Share Attributable to NEE, Assuming Dilution
> Years Ended December 31, | Years Ended December 31,
> 2025 | 2024 | 2023 | 2025 | 2024 | 2023

**[0000753308-26-000015:7:2]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> (millions)
> FPL | $ | 5,012 | $ | 4,543 | $ | 4,552 | $ | 2.42 | $ | 2.21 | $ | 2.24
> NEER(a) | 2,975 | 2,299 | 3,558 | 1.44 | 1.12 | 1.75
> Corporate and Other | (1,152) | 104 | (800) | (0.56) | 0.04 | (0.39)
> NEE | $ | 6,835 | $ | 6,946 | $ | 7,310 | $ | 3.30 | $ | 3.37 | $ | 3.60
> ______________________
> (a) NEER's results reflect an allocation of interest expense from NEECH to NextEra Energy Resources based on a deemed capital structure of 70% debt and differential membership interests sold by NextEra Energy Resources' subsidiaries.
> For the five years ended December 31, 2025, NEE delivered a total shareholder return of approximately 18.2%, compared to the S&P 500's 96.2% return, the S&P 500 Utilities' 59.1% return and the Dow Jones U.S. Electricity's 64.8% return. The historical stock performance of NEE's common stock shown in the performance graph below is not necessarily indicative of future stock price performance.
> 39
> Table of Contents
> Adjusted Earnings

**[0000753308-26-000015:7:8]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE and its subsidiaries require funds to support and grow their businesses. These funds are primarily provided by cash flows from operations, borrowings or issuances of short- and long-term debt and, from time to time, issuances of equity securities, proceeds from differential membership investors, and sales of tax credits and ownership interests in assets/businesses. See Liquidity and Capital Resources.
> RESULTS OF OPERATIONS
> Net income attributable to NEE for 2025 was $6.84 billion compared to $6.95 billion in 2024. In 2025, net income attributable to NEE decreased primarily due to lower results at Corporate and Other, partly offset by higher results at FPL and NEER. The comparison of the results of operations for the years ended December 31, 2024 and 2023 are included in Management's Discussion in NEE's and FPL's Annual Report on Form 10-K for the year ended December 31, 2024.
> NEE's effective income tax rate for 2025 and 2024 was approximately (18)% and 6%, respectively. The rates for both years reflect the composition of pretax income in 2025 and 2024 as well as the impact of clean energy tax credits. See Note 5.

**[0000753308-26-000015:7:22]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Corporate and Other is primarily comprised of the operating results of other business activities, as well as corporate interest income and expenses. Corporate and Other allocates a portion of NEECH's corporate interest expense to NextEra Energy Resources. Interest expense is allocated based on a deemed capital structure of 70% debt and differential membership interests sold by NextEra Energy Resources' subsidiaries.
> Corporate and Other's results decreased $1,256 million during 2025 primarily due to unfavorable after-tax impacts of approximately $1,002 million, as compared to the prior year, related to non-qualifying hedge activity as a result of changes in the fair value of interest rate derivative instruments used to manage interest rate and foreign currency exchange rate risk associated primarily with outstanding and expected future debt issuances and borrowings (see Note 3) as well as higher average debt balances.
> LIQUIDITY AND CAPITAL RESOURCES

**[0000753308-26-000015:7:23]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE and its subsidiaries require funds to support and grow their businesses. These funds are used for, among other things, working capital, capital expenditures (see Note 15 – Commitments), investments in or acquisitions of assets and businesses (see Note 6), payment of maturing debt and related derivative obligations (see Note 13 and Note 3) and, from time to time, redemption or repurchase of outstanding debt or equity securities. It is anticipated that these requirements will be satisfied through a combination of cash flows from operations, short- and long-term borrowings, the issuance of short- and long-term debt (see Note 13) and, from time to time, equity securities, proceeds from differential membership investors, sales of clean energy tax credits (see Note 1 – Income Taxes) and sales of ownership interests in assets/businesses (see Note 1 – Disposal of Businesses), consistent with NEE's and FPL's objective of maintaining, on a long-term basis, a capital structure that will support a strong investment grade credit rating. NEE, FPL and NEECH rely on access to credit and capital markets as significant sources of liquidity for capital requirements and other operations that are not satisfied by operating cash flows. The inability of NEE, FPL and NEECH to maintain their current credit ratings could affect their ability to raise short- and long-term capital, their cost of capital and the execution of their respective financing strategies, and could require the posting of additional collateral under certain agreements.

**[0000753308-26-000015:7:25]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> 44
> Table of Contents
> Cash Flows
> NEE's sources and uses of cash for 2025, 2024 and 2023 were as follows:
> Years Ended December 31,
> 2025 | 2024 | 2023
> (millions)
> Sources of cash:
> Cash flows from operating activities | $ | 12,485 | $ | 13,260 | $ | 11,301
> Issuances of long-term debt, including premiums and discounts | 23,394 | 24,769 | 13,857
> Proceeds from differential membership investors | 3,276 | 2,257 | 2,745
> Proceeds from the sale of Florida City Gas business | — | — | 924
> Sale of independent power and other investments of NEER | 1,115 | 2,659 | 1,883
> Issuances of common stock/equity units | 2,038 | 48 | 4,514
> Net increase in commercial paper and other short-term debt | 676 | — | 2,308
> Cash swept from related parties – net | — | — | 1,213
> Other sources – net | 118 | — | —
> Total sources of cash | 43,102 | 42,993 | 38,745
> Uses of cash:
> Capital expenditures, independent power and other investments and nuclear fuel purchases | (24,606) | (24,729) | (25,113)
> Retirements of long-term debt | (10,347) | (10,113) | (7,978)

**[0000753308-26-000015:7:26]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> Net decrease in commercial paper and other short-term debt | — | (3,018) | —
> Payments to differential membership investors | (516) | (740) | (75)
> Repayments of cash swept to related parties – net | (131) | (1,371) | —
> Dividends on common stock | (4,680) | (4,235) | (3,782)
> Other uses – net | (1,223) | (791) | (1,814)
> Total uses of cash | (41,503) | (44,997) | (38,762)
> Effects of currency translation on cash, cash equivalents and restricted cash | 5 | (14) | (4)
> Net increase (decrease) in cash, cash equivalents and restricted cash | $ | 1,604 | $ | (2,018) | $ | (21)
> For significant financing activity that occurred subsequent to December 31, 2025, see Note 13.
> NEE's primary capital requirements are for expanding and enhancing FPL's electric system and generation facilities to continue to provide reliable service to meet customer electricity demands and for funding NEER's investments in independent power and other projects. See Note 15 – Commitments for estimated capital expenditures in 2026 through 2030.
> The following table provides a summary of capital investments for 2025, 2024 and 2023.
> Years Ended December 31,
> 2025 | 2024 | 2023
> (millions)
> FPL:
> Generation:

**[0000753308-26-000015:7:42]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/753308/000075330826000015/nee-20251231.htm)

> NEE's charter does not limit the dividends that may be paid on its common stock. As a practical matter, the ability of NEE to pay dividends on its common stock is dependent upon, among other things, dividends paid to it by its subsidiaries. For example, FPL pays dividends to NEE in a manner consistent with FPL's long-term targeted capital structure. However, the mortgage securing FPL's first mortgage bonds contains provisions which, under certain conditions, restrict the payment of dividends to NEE and the issuance of additional first mortgage bonds. Additionally, in some circumstances, the mortgage restricts the amount of retained earnings that FPL can use to pay cash dividends on its common stock. The restricted amount may change based on factors set out in the mortgage. Other than this restriction on the payment of common stock dividends, the mortgage does not restrict FPL's use of retained earnings. As of December 31, 2025, no retained earnings were restricted by these provisions of the mortgage and, in light of FPL's current financial condition and level of earnings, management does not expect that planned financing activities or dividends would be affected by these limitations.

**Verdict:** found 

**Note:** 

---

## CAT

Form 10-K, accession 0000018230-26-000008, filed 2026-02-13, period 2025-12-31. [Open the filing on sec.gov](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

### CAT · understandable_business

**Understandable business.** Can the business be explained simply: what the company sells, to whom, and how it makes money?

- **found** ("evidence found"): The filing names specific products or services, the customers or markets they are sold to, and how revenue is earned (for example segments with figures, a pricing or sales model), in plain terms.
- **weak** ("evidence weak"): The business is described only in general or promotional terms (a 'leading provider of solutions'), or the filing says what is sold but not who buys it or how it earns money.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what the company sells or how it earns money, or the Business section is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1), in filing order:

**[0000018230-26-000008:1:1]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Item 1.Business.
> General
> Originally organized as Caterpillar Tractor Co. in 1925 in the State of California, our company was reorganized as Caterpillar Inc. in 1986 in the State of Delaware. As used herein, the term "Caterpillar," "we," "us," "our" or "the company" refers to Caterpillar Inc. and its subsidiaries unless designated or identified otherwise.
> Overview
> With 2025 sales and revenues of $67.589 billion, Caterpillar Inc. is shaping the future as the world's leading manufacturer of construction and mining equipment, off-highway diesel and natural gas engines, industrial gas turbines and diesel-electric locomotives. Backed by one of the largest independent global dealer networks and financing services through Cat Financial, the company's primary business segments: Power & Energy, Construction Industries and Resource Industries are solving customers' toughest challenges through commercial excellence and advanced technology, driven by a highly skilled, dedicated global team.
> Enterprise Strategy

**[0000018230-26-000008:1:2]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> In 2025, our company introduced a revised strategy anchored by a new mission statement: Solving our customers' toughest challenges. Coupled with our purpose, we build a better, more sustainable world, this strategy guides how we operate with our global team and engage with customers, dealers and suppliers. The refreshed strategy establishes three profitable growth pillars focused on addressing customers' needs; Commercial Excellence, Advanced Technology Leader, and Transform How We Work. These pillars are built upon our longstanding foundation of Operational Excellence and guided by the Operating & Execution model. We also re-enforced our commitment to our Values in Action - Safety, Integrity, Teamwork, Excellence and Commitment. Caterpillar continues to operate through five operating segments, four of which are reportable segments and are described below.
> Categories of Business Organization
> 1.Machinery, Power & Energy — Caterpillar Inc. and its subsidiaries, excluding Financial Products. Machinery, Power & Energy information relates to the design, manufacturing and marketing of our products.
> 2.Financial Products — Our finance and insurance subsidiaries, primarily Caterpillar Financial Services Corporation (Cat Financial) and Caterpillar Insurance Holdings Inc. (Insurance Services). Financial Products information relates to the financing to customers and dealers for the purchase and lease of Caterpillar and other equipment.

**[0000018230-26-000008:1:11]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> The business of our Financial Products Segment is primarily conducted by Cat Financial, Insurance Services and their respective subsidiaries and affiliates. Cat Financial is a wholly owned finance subsidiary of Caterpillar Inc., and it provides retail and wholesale financing alternatives to customers and dealers around the world for Caterpillar products and services, as well as financing for power generation facilities that incorporate Caterpillar products. The various financing plans offered by Cat Financial are designed to support sales of Caterpillar products and services and generate financing income for Cat Financial. In addition, Cat Financial purchases short-term wholesale trade receivables from Caterpillar. A significant portion of Cat Financial's activity is conducted in North America, and Cat Financial has additional offices and subsidiaries in Latin America, Asia/Pacific, Europe and Africa.
> For over 40 years, Cat Financial has been providing financing for Caterpillar products, contributing to our knowledge of asset values, industry trends, financing structures and customer needs.
> Cat Financial offers the following financing products to customers:
> •Loans – Cat Financial offers loans that allow customers to purchase equipment with structured payments over time. These loans are typically secured by the equipment purchased.

**[0000018230-26-000008:1:16]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Cat Financial has a match-funding policy that addresses interest rate risk by aligning the interest rate profile (fixed or floating rate and duration) of its debt portfolio with the interest rate profile of its receivables portfolio within predetermined ranges on an ongoing basis. In connection with that policy, Cat Financial uses interest rate derivative instruments to modify the debt structure to match assets within the receivables portfolio. This matched funding reduces the volatility of margins between interest-bearing assets and interest-bearing liabilities, regardless of which direction interest rates move. For more information regarding match funding, please see Note 4 — "Derivative financial instruments and risk management" of Part II, Item 8 "Financial Statements and Supplementary Data." See also the risk factors associated with our financial products business included in Item 1A. of this Form 10-K.
> 4
> Table of Contents

**[0000018230-26-000008:1:23]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> We source our raw materials and manufactured components from suppliers both domestically and internationally. These purchases include unformed materials and rough and finished parts. Unformed materials include a variety of steel products, which are then cut or formed to shape and machined in our facilities. Rough parts include various sized steel and iron castings and forgings, which are machined to final specification levels inside our facilities. Finished parts are ready to assemble components, which are made either to Caterpillar specifications or to supplier developed specifications. We machine and assemble some of the components used in our machines, engines and power generation units and to support our after-market dealer parts sales. We also purchase various goods and services used in production, logistics, offices and product development processes. We maintain global strategic sourcing models to meet our global facilities' production needs while building long-term supplier relationships and leveraging enterprise spend. We expect our suppliers to maintain, at all times, industry-leading levels of quality and the ability to timely deliver raw materials and component products for our machine and engine products. However, in some cases, increases in demand or supply chain disruptions have led to parts and components constraints across some products. We use a variety of agreements with suppliers to protect our intellectual property and processes to monitor and mitigate risks of the supply base causing a business disruption. The risks monitored include supplier financial viability, the ability to increase or decrease production levels, business continuity, quality and delivery.

**[0000018230-26-000008:1:24]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Patents and Trademarks
> We own a number of patents and trademarks, which have been obtained over a period of years and relate to the products we manufacture and the services we provide. These patents and trademarks are generally considered beneficial to our business. We do not regard our business as being dependent upon any single patent or group of patents.
> Order Backlog
> The dollar amount of backlog believed to be firm was approximately $51.2 billion at December 31, 2025 and $30.0 billion at December 31, 2024. Compared with year-end 2024, the order backlog increased across the primary segments, with the largest increase in Power & Energy. Of the total backlog at December 31, 2025, approximately $19.3 billion was not expected to be filled in 2026.
> Dealers and Distributors

**[0000018230-26-000008:1:25]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> We distribute our machines principally through a worldwide organization of dealers (dealer network), 41 located in the United States and 109 located outside the United States, serving 190 countries. We sell reciprocating engines principally through the dealer network and to other manufacturers for use in products. We also sell some of the reciprocating engines manufactured by our subsidiary Perkins Engines Company Limited through its worldwide network of 86 distributors covering 183 countries. We sell the FG Wilson branded electric power generation systems through its worldwide network of 108 distributors covering 159 countries.
> Our dealers do not deal exclusively with our products; however, in most cases sales and servicing of our products are the dealers' principal business. We sell some products, primarily turbines and locomotives, directly to end customers through sales forces employed by the company. At times, these employees are assisted by independent sales representatives.

**[0000018230-26-000008:1:31]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Management aligns employment levels with the needs of the business. We believe we have the appropriate human capital resources to successfully operate and deliver our enterprise strategy. As of December 31, 2025, we employed about 118,000 full-time persons of whom approximately 66,400 were located outside the United States. In the United States, we employed approximately 51,600 full-time persons, most of whom are at-will employees and, therefore, not subject to any type of employment contract or agreement. At select business units, we have hired certain highly specialized employees under employment contracts that specify a term of employment, pay and other benefits.
> Full-Time Employees at Year-End
> 2025 | 2024
> Inside U.S. | 51,600 | 51,500
> Outside U.S. | 66,400 | 61,400
> Total | 118,000 | 112,900
> By Region:
> North America | 52,100 | 52,000
> EAME | 16,700 | 15,900
> Latin America | 22,300 | 19,700
> Asia/Pacific | 26,900 | 25,300
> Total | 118,000 | 112,900

**Verdict:** found

**Note:** 

### CAT · durable_competitive_advantage

**Durable competitive advantage.** Does the filing give concrete evidence of an advantage that protects the company's profits from competitors over many years (for example a brand, scale or cost position, switching costs, a network, patents, or a regulated franchise)?

- **found** ("evidence found"): The filing states a source of advantage AND a checkable specific for it: a market share or rank figure; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated network size. A statement that an asset exists or matters (brand, trade secrets, patents, 'strong' distribution) without a measure is not enough.
- **weak** ("evidence weak"): The advantage is only asserted, or an asset is named as important (brand, trade secrets, patents, scale) without any measure; or the specifics are offset by the filing's own statements that competitors or customers can readily erode the position.
- **insufficient** ("insufficient evidence"): The retrieved text says nothing about the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1, Item 1A), in filing order:

**[0000018230-26-000008:1:1]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Item 1.Business.
> General
> Originally organized as Caterpillar Tractor Co. in 1925 in the State of California, our company was reorganized as Caterpillar Inc. in 1986 in the State of Delaware. As used herein, the term "Caterpillar," "we," "us," "our" or "the company" refers to Caterpillar Inc. and its subsidiaries unless designated or identified otherwise.
> Overview
> With 2025 sales and revenues of $67.589 billion, Caterpillar Inc. is shaping the future as the world's leading manufacturer of construction and mining equipment, off-highway diesel and natural gas engines, industrial gas turbines and diesel-electric locomotives. Backed by one of the largest independent global dealer networks and financing services through Cat Financial, the company's primary business segments: Power & Energy, Construction Industries and Resource Industries are solving customers' toughest challenges through commercial excellence and advanced technology, driven by a highly skilled, dedicated global team.
> Enterprise Strategy

**[0000018230-26-000008:1:22]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Caterpillar products and services are sold worldwide into a variety of highly competitive markets. In all markets, we compete on the basis of product performance, customer service, quality and price. From time to time, the intensity of competition results in price discounting in a particular industry or region. Such price discounting puts pressure on margins and can negatively impact operating profit. Outside the United States, certain competitors enjoy competitive advantages inherent to operating in their home countries or regions.
> Raw Materials and Component Products

**[0000018230-26-000008:1:24]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Patents and Trademarks
> We own a number of patents and trademarks, which have been obtained over a period of years and relate to the products we manufacture and the services we provide. These patents and trademarks are generally considered beneficial to our business. We do not regard our business as being dependent upon any single patent or group of patents.
> Order Backlog
> The dollar amount of backlog believed to be firm was approximately $51.2 billion at December 31, 2025 and $30.0 billion at December 31, 2024. Compared with year-end 2024, the order backlog increased across the primary segments, with the largest increase in Power & Energy. Of the total backlog at December 31, 2025, approximately $19.3 billion was not expected to be filled in 2026.
> Dealers and Distributors

**[0000018230-26-000008:1:26]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> While the large majority of our worldwide dealers are independently owned and operated, we own and operate a dealership in Japan that covers approximately 80% of the Japanese market: Nippon Caterpillar Division. We are currently operating this Japanese dealer directly and we report its results in the All Other Segment. There are also three independent dealers in the Southern Region of Japan.
> 6
> Table of Contents
> For Caterpillar-branded products, the company's relationship with each of its independent dealers is memorialized in standard sales and service agreements. Pursuant to these agreements, the company grants the dealer the right to purchase and sell its products and to service the products in a specified geographic service territory. The company establishes prices to dealers after receiving input from dealers on transactional pricing in the marketplace. The company also agrees to defend its intellectual property and to provide warranty and technical support to the dealer. The agreement further grants the dealer a non-exclusive license to use the company's trademarks, service marks and brand names. In some instances, a separate trademark agreement exists between the company and a dealer.

**[0000018230-26-000008:1A:14]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Our business relies on continued global demand for our brands and products. To achieve business goals, we must develop and sell products that appeal to our dealers, OEMs and end-user customers. This is dependent on a number of factors, including our ability to maintain key dealer relationships; our ability to produce products that meet the quality, performance and price expectations of our customers and our ability to develop effective sales, advertising and marketing programs. In addition, our continued success in selling products that appeal to our customers is dependent on leading-edge innovation, with respect to both products and operations, and on the availability and effectiveness of legal protection for our innovations. Failure to continue to deliver high quality, innovative, competitive products to the marketplace, to adequately protect our intellectual property rights; to supply products that meet applicable regulatory requirements, including engine exhaust emission requirements or to predict market demands for, or gain market acceptance of, our products, could have a negative impact on our business, results of operations and financial condition.
> We operate in a highly competitive environment, which could adversely affect our sales and pricing.

**[0000018230-26-000008:1A:15]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> We operate in a highly competitive environment. We compete on the basis of a variety of factors, including product performance, customer service, quality and price. There can be no assurance that our products will be able to compete successfully with other companies' products. Thus, our share of industry sales could be reduced due to aggressive pricing or product strategies pursued by competitors, unanticipated product or manufacturing difficulties, our failure to price our products competitively, our failure to produce our products at a competitive cost or an unexpected buildup in competitors' new machine or dealer-owned rental fleets, which could lead to downward pressure on machine rental rates and/or used equipment prices.
> Lack of customer acceptance of price increases we announce from time to time, changes in customer requirements for price discounts, changes in our customers' behavior or a weak pricing environment could have an adverse impact on our business, results of operations and financial condition.
> In addition, our results and ability to compete may be impacted negatively by changes in our geographic and product mix of sales.
> Increased information technology security threats and more sophisticated computer crime pose a risk to our systems, networks, products and services.

**[0000018230-26-000008:1A:31]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> •Market developments that may affect customer confidence levels and cause declines in the demand for financing and adverse changes in payment patterns, causing increases in delinquencies and default rates, which could increase Cat Financial's write-offs and provision for credit losses.
> •The process Cat Financial uses to estimate losses inherent in its credit exposure requires a high degree of management's judgment regarding numerous subjective qualitative factors, including forecasts of economic conditions and how economic predictors might impair the ability of its borrowers to repay their loans. Financial market disruption and volatility may impact the accuracy of these judgments.
> •Cat Financial's ability to engage in routine funding transactions or to borrow from other financial institutions on acceptable terms or at all could be adversely affected by disruptions in the capital markets or other events, including actions by rating agencies and deteriorating investor expectations.
> •As Cat Financial's borrowing agreements are primarily with financial institutions, their ability to perform in accordance with any of our underlying agreements could be adversely affected by market volatility and/or disruptions in financial markets.
> 15
> Table of Contents
> Changes in interest rates or market liquidity conditions could adversely affect Cat Financial's and our earnings and/or cash flow.

**[0000018230-26-000008:1A:39]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> We maintain certain defined benefit pension plans for our employees, which impose on us certain funding obligations. We use many assumptions in determining our future payment obligations under the plans. Significant adverse changes in credit or capital markets could result in actual rates of return on pension investments being materially lower than projected and result in increased contribution requirements. These factors could increase our payment obligations under the plans and, as a result, adversely affect our business and overall financial condition. We may be required to make material contributions to our pension plans in the future and may fund contributions through the use of cash on hand, the proceeds of borrowings, shares of our common stock or a combination of the foregoing, as permitted by applicable law. We employ a liability-driven investment strategy, where the interest rate sensitivity of the pension investments and pension obligations are aligned to reduce funded status volatility.
> LEGAL & REGULATORY RISKS
> Our global operations are subject to a wide range of trade and anti-corruption laws and regulations.

**Verdict:** Found

**Note:** 

### CAT · candid_management

**Candid management.** Does management openly discuss setbacks, mistakes, declines and uncertainty in its own words, rather than only successes?

- **found** ("evidence found"): Management's own account of a setback that it attributes at least partly to the company's own decisions or execution; or a target or guidance of its own that was missed; or an acknowledged material weakness, restatement or write-down of something management chose (an acquisition, investment or project), stated plainly.
- **weak** ("evidence weak"): Declines or charges explained only by external factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even when quantified; or generic caution ('results may fluctuate', 'we face risks'); or a setback mentioned without explanation.
- **insufficient** ("insufficient evidence"): The retrieved text is promotional or boilerplate and gives nothing to judge candour either way, or MD&A and Risk Factors are missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.
- **Limitation:** Limitation: 10-K text is reviewed by lawyers, and candour is better judged from shareholder letters (outside this tool's scope). Do not read polished or detailed prose as candour;

Passages (Item 7, Item 1A), in filing order:

**[0000018230-26-000008:1A:1]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Item 1A.Risk Factors.
> The statements in this section describe the most significant risks to our business and should be considered carefully in conjunction with Part II, Item 7 "Management's Discussion and Analysis of Financial Condition and Results of Operations" and the "Notes to Consolidated Financial Statements" of Part II, Item 8 "Financial Statements and Supplementary Data" to this Form 10-K. In addition, the statements in this section and other sections of this Form 10-K, including in Part II, Item 7 "Management's Discussion and Analysis of Financial Condition and Results of Operations," include "forward-looking statements" as that term is defined in the Private Securities Litigation Reform Act of 1995 and involve uncertainties that could significantly impact results. Forward-looking statements give current expectations or forecasts of future events about the company or our outlook. You can identify forward-looking statements by the fact they do not relate to historical or current facts and by the use of words such as "believe," "expect," "estimate," "anticipate," "will be," "should," "plan," "forecast," "target," "guide," "project," "intend," "could" and similar words or expressions.

**[0000018230-26-000008:1A:4]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Our results of operations are materially affected by economic conditions globally and regionally and in the particular industries we serve. The demand for our products and services tends to be cyclical and can be significantly reduced in periods of economic weakness characterized by lower levels of government and business investment, lower levels of business confidence, lower corporate earnings, high real interest rates, lower credit activity or tighter credit conditions, perceived or actual industry overcapacity, higher unemployment and lower consumer spending. A prolonged period of economic weakness may also result in increased expenses due to higher allowances for doubtful accounts and potential goodwill and asset impairment charges. Economic conditions vary across regions and countries, and demand for our products and services generally increases in those regions and countries experiencing economic growth and investment. Slower economic growth or a change in the global mix of regions and countries experiencing economic growth and investment could have an adverse effect on our business, results of operations and financial condition.

**[0000018230-26-000008:1A:9]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> We rely on suppliers to produce or secure material required for the manufacture of our products. Production challenges at suppliers (including suppliers of semiconductors), a disruption in deliveries to or from suppliers or decreased availability of raw materials or commodities could have an adverse effect on our ability to meet our commitments to customers or increase our operating costs. On the other hand, in circumstances where demand for our products is less than we expect, we may experience excess inventories and be forced to incur additional costs and our profitability may suffer. Our business, competitive position, results of operations or financial condition could be negatively impacted if supply is insufficient for our operations, if significant transportation delays interfere with deliveries, if we experience excess inventories or if we are unable to adjust our production schedules or our purchases from suppliers to reflect changes in customer demand and market fluctuations on a timely basis.
> Changes in government monetary or fiscal policies may negatively impact our results.

**[0000018230-26-000008:1A:14]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Our business relies on continued global demand for our brands and products. To achieve business goals, we must develop and sell products that appeal to our dealers, OEMs and end-user customers. This is dependent on a number of factors, including our ability to maintain key dealer relationships; our ability to produce products that meet the quality, performance and price expectations of our customers and our ability to develop effective sales, advertising and marketing programs. In addition, our continued success in selling products that appeal to our customers is dependent on leading-edge innovation, with respect to both products and operations, and on the availability and effectiveness of legal protection for our innovations. Failure to continue to deliver high quality, innovative, competitive products to the marketplace, to adequately protect our intellectual property rights; to supply products that meet applicable regulatory requirements, including engine exhaust emission requirements or to predict market demands for, or gain market acceptance of, our products, could have a negative impact on our business, results of operations and financial condition.
> We operate in a highly competitive environment, which could adversely affect our sales and pricing.

**[0000018230-26-000008:1A:31]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> •Market developments that may affect customer confidence levels and cause declines in the demand for financing and adverse changes in payment patterns, causing increases in delinquencies and default rates, which could increase Cat Financial's write-offs and provision for credit losses.
> •The process Cat Financial uses to estimate losses inherent in its credit exposure requires a high degree of management's judgment regarding numerous subjective qualitative factors, including forecasts of economic conditions and how economic predictors might impair the ability of its borrowers to repay their loans. Financial market disruption and volatility may impact the accuracy of these judgments.
> •Cat Financial's ability to engage in routine funding transactions or to borrow from other financial institutions on acceptable terms or at all could be adversely affected by disruptions in the capital markets or other events, including actions by rating agencies and deteriorating investor expectations.
> •As Cat Financial's borrowing agreements are primarily with financial institutions, their ability to perform in accordance with any of our underlying agreements could be adversely affected by market volatility and/or disruptions in financial markets.
> 15
> Table of Contents
> Changes in interest rates or market liquidity conditions could adversely affect Cat Financial's and our earnings and/or cash flow.

**[0000018230-26-000008:1A:33]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Cat Financial manages interest rate and market liquidity risks through a variety of techniques that include a match funding strategy, the selective use of derivatives and a broadly diversified funding program. There can be no assurance, however, that fluctuations in interest rates and market liquidity conditions will not have an adverse impact on its and our earnings and cash flows. If any of the variety of instruments and strategies Cat Financial uses to hedge its exposure to these types of risk is ineffective, this may have an adverse impact on our earnings and cash flows. With respect to Insurance Services' investment activities, changes in equity and bond markets could result in a decline in value of its investment portfolio, resulting in an unfavorable impact to earnings.
> An increase in delinquencies, repossessions or net losses of Cat Financial customers could adversely affect its results.

**[0000018230-26-000008:1A:39]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> We maintain certain defined benefit pension plans for our employees, which impose on us certain funding obligations. We use many assumptions in determining our future payment obligations under the plans. Significant adverse changes in credit or capital markets could result in actual rates of return on pension investments being materially lower than projected and result in increased contribution requirements. These factors could increase our payment obligations under the plans and, as a result, adversely affect our business and overall financial condition. We may be required to make material contributions to our pension plans in the future and may fund contributions through the use of cash on hand, the proceeds of borrowings, shares of our common stock or a combination of the foregoing, as permitted by applicable law. We employ a liability-driven investment strategy, where the interest rate sensitivity of the pension investments and pension obligations are aligned to reduce funded status volatility.
> LEGAL & REGULATORY RISKS
> Our global operations are subject to a wide range of trade and anti-corruption laws and regulations.

**[0000018230-26-000008:7:1]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Item 7.Management's Discussion and Analysis of Financial Condition and Results of Operations.
> The following Management's Discussion and Analysis of Financial Condition and Results of Operations (MD&A) is intended to provide information that will assist the reader in understanding the company's Consolidated Financial Statements, the changes in certain key items in those financial statements between select periods and the primary factors that accounted for those changes. In addition, we discuss how certain accounting principles, policies and critical estimates affect our Consolidated Financial Statements. Our discussion also contains certain forward-looking statements related to future events and expectations. This MD&A should be read in conjunction with our discussion of cautionary statements and significant risks to the company's business under Item 1A. Risk Factors of the 2025 Form 10-K.
> Highlights for the full-year 2025 include:
> •Sales and revenues for 2025 were $67.589 billion, an increase of $2.780 billion, or 4 percent, compared with $64.809 billion for 2024. Sales were higher in Power & Energy, about flat in Resource Industries and slightly lower in Construction Industries.

**Verdict:** found

**Note:** 

### CAT · rational_capital_allocation

**Rational capital allocation.** Does the filing show what management does with the cash the business generates (reinvestment, acquisitions, buybacks, dividends, debt repayment) and explain it? You judge whether it is documented concretely, not whether prices paid were good.

- **found** ("evidence found"): The filing quantifies at least one past action in the fiscal year (share repurchases, dividends, acquisitions, capital expenditure or debt repayment, with an amount) AND states a policy, priority or rationale for how cash is used. Not every action needs an amount.
- **weak** ("evidence weak"): Forward-looking plans only; or actions with no amount at all; or amounts with no stated policy, priority or rationale.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what was done with cash, or MD&A is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.

Passages (Item 7), in filing order:

**[0000018230-26-000008:7:1]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Item 7.Management's Discussion and Analysis of Financial Condition and Results of Operations.
> The following Management's Discussion and Analysis of Financial Condition and Results of Operations (MD&A) is intended to provide information that will assist the reader in understanding the company's Consolidated Financial Statements, the changes in certain key items in those financial statements between select periods and the primary factors that accounted for those changes. In addition, we discuss how certain accounting principles, policies and critical estimates affect our Consolidated Financial Statements. Our discussion also contains certain forward-looking statements related to future events and expectations. This MD&A should be read in conjunction with our discussion of cautionary statements and significant risks to the company's business under Item 1A. Risk Factors of the 2025 Form 10-K.
> Highlights for the full-year 2025 include:
> •Sales and revenues for 2025 were $67.589 billion, an increase of $2.780 billion, or 4 percent, compared with $64.809 billion for 2024. Sales were higher in Power & Energy, about flat in Resource Industries and slightly lower in Construction Industries.

**[0000018230-26-000008:7:40]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> We generate significant capital resources from operating activities, which are the primary source of funding for our MP&E operations. Funding for these businesses is also available from commercial paper and long-term debt issuances. Financial Products' operations are funded primarily from commercial paper, term debt issuances and collections from its existing portfolio. During 2025, we had positive operating cash flow within both our MP&E and Financial Products' operations. On a consolidated basis, we ended 2025 with $9.980 billion of cash, an increase of $3.091 billion from year-end 2024. In addition, MP&E invests in available-for-sale debt securities and bank time deposits that are considered highly liquid and are available for current operations. These MP&E securities were $1.230 billion as of December 31, 2025 and are included in Prepaid expenses and other current assets and Other assets in the Consolidated Statement of Financial Position. We intend to maintain a strong cash and liquidity position.
> Consolidated operating cash flow for 2025 was $11.739 billion, down $296 million compared to 2024. The decrease was primarily due to lower profit before taxes, adjusted for non-cash items, partially offset by lower cash taxes paid and changes in accrued wages, salaries, and employee benefits.

**[0000018230-26-000008:7:49]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Net cash used by investing activities in 2025 was $2.870 billion, compared with net cash provided of $133 million in 2024. The change was primarily due to lower proceeds from maturities and sale of securities, primarily due to time deposit maturities in 2024; increased activity related to intercompany lending with Financial Products; and an increase in capital expenditures.
> Net cash used for financing activities during 2025 was $6.184 billion, compared with $11.417 billion in 2024. The change was primarily due to lower payments to repurchase common stock, higher proceeds from debt issued and lower payments on debt in 2025 compared to 2024.
> While our short-term priorities for the use of cash may vary from time to time as business needs and conditions dictate, our resource allocation framework is focused on the following priorities. Our top priority is to maintain a strong financial position in support of a mid-A rating. Next, we intend to fund operational commitments and strategic growth initiatives assessed using the Operating & Execution Model. Then, we intend to return capital to shareholders through dividend growth and share repurchases. Additional information on the resource allocation framework is as follows:

**[0000018230-26-000008:7:51]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> We intend to utilize our liquidity and debt capacity to fund initiatives targeted to drive long term profitable growth focused on our three strategic growth pillars. Our strategic growth pillars are commercial excellence, advanced technology leadership and transforming how we work. These pillars work together to drive sustainable growth, innovation and operational efficiency for Caterpillar and our customers.
> On February 3, 2026, the Federal Court of Australia approved Caterpillar's acquisition of RPMGlobal Holdings Limited, an Australian based software company. The transaction is expected to close in the final two weeks of February with a purchase price of approximately $790 million, excluding cash acquired. RPMGlobal is a leading provider of mining software solutions with deep domain expertise in mining technology enablement and data-driven software solutions at every stage of the mining lifecycle.
> Return to shareholders — Our goal is to return substantially all MP&E free cash flow to shareholders over time in the form of dividends and share repurchases, while maintaining our mid-A rating.

**[0000018230-26-000008:7:52]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> MP&E free cash flow is a liquidity measure we use to determine the cash generated and available for financing activities including debt repayments, dividends and share repurchases. We define MP&E free cash flow as cash from MP&E operations less capital expenditures, excluding discretionary pension and other postretirement benefit plan contributions.
> Each quarter, our Board of Directors reviews the company's dividend for the applicable quarter. The Board evaluates the financial condition of the company and considers corporate cash flow, the company's liquidity needs, the economic outlook, and the health and stability of global credit markets to determine whether to maintain or change the quarterly dividend. In December 2025, the Board of Directors approved maintaining our quarterly dividend representing $1.51 per share, and we continue to expect our strong financial position to support the dividend. Dividends paid totaled $2.749 billion in 2025.

**[0000018230-26-000008:7:53]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Our share repurchase plans are subject to the company's resource allocation framework and are evaluated on an ongoing basis considering the financial condition of the company, corporate cash flow, the company's liquidity needs, the economic outlook, and the health and stability of global credit markets. The timing and amount of future repurchases may vary depending on market conditions and investing priorities. In May 2022, the Board approved a share repurchase authorization (the 2022 Authorization) of up to $15.0 billion of Caterpillar common stock effective August 1, 2022 with no expiration. In June 2024, the Board approved an additional share repurchase authorization (the 2024 Authorization) of up to $20.0 billion of Caterpillar common stock, effective June 12, 2024, with no expiration. In 2025, we repurchased $5.190 billion of Caterpillar common stock. As of December 31, 2025, the 2022 Authorization was fully utilized and $14.937 billion remained under the 2024 Authorization. Caterpillar's basic shares outstanding as of December 31, 2025 were approximately 465 million.
> Financial Products

**[0000018230-26-000008:7:60]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> For reporting units where we perform a quantitative goodwill impairment test, the process requires valuation of the respective reporting unit, which we primarily determine using an income approach based on a discounted five year forecasted cash flow with a year-five residual value. We compute the residual value using the constant growth method, which values the forecasted cash flows in perpetuity. The assumptions about future cash flows and growth rates are based on each reporting unit's long-term forecast and are subject to review and approval by senior management. A reporting unit's discount rate is a risk-adjusted weighted average cost of capital, which we believe approximates the rate from a market participant's perspective. The estimated fair value could be impacted by changes in market conditions, interest rates, growth rates, tax rates, costs, pricing and capital expenditures. We categorize the fair value determination as Level 3 in the fair value hierarchy due to its use of internal projections and unobservable measurement inputs.

**[0000018230-26-000008:7:90]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/18230/000001823026000008/cat-20251231.htm)

> Other restructuring (income) costs | 195 | 46
> Changes in estimates related to prior years | — | (47)
> Excess stock-based compensation | — | (57)
> Twelve Months Ended December 31, 2024 - Adjusted | $ | 13,578 | $ | 2,910
> In addition, we provide a calculation of MP&E free cash flow as we believe it is an important measure for investors to determine the cash generation available for financing activities including debt repayments, dividends and share repurchases.
> Reconciliations of MP&E free cash flow to the most directly comparable GAAP measure, net cash provided by operating activities are as follows:
> Millions of dollars | Twelve Months Ended December 31,
> 2025 | 2024
> MP&E net cash provided by operating activities 1 | $ | 12,278 | $ | 11,437
> MP&E capital expenditures | (2,794) | (1,988)
> MP&E free cash flow | $ | 9,484 | $ | 9,449
> 1 See reconciliation of MP&E net cash provided by operating activities to consolidated net cash provided by operating activities on page 53.
> 49
> Table of Contents
> Supplemental Consolidating Data
> We are providing supplemental consolidating data for the purpose of additional analysis. We have grouped the data as follows:

**Verdict:** found

**Note:** 

---

## JNJ

Form 10-K, accession 0000200406-26-000016, filed 2026-02-11, period 2025-12-28. [Open the filing on sec.gov](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

### JNJ · understandable_business

**Understandable business.** Can the business be explained simply: what the company sells, to whom, and how it makes money?

- **found** ("evidence found"): The filing names specific products or services, the customers or markets they are sold to, and how revenue is earned (for example segments with figures, a pricing or sales model), in plain terms.
- **weak** ("evidence weak"): The business is described only in general or promotional terms (a 'leading provider of solutions'), or the filing says what is sold but not who buys it or how it earns money.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what the company sells or how it earns money, or the Business section is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1), in filing order:

**[0000200406-26-000016:1:1]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Item 1. Business
> General
> Johnson & Johnson and its subsidiaries (the Company) have approximately 138,200 employees worldwide engaged in the research and development, manufacture and sale of a broad range of products in the healthcare field. Johnson & Johnson is a holding company, with operating companies conducting business in virtually all countries of the world. The Company's primary focus is products related to human health and well-being. Johnson & Johnson was incorporated in the State of New Jersey in 1887.
> The Chief Operating Decision Maker (CODM) is the Company's Chief Executive Officer (Principal Executive Officer). The Executive Committee is Johnson & Johnson's senior leadership team responsible for setting the strategy and priorities of the Company and driving accountability at all levels. Within the strategic parameters provided by the Executive Committee, senior management groups at U.S. and international operating companies are each responsible for their own strategic plans and the day-to-day operations of those companies.
> Segments of business

**[0000200406-26-000016:1:2]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> The Company is organized into two business segments: Innovative Medicine and MedTech. Additional information required by this item is incorporated herein by reference to the narrative and tabular descriptions of segments and operating results under: Item 7. Management's discussion and analysis of results of operations and financial condition of this Report; and Note 17 Segments of business and geographic areas of the notes to consolidated financial statements included in Item 8 of this Report.
> Innovative Medicine

**[0000200406-26-000016:1:9]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> In October 2025, the Company announced its intention to separate its Orthopaedics business. The Company intends to explore multiple paths to effect the planned separation with a targeted completion within 18 to 24 months after the initial announcement.
> Geographic areas
> The Company conducts business in virtually all countries of the world with the primary focus on products related to human health and well-being. The products made and sold in the international business include many of those described above under Segments of Business – Innovative Medicine and MedTech. However, the principal markets, products and methods of distribution in the international business vary with the country and the culture. The products sold in the international business include those developed in the U.S. and by subsidiaries abroad.
> 2
> Investments and activities in some countries outside the U.S. are subject to higher risks than comparable U.S. activities because the investment and commercial climate may be influenced by financial instability in international economies, restrictive economic policies and political and legal system uncertainties.
> Raw materials

**[0000200406-26-000016:1:15]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> The medical device regulatory framework and the evolving privacy, data localization, and emerging cyber security laws and regulations around the world are examples of such increased regulation. Within the U.S., an increasing number of U.S. States have enacted comprehensive privacy laws, and federal regulators (e.g., the U.S. FDA, FTC and HHS) continue to stress the intersection of health and privacy as a compliance and enforcement priority. In the EU, multiple directives and laws (including NIS2, EHDS, the Data Act, the Cyber Resilience Act, and the AI Act) are rapidly changing privacy and cybersecurity compliance requirements while introducing new enforcement risks. In addition, China has introduced broad personal information protection and data security regulations, with more anticipated, thereby increasing China's scrutiny of company compliance and data transfer practices. With other jurisdictions enacting similar privacy laws, local data protection authorities will force greater accountability on the collection, access and use of personal data in the healthcare industry. These laws can also restrict transfers of data across borders, potentially impacting how data-driven health care solutions are developed and deployed globally in a compliant manner. Moreover, as a result of the broad scale release and availability of Artificial Intelligence (AI) technologies such as generative AI, a global trend towards more comprehensive and nuanced regulation to ensure the ethical use, privacy, and security of AI is underway that includes standards for transparency, accountability, and fairness, which will require compliance developments or enhancements.

**[0000200406-26-000016:1:20]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Our business has been and continues to be affected by federal and state legislation that alters the pricing, coverage, and reimbursement landscape. The federal Inflation Reduction Act of 2022 (IRA) includes provisions that effectively authorize the government to establish prices for certain high-spend single-source drugs and biologics reimbursed by the Medicare program, starting in 2026 for Medicare Part D drugs and 2028 for Medicare Part B drugs. In 2023, the Centers for Medicare & Medicaid Services (CMS) published the first "Selected Drug" list, which includes XARELTO and STELARA as well as IMBRUVICA, which is developed in collaboration and co-commercialized in the U.S. with Pharmacyclics LLC, an AbbVie company. The IRA specifies a ceiling price but not a minimum price for selected drugs and does not require CMS to use a specific framework for determining selected drug prices. The selected products are subject to a government-established price for the Medicare population beginning in 2026. CMS has indicated that, beginning in 2027, it will remove Xarelto and Stelara from the Selected Drug List, such that the products will no longer be subject to the IRA's minimum pricing provisions. In January 2026, CMS published the Selected Drug list for 2028, which includes ERLEADA.

**[0000200406-26-000016:1:23]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> In January 2026, the Company reached an agreement with the U.S. Administration to improve access to medicines and lower costs for U.S. patients. Additionally, we expect continued scrutiny on drug pricing and government price reporting from Congress, agencies, and other bodies at the federal and state levels, which may result in additional regulations, including models or other mechanisms to increase pricing controls and/or transparency.
> There are a number of additional bills pending in Congress and healthcare reform proposals at the state level that would affect drug pricing, including in the Medicare and Medicaid programs. This changing legal landscape has both positive and negative impacts on the U.S. healthcare industry with much remaining uncertain as to how various provisions of federal and state law, and potential modification or repeal of these laws, will ultimately affect the industry. The IRA and any other federal or state legislative change could affect the pricing and market conditions for our products.

**[0000200406-26-000016:1:25]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> As of December 28, 2025 and December 29, 2024 the number of employees was approximately:
> 2025 | 2024
> Employees(1) | 140,800 | 139,800
> Full-time equivalent (FTE) positions(2) | 138,200 | 138,100
> (1)"Employee" is defined as an individual working full-time or part-time, excluding fixed term employees, interns and co-op employees. Employee data may not include full population from more recently acquired companies and individuals on long-term disability are excluded. Contingent workers, contractors and subcontractors are also excluded.
> (2)FTE represents the total number of full-time equivalent positions and does not reflect the total number of individual employees as some work part-time.
> Employees by region (in percentages)
> Strategy
> The Company believes that its employees are critical to its continued success and are an essential element of its long-term strategy. Management is responsible for ensuring that its policies and processes reflect and reinforce the Company's desired corporate culture, including policies and processes related to strategy, risk management, and ethics and compliance. The Company's human capital management strategy is built on three fundamental focus areas:
> •Attracting and recruiting top talent
> •Developing and retaining top talent
> •Empowering and inspiring talent

**[0000200406-26-000016:1:31]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> In addition, the Restated Certificate of Incorporation, as amended, Amended and Restated By-Laws, the written charters of the Audit Committee, the Compensation & Benefits Committee, the Nominating & Corporate Governance Committee, the Regulatory Compliance & Sustainability Committee, and the Science & Technology Committee of the Board of Directors, and the Company's Principles of Corporate Governance, Code of Business Conduct (for employees), Code of Business Conduct & Ethics for Members of the Board of Directors and Executive Officers, and other corporate governance materials are available on the Company's website at www.investor.jnj.com/governance/corporate-governance-overview and will be provided without charge to any shareholder submitting a written request, as provided above. The information on www.jnj.com, investor.jnj.com and www.factsabouttalc.com is not, and will not be deemed, a part of this Report or incorporated into any other filings the Company makes with the SEC.
> 8

**Verdict:** found

**Note:** 

### JNJ · durable_competitive_advantage

**Durable competitive advantage.** Does the filing give concrete evidence of an advantage that protects the company's profits from competitors over many years (for example a brand, scale or cost position, switching costs, a network, patents, or a regulated franchise)?

- **found** ("evidence found"): The filing states a source of advantage AND a checkable specific for it: a market share or rank figure; a regulated exclusive franchise or service territory; a quantified scale or cost position; long-term contracts with stated terms; a stated network size. A statement that an asset exists or matters (brand, trade secrets, patents, 'strong' distribution) without a measure is not enough.
- **weak** ("evidence weak"): The advantage is only asserted, or an asset is named as important (brand, trade secrets, patents, scale) without any measure; or the specifics are offset by the filing's own statements that competitors or customers can readily erode the position.
- **insufficient** ("insufficient evidence"): The retrieved text says nothing about the company's competitive position, or only lists competitors, threats and competitive pressure. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.

Passages (Item 1, Item 1A), in filing order:

**[0000200406-26-000016:1:10]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Raw materials essential to the Company's business are generally readily available from multiple sources. Where there are exceptions, the temporary unavailability of those raw materials would not likely have a material adverse effect on the financial results of the Company.
> Patents
> The Company's subsidiaries have made a practice of obtaining patent protection on their products and processes where possible. They own, or are licensed under, a significant number of patents in the U.S. and other countries relating to their products, product uses, formulations and manufacturing processes. The Company's subsidiaries face patent challenges from third parties, including challenges seeking to manufacture and market generic and biosimilar versions of the Company's key pharmaceutical products prior to expiration of the applicable patents covering those products. Significant legal proceedings and claims involving the Company's patent and other intellectual property are described in Note 19 Legal proceedings—Intellectual property of the Notes to Consolidated Financial Statements included in Item 8 of this Report.

**[0000200406-26-000016:1:13]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> In all of their product lines, the Company's subsidiaries compete with companies both locally and globally. Competition exists in all product lines without regard to the number and size of the competing companies involved. Competition in research, both internally and externally sourced, involving the development and the improvement of new and existing products and processes, is particularly significant. The development of new and innovative products, as well as protecting the underlying intellectual property of the Company's product portfolio, is important to the Company's success in all areas of its business. The competitive environment requires substantial investments in continuing research.
> Environment
> The Company is subject to a variety of environmental laws and regulations in the United States and other jurisdictions. The Company believes that its operations comply in all material respects with applicable environmental laws and regulations. The Company's compliance with these requirements is not expected to have a material effect upon its capital expenditures, cash flows, earnings or competitive position.
> Regulation

**[0000200406-26-000016:1:23]** Item 1 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> In January 2026, the Company reached an agreement with the U.S. Administration to improve access to medicines and lower costs for U.S. patients. Additionally, we expect continued scrutiny on drug pricing and government price reporting from Congress, agencies, and other bodies at the federal and state levels, which may result in additional regulations, including models or other mechanisms to increase pricing controls and/or transparency.
> There are a number of additional bills pending in Congress and healthcare reform proposals at the state level that would affect drug pricing, including in the Medicare and Medicaid programs. This changing legal landscape has both positive and negative impacts on the U.S. healthcare industry with much remaining uncertain as to how various provisions of federal and state law, and potential modification or repeal of these laws, will ultimately affect the industry. The IRA and any other federal or state legislative change could affect the pricing and market conditions for our products.

**[0000200406-26-000016:1A:1]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Item 1A. Risk factors
> An investment in the Company's common stock or debt securities involves risks and uncertainties. The Company seeks to identify, manage and mitigate risks to our business, but uncertainties and risks are difficult to predict and many are outside of the Company's control and cannot therefore be eliminated. In addition to the other information in this report and the Company's other filings with the SEC, investors should consider carefully the factors set forth below. Investors should be aware that it is not possible to predict or identify all such factors and that the following is not meant to be a complete discussion of all potential risks or uncertainties. If known or unknown risks or uncertainties materialize, the Company's business, results of operations or financial condition could be adversely affected, potentially in a material way.
> Risks related to our business, industry and operations
> The Company's businesses operate in highly competitive product markets and competitive pressures could adversely affect the Company's earnings.

**[0000200406-26-000016:1A:2]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> The Company faces substantial competition in its two operating segments and in all geographic markets. The Company's businesses compete with companies of all sizes on the basis of cost-effectiveness, technological innovations, intellectual property rights, product performance, real or perceived product advantages, pricing and availability and rate of reimbursement. The Company also competes with other market participants in securing rights to acquisitions, collaborations and licensing agreements with third parties. Competition for rights to product candidates and technologies may result in significant investment and acquisition costs and onerous agreement terms for the Company. Competitors' development of more effective or less costly products, and/or their ability to secure patent and other intellectual property rights and successfully market products ahead of the Company, could negatively impact sales of the Company's existing products as well as its ability to bring new products to market despite significant prior investment in the related product development. The Company may also experience operational and financial risk in connection with acquisitions if we are unable to fully identify potential risks and liabilities associated with acquired businesses or products, successfully integrate operations and employees, and successfully identify and realize synergies with existing businesses while containing acquisition-related strain on our management, operations and financial resources.

**[0000200406-26-000016:1A:10]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Sales of the Company's Innovative Medicine and MedTech products are significantly affected by reimbursements by third-party payors such as government healthcare programs, private insurance plans and managed care organizations. As part of various efforts to contain healthcare costs, these payors are putting downward pressure on prices at which products will be reimbursed. In the U.S., increased purchasing power of entities that negotiate on behalf of Medicare, Medicaid, and private sector beneficiaries, in part due to continued consolidation among healthcare providers, could result in further pricing pressures. In addition, recent legislation and ongoing political scrutiny on pricing, coverage and reimbursement could result in additional pricing pressures. Specifically, the Inflation Reduction Act of 2022 (IRA) has changed Medicare Part D benefit design and has subjected certain of the Company's products to government-established pricing beginning in 2026 and may subject additional products in the future. Failure to adhere to the government's interpretations of the law pending ongoing litigation may expose the Company to penalties. In addition, change to Medicare Part D could have a negative impact on U.S. Innovative Medicine sales. Further, increased third-party utilization of the 340B Federal Drug Discount Program from expanded interpretations of the statute and program abuse may have a negative impact on the Company's financial performance. Outside the U.S., numerous major markets, including the EU, United Kingdom, Japan and China, have pervasive government involvement in funding healthcare and, in that regard, directly or indirectly impose price controls, limit access to, or reimbursement for, the Company's products, or reduce the value of its intellectual property protection.

**[0000200406-26-000016:1A:22]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> The Company leverages the use of data science, machine learning and other forms of AI and emerging technologies across varying parts of its business and operations, and the introduction and incorporation of AI may result in unintended consequences or other new or expanded risks and liabilities. AI technology is continuously evolving, and the AI technologies we develop and adopt may become obsolete earlier than planned. Our investments in these technologies may not result in the benefits we anticipate or enable us to obtain or maintain a competitive advantage. The application of AI in our business is emerging and evolving alongside new laws and regulations that may entail significant costs or ultimately limit our ability to continue the use of these technologies. These technologies also carry inherent risks related to data privacy and security further described below.
> Risks related to financial and economic market conditions
> The Company faces a variety of financial, economic, legal, social and political risks associated with conducting business internationally.
> The Company's extensive operations and business activity throughout the world are accompanied by certain financial, economic, legal, social and political risks, including those listed below.

**[0000200406-26-000016:1A:35]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> To meet business objectives, the Company relies on both internal information technology (IT) systems and networks, and those of third parties and their vendors, to process and store sensitive data (including confidential research, business plans, financial information, intellectual property, and personal data that may be subject to legal protection) to ensure the continuity of the Company's supply chain and operations, and as part of many of the products we deliver to customers. The extensive range of information security and cybersecurity threats, which affect companies globally, pose a persistent risk to the security and availability of these systems and networks, including to customer products that are connected to or rely on such systems and networks, and the confidentiality, integrity, and availability of the Company's sensitive data. The Company assesses these threats, responds to attacks and breaches that it has experienced, and makes investments to increase internal protection, detection, and response capabilities, as well as ensure the Company's third-party providers have required capabilities and controls, to address this risk. Because of the frequently changing attack techniques, along with the increased volume and sophistication of the attacks and increasing use and reliance on third parties, there is the potential for the Company to be adversely impacted. This impact could result in reputational, competitive, operational or other business harm as well as financial costs and regulatory action. The increasing use of AI and other emerging technology could also increase these risks. The Company maintains cybersecurity insurance in the event of an information security or cyber incident; however, the coverage may not be sufficient to cover all financial, legal, business or reputational losses.

**Verdict:** Found

**Note:** 

### JNJ · candid_management

**Candid management.** Does management openly discuss setbacks, mistakes, declines and uncertainty in its own words, rather than only successes?

- **found** ("evidence found"): Management's own account of a setback that it attributes at least partly to the company's own decisions or execution; or a target or guidance of its own that was missed; or an acknowledged material weakness, restatement or write-down of something management chose (an acquisition, investment or project), stated plainly.
- **weak** ("evidence weak"): Declines or charges explained only by external factors (interest rates, currency, weather, regulation, the economy, product mix, litigation outcomes), even when quantified; or generic caution ('results may fluctuate', 'we face risks'); or a setback mentioned without explanation.
- **insufficient** ("insufficient evidence"): The retrieved text is promotional or boilerplate and gives nothing to judge candour either way, or MD&A and Risk Factors are missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.
- **Limitation:** Limitation: 10-K text is reviewed by lawyers, and candour is better judged from shareholder letters (outside this tool's scope). Do not read polished or detailed prose as candour;

Passages (Item 7, Item 1A), in filing order:

**[0000200406-26-000016:1A:1]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Item 1A. Risk factors
> An investment in the Company's common stock or debt securities involves risks and uncertainties. The Company seeks to identify, manage and mitigate risks to our business, but uncertainties and risks are difficult to predict and many are outside of the Company's control and cannot therefore be eliminated. In addition to the other information in this report and the Company's other filings with the SEC, investors should consider carefully the factors set forth below. Investors should be aware that it is not possible to predict or identify all such factors and that the following is not meant to be a complete discussion of all potential risks or uncertainties. If known or unknown risks or uncertainties materialize, the Company's business, results of operations or financial condition could be adversely affected, potentially in a material way.
> Risks related to our business, industry and operations
> The Company's businesses operate in highly competitive product markets and competitive pressures could adversely affect the Company's earnings.

**[0000200406-26-000016:1A:22]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> The Company leverages the use of data science, machine learning and other forms of AI and emerging technologies across varying parts of its business and operations, and the introduction and incorporation of AI may result in unintended consequences or other new or expanded risks and liabilities. AI technology is continuously evolving, and the AI technologies we develop and adopt may become obsolete earlier than planned. Our investments in these technologies may not result in the benefits we anticipate or enable us to obtain or maintain a competitive advantage. The application of AI in our business is emerging and evolving alongside new laws and regulations that may entail significant costs or ultimately limit our ability to continue the use of these technologies. These technologies also carry inherent risks related to data privacy and security further described below.
> Risks related to financial and economic market conditions
> The Company faces a variety of financial, economic, legal, social and political risks associated with conducting business internationally.
> The Company's extensive operations and business activity throughout the world are accompanied by certain financial, economic, legal, social and political risks, including those listed below.

**[0000200406-26-000016:1A:27]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> As described above, the Company has extensive operations and business activity throughout the world. Global tensions, conflict and/or war among any of the countries in which we conduct business or distribute our products may result in foreign currency volatility, decreased demand for our products in affected countries, and challenges to our global supply chain related to increased costs of materials and other inputs for our products and suppliers. Most recently, we have experienced, and expect to continue to experience, impacts to the Company's business resulting from the Russia-Ukraine war, conflict in the Middle East as well as increasing tensions between the U.S. and China. In response to heightened conflict, such as the Russia-Ukraine war, governments may impose export controls and broad financial and economic sanctions. Our business and operations may be further impacted by the imposition of tariffs, trade protection measures or other policies - including data localization laws and restrictions on data transfers - adopted by any country that favor domestic companies and technologies over foreign competitors. Additional sanctions or other measures may be imposed by the global community, including but not limited to limitations on our ability to file, prosecute and maintain patents, trademarks and other intellectual property rights. Furthermore, in some countries, action may be taken that allows companies and individuals to exploit inventions owned by patent holders from the United States and many other countries without consent or compensation and we may not be able to prevent third parties from practicing the Company's inventions or from selling or importing products. In addition, the U.S. government has imposed and/or announced the potential imposition of tariffs on products manufactured in other jurisdictions.

**[0000200406-26-000016:1A:29]** Item 1A · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> We currently maintain investment grade credit ratings with Moody's Investors Service and Standard & Poor's Ratings Services. Rating agencies routinely evaluate us, and their ratings of our long-term and short-term debt are based on a number of factors. Any downgrade of our credit ratings by a credit rating agency, whether as a result of our actions or factors which are beyond our control, can increase the cost of borrowing under any indebtedness we may incur, reduce market capacity for our commercial paper or require the posting of additional collateral under our derivative contracts. There can be no assurance that we will be able to maintain our credit ratings, and any additional actual or anticipated changes or downgrades in our credit ratings, including any announcement that our ratings are under review for a downgrade, may have a negative impact on our liquidity, capital position and access to capital markets.
> Risks related to the planned separation of our Orthopaedics business
> The planned separation of the Company's Orthopaedics business may not be completed on the terms or timeline currently contemplated, if at all, and may not achieve the expected results

**[0000200406-26-000016:7:24]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> •Acquired in-process research & development expense of $0.5 billion from the V-Wave acquisition and a Laminar milestone of $0.3 billion in the MedTech business in 2024
> •Leverage resulting from investment prioritization in the Innovative Medicine business
> In-Process Research and Development Impairments (IPR&D): In the fiscal year 2025, the Company recorded a charge of approximately $0.1 billion primarily related to a non-strategic asset acquired with Abiomed in 2022. In the fiscal year 2024, the Company recorded a charge of approximately $0.2 billion primarily associated with the M710 (biosimilar) asset acquired as part of the acquisition of Momenta Pharmaceuticals in 2020. There was also a partial impairment of this asset for $0.2 billion in the fiscal 2023. This asset is fully impaired.
> 30
> Other (Income) Expense, Net: Other (income) expense, net is the account where the Company records gains and losses related to the sale and write-down of certain investments in equity securities held by Johnson & Johnson Innovation - JJDC, Inc. (JJDC), changes in the fair value of securities, investment (income)/loss related to employee benefit programs, gains and losses on divestitures, certain transactional currency gains and losses, acquisition and divestiture related costs, litigation accruals and settlements, as well as royalty income.

**[0000200406-26-000016:7:27]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Interest (Income) Expense: Interest income in the fiscal year 2025 was $1.1 billion as compared to $1.3 billion in 2024. Interest income decreased as compared to the prior year driven by lower interest rates earned on cash balances. Interest expense in the fiscal year 2025 was $1.0 billion as compared to $0.8 billion in 2024. Interest expense was higher as compared to the prior year due to a higher average debt balance. Cash, cash equivalents and marketable securities totaled $20.1 billion at the end of 2025, and averaged $22.3 billion as compared to the cash, cash equivalents and marketable securities total of $24.5 billion and $23.7 billion average balance in 2024. The total debt balance at the end of 2025 was $47.9 billion with an average debt balance of $42.3 billion as compared to $36.6 billion at the end of 2024 and an average debt balance of $33.0 billion. The higher debt balance was due to the senior unsecured notes issued by the Company in the fiscal first quarter of 2025. The net proceeds from this offering were used to fund the Intra-Cellular Therapies, Inc. acquisition which closed on April 2, 2025 and for general corporate purposes.

**[0000200406-26-000016:7:35]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Cash and cash equivalents were $19.7 billion at the end of 2025 as compared to $24.1 billion at the end of 2024.
> The primary sources and uses of cash that contributed to the $4.4 billion decrease were:
> (Dollars in billions)
> $24.1 | Q4 2024 Cash and cash equivalents balance
> 24.5 | cash generated from operating activities
> (23.6) | net cash used for investing activities
> (5.5) | net cash used for financing activities
> 0.2 | effect of exchange rate and rounding
> $19.7 | Q4 2025 Cash and cash equivalents balance
> In addition, the Company had $0.4 billion in marketable securities at the end of fiscal year 2025 and $0.4 billion at the end of fiscal year 2024. See Note 1 to the Consolidated Financial Statements for additional details on cash, cash equivalents and marketable securities.
> 2025 Annual Report | 33
> Cash flow from operations of $24.5 billion was the result of:
> (Dollars In billions)
> $26.8 | Net Earnings
> 10.4 | non-cash expenses and other adjustments primarily for depreciation and amortization, stock-based compensation, asset write-downs, charges for acquired in-process research and development and deferred tax provision partially offset by net gain on sale of assets/businesses

**[0000200406-26-000016:7:56]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> The Company operates in certain countries where the economic conditions continue to present significant challenges. The Company continues to monitor these situations and take appropriate actions. Inflation rates continue to have an effect on worldwide economies and, consequently, on the way companies operate. The Company has accounted for operations in Argentina, Venezuela, Turkey and Egypt (beginning in the fiscal fourth quarter of 2024) as highly inflationary, as the prior three-year cumulative inflation rate surpassed 100%. This did not have a material impact to the Company's results in the period. In the face of increasing costs, the Company strives to maintain its profit margins through cost reduction programs, productivity improvements and periodic price increases.

**Verdict:** found

**Note:** 

### JNJ · rational_capital_allocation

**Rational capital allocation.** Does the filing show what management does with the cash the business generates (reinvestment, acquisitions, buybacks, dividends, debt repayment) and explain it? You judge whether it is documented concretely, not whether prices paid were good.

- **found** ("evidence found"): The filing quantifies at least one past action in the fiscal year (share repurchases, dividends, acquisitions, capital expenditure or debt repayment, with an amount) AND states a policy, priority or rationale for how cash is used. Not every action needs an amount.
- **weak** ("evidence weak"): Forward-looking plans only; or actions with no amount at all; or amounts with no stated policy, priority or rationale.
- **insufficient** ("insufficient evidence"): The retrieved text does not say what was done with cash, or MD&A is missing. If the retrieved text argues against the criterion, this is the verdict, and the rationale says so.
- **Year rule:** Judge the company's latest fiscal year, the year this 10-K reports on. Sentences about the prior-year comparative (the year before) count only as context: they cannot be the evidence for the verdict unless the filing says the same of the latest year.

Passages (Item 7), in filing order:

**[0000200406-26-000016:7:2]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> In October 2025, the Company announced its intention to separate its Orthopaedics business. The Company intends to explore multiple paths to effect the planned separation with a targeted completion within 18 to 24 months after the initial announcement.
> The Chief Operating Decision Maker (CODM) is the Company's Chief Executive Officer (Principal Executive Officer). The Executive Committee is Johnson & Johnson's senior leadership team responsible for setting the strategy and priorities of the Company and driving accountability at all levels. Within the strategic parameters provided by the Executive Committee, senior management groups at U.S. and international operating companies are each responsible for their own strategic plans and the day-to-day operations of those companies.

**[0000200406-26-000016:7:4]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> New products introduced within the past five years accounted for approximately 25% of 2025 sales. In 2025, $14.7 billion was invested in research and development reflecting management's commitment to create life-enhancing innovations and to create value through partnerships that will profoundly impact of health for humanity.
> Our approximately 138,200 employees are critical drivers of the Company's success. Employees are empowered and inspired to lead with Our Credo and purpose as guides. This allows every employee to use the Company's reach and size to advance the Company's purpose, and to also lead with agility and urgency. Leveraging the extensive resources across the enterprise enables the Company to innovate and execute with excellence. This ensures the Company can remain focused on addressing the unmet needs of society every day and invest for an enduring impact, ultimately delivering value to its patients, consumers and healthcare professionals, employees, communities and shareholders.
> 22
> Research &
> development
> Acquisitions*
> (net of cash acquired)
> Dividends paid
> per share
> * Includes business combinations and asset acquisitions
> Results of operations
> Analysis of consolidated sales

**[0000200406-26-000016:7:13]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> At least two biosimilars are pursuing regulatory approval for a SIMPONI biosimilar in the United States, which would likely result in a significant reduction in future sales.
> Neuroscience products, which include sales of CAPLYTA (lumateperone) acquired with the Intra-Cellular Therapies (Intra-Cellular) acquisition on April 2, 2025, achieved sales of $7.8 billion in 2025, representing an increase of 10.1% as compared to the prior year. Growth of SPRAVATO (esketamine) was driven by continued increased physician and patient demand. Growth was partially offset by the sales decline of INVEGA SUSTENNA / XEPLION / INVEGA TRINZA / TREVICTA primarily due to the impact of Medicare Part D redesign.
> Pulmonary Hypertension products achieved sales of $4.4 billion, representing an increase of 3.6% as compared to the prior year. Sales growth of OPSUMIT (macitentan)/OPSYNVI (macitentan/tadalafil) was driven by share gains and market growth partially offset by the impact of Medicare Part D redesign and UPTRAVI (selexipag) was driven by market growth partially offset by the impact of Medicare Part D redesign. The Company expects generic competition for OPSUMIT in 2026, which would likely result in a significant reduction in future sales.

**[0000200406-26-000016:7:27]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Interest (Income) Expense: Interest income in the fiscal year 2025 was $1.1 billion as compared to $1.3 billion in 2024. Interest income decreased as compared to the prior year driven by lower interest rates earned on cash balances. Interest expense in the fiscal year 2025 was $1.0 billion as compared to $0.8 billion in 2024. Interest expense was higher as compared to the prior year due to a higher average debt balance. Cash, cash equivalents and marketable securities totaled $20.1 billion at the end of 2025, and averaged $22.3 billion as compared to the cash, cash equivalents and marketable securities total of $24.5 billion and $23.7 billion average balance in 2024. The total debt balance at the end of 2025 was $47.9 billion with an average debt balance of $42.3 billion as compared to $36.6 billion at the end of 2024 and an average debt balance of $33.0 billion. The higher debt balance was due to the senior unsecured notes issued by the Company in the fiscal first quarter of 2025. The net proceeds from this offering were used to fund the Intra-Cellular Therapies, Inc. acquisition which closed on April 2, 2025 and for general corporate purposes.

**[0000200406-26-000016:7:36]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> (6.2) | an increase in other current and non-current assets
> (5.7) | a decrease in other current and non-current liabilities
> 2.4 | an increase in accounts payable and accrued liabilities
> (3.2) | an increase in accounts receivable and inventories
> $24.5 | Cash flow from operations
> Cash flow used for investing activities of $23.6 billion was primarily due to:
> (Dollars in billions)
> $(4.8) | additions to property, plant and equipment
> (17.5) | acquisitions, net of cash acquired
> 0.7 | proceeds from the disposal of assets/businesses, net
> (0.4) | acquired in-process research and development /related milestones
> 0.7 | net sales of investments
> (2.1) | credit support agreements activity, net
> (0.2) | other (including capitalized licenses and milestones)
> $(23.6) | Net cash used for investing activities
> Cash flow used for financing activities of $5.5 billion was primarily due to:
> (Dollars in billions)
> $(12.4) | dividends to shareholders
> (6.0) | repurchase of common stock
> 9.6 | net proceeds from short and long-term debt
> 3.4 | proceeds from stock options exercised/employee withholding tax on stock awards, net
> (0.2) | credit support agreements activity, net
> 0.1 | other and rounding
> $(5.5) | Net cash used for financing activities

**[0000200406-26-000016:7:37]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> As of December 28, 2025, the Company's notes payable and long-term debt was in excess of cash, cash equivalents and marketable securities. As of December 28, 2025, the net debt position was $27.8 billion as compared to the prior year of $12.1 billion. The debt balance at the end of 2025 was $47.9 billion as compared to $36.6 billion in 2024. In the fiscal first quarter of 2025, the Company issued senior unsecured notes for a total of $9.2 billion. For additional details on borrowings, see Note 7 to the Consolidated Financial Statements. The net proceeds from this offering were used to fund the Intra-Cellular Therapies, Inc. acquisition for approximately $14.5 billion which closed on April 2, 2025, and for general corporate purposes. Considering recent market conditions, the Company has re-evaluated its operating cash flows and liquidity profile and does not foresee any significant incremental risk. The Company anticipates that operating cash flows, the ability to raise funds from external sources, borrowing capacity from existing committed credit facilities and access to the commercial paper markets will continue to provide sufficient resources to fund operating needs, including the Company's reserve balance of approximately $3.4 billion related to talc matters, $2.0 billion related to the current portion of Corporate bonds due and the remaining

**[0000200406-26-000016:7:38]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> 34
> approximately $1.1 billion to settle opioid litigation (See Note 19 to the Consolidated Financial Statements for additional details). In addition, the Company monitors the global capital markets on an ongoing basis and from time to time may raise capital when market conditions are favorable.
> The following table summarizes the Company's material contractual obligations and their aggregate maturities as of December 28, 2025: To satisfy these obligations, the Company intends to use cash from operations.
> (Dollars in Millions) | Debt Obligations | Interest on Debt Obligations | Total
> 2026 | 2,000 | 1,458 | 3,458
> 2027 | 3,216 | 1,368 | 4,584
> 2028 | 3,128 | 1,273 | 4,401
> 2029 | 2,153 | 1,208 | 3,361
> 2030 | 2,689 | 1,118 | 3,807
> After 2030 | 28,252 | 10,306 | 38,558
> Total | 41,438 | 16,731 | 58,169
> For tax matters, see Note 8 to the Consolidated Financial Statements. For talc matters, see Note 19 to the Consolidated Financial Statements.
> Financing and market risk

**[0000200406-26-000016:7:43]** Item 7 · [filing](https://www.sec.gov/Archives/edgar/data/200406/000020040626000016/jnj-20251228.htm)

> Total borrowings at the end of 2025 and 2024 were $47.9 billion and $36.6 billion, respectively. The increase in the borrowings was primarily due to the issuance of new debt in the fiscal first quarter of 2025. The Company issued senior unsecured notes for approximately $9.2 billion. The net proceeds from this offering were used to fund the Intra-Cellular Therapies, Inc. acquisition for approximately $14.5 billion which closed on April 2, 2025, and for general corporate purposes. In 2025, net debt (cash and current marketable securities, net of debt) was $27.8 billion compared to net debt of $12.1 billion in 2024. Total debt represented 37.0% of total capital (shareholders' equity and total debt) in 2025 and 34.0% of total capital in 2024. Shareholders' equity per share at the end of 2025 was $33.86 compared to $29.70 at year-end 2024.
> A summary of borrowings can be found in Note 7 to the Consolidated Financial Statements.
> Dividends
> The Company increased its dividend in 2025 for the 63rd consecutive year. Cash dividends paid were $5.14 per share in 2025 and $4.91 per share in 2024.

**Verdict:** found 

**Note:** 

