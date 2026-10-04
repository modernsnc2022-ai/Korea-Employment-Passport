# Company Community + Human Reality Check architecture

## Product intent
Korea Employment Passport adds a members-only, company-centric anonymous community on top of the official zero-broker route.

The sequence is:
1. Search the company.
2. Read existing public/official evidence.
3. Read or ask in the members-only anonymous board.
4. If evidence is still insufficient, request a paid Human Reality Check.
5. The operator reports verified facts and explicitly marks what could not be verified.

This service is information verification, not job placement and not a guarantee that an employer is good or bad.

## Security lock
The company board must fail closed until a real backend exists.

- GitHub Pages, localStorage, query parameters, or a KEP beta ID are **not authentication**.
- No member post, comment, image metadata, or account-to-pseudonym mapping may be shipped in public static JSON.
- Read/write access must be enforced server-side.
- A member can have a public pseudonym while the service retains a private account link for moderation, abuse response, and duplicate-account controls.
- Operator/admin access requires a distinct authorization role and auditable actions.

## Board model
Each normalized company has one board. Post types:
- question
- work experience
- dorm/context information
- pay/overtime experience
- transport/living environment
- photo context
- operator report summary

Every claim shown to another member carries an evidence label such as personal experience, verified worker evidence, public information, operator verified, or unverified.

## Privacy and moderation
Do not allow:
- passport/KTP/ARC numbers or identity-document images;
- private home/dorm addresses;
- doxxing;
- unblurred faces without consent;
- unnecessary vehicle plates;
- medical or bank information;
- unsupported accusations presented as verified fact.

Provide report, block, moderator review, and audit history.

## Paid Human Reality Check
The current public app can create a privacy-minimized request by email.

Tiers:
1. Detailed desk research.
2. Desk research + phone verification when lawful and feasible.
3. Field visit when lawful and feasible.

Price is quote-before-payment until commercial pricing is approved. A report must separate:
- official/public records;
- public observation;
- company response;
- verified worker experience;
- operator field observation;
- not verified.

No trespass, covert entry, or trade-secret recording.

## Advertising readiness
Advertising is disabled by default.

When enabled:
- all sponsored placements must say **IKLAN / SPONSOR**;
- ads never alter official answers, evidence ranking, or zero-broker guidance;
- a paid advertiser cannot be presented as required to complete the official EPS route;
- regulated advertisers must pass license/registration verification;
- no targeting based on passport/ARC, health, complaint content, private company-board posts, or other sensitive data;
- never imitate a government notice.

Initial candidate categories include licensed administrative services, insurance, telecom/SIM, regulated remittance/banking, Korean-language education, licensed legal/labor support, and general living services.

## Backend acceptance criteria
Do not set `community.status=live` until:
- server-side member authentication exists;
- per-company access is protected by authenticated APIs;
- create/read/update/delete permissions are tested;
- image upload uses private storage and metadata stripping;
- pseudonym mapping is non-public;
- report/block/moderation workflows exist;
- rate limiting and abuse controls exist;
- deletion/export/privacy handling exists;
- UI tests prove unauthenticated users cannot read post content.
