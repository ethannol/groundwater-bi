# How I would deploy BI and analytics tooling

This is the opinion the rest of the repository exists to back up. It comes
from building a small stack end to end over real data and from watching
analytics deployments drift in practice.

## 1. Metric definitions live in git, not in the BI tool

Every BI tool lets you define a metric in its own UI. Every team that does
this ends up with three "active wells" numbers that disagree. The fix is
boring: metrics and dimensions are defined once, in version-controlled files
next to the warehouse models, and the BI tools consume those definitions.

In this repo that means dbt models with `meta` blocks (`warehouse/models/marts/schema.yml`)
and a LookML model (`looker/`) that mirrors them. A CI job builds the
warehouse and then checks the LookML against the resulting schema
(`tests/test_lookml.py`). A dimension that points at a renamed column fails
the pull request, not the Monday dashboard review.

The honest limit: without a live Looker instance the check is syntactic and
structural, not semantic. With one, Spectacles or Looker's validate API would
run in the same CI step.

## 2. Choose the tool by audience, and expect to run more than one

| Audience | Need | Tool shape | In this repo |
| --- | --- | --- | --- |
| Analysts and data scientists | Python, SQL, narrative, parameters | Notebook-first: Hex | `hex/` |
| Internal non-technical staff | Self-serve on governed fields | Modeled explores: Looker, Lightdash | `looker/` |
| Customers inside a product | Scoped, read-mostly, in our UI | Embedded: signed-token iframes or SDK | `embed/` |

Trying to make one tool serve all three is how you get a Hex app that is
really a dashboard with no governance, or a Looker explore that an analyst
exports to CSV to do the real work. Running two or three tools is fine as
long as they read the same semantic layer (point 1).

## 3. Authorization is decided by the application, enforced by the token

For embedded analytics the host application already knows who the viewer is
and what they own. Encode that in a short-lived signed token (locked
parameters in Metabase, user attributes in Looker SSO embed) and let the BI
tool enforce it. Never filter in the browser, and never hand a customer a
shared dashboard link with a "please only look at your rows" filter.

Row-level scoping belongs in the semantic layer too: `access_filter` on the
LookML explore, so an analyst inside the company gets the same enforcement
as a customer outside it.

## 4. Promote content like code: dev, review, prod

Looker and Lightdash both have the notion of a development branch per user
and a production branch. Use it. Dashboards and models get reviewed before
they reach the people who make decisions on them. Hex projects have
versioning, and on paid tiers can export to git; on the free tier the
"review" is a published-app boundary, which is weaker and should be said
out loud.

Practically: one warehouse schema per environment, one BI project per
environment, CI builds against the dev schema, promotion is a merge.

## 5. Keep the warehouse boring and the BI tool thin

Heavy logic in a BI tool is invisible to tests. In this repo every
transformation is a dbt model with tests (uniqueness, relationships,
accepted values, and a custom test that censored results keep their
interval). The BI layer adds labels, joins and measures, nothing more. If a
dashboard needs a new derived field, it goes into dbt first.

## 6. Be explicit about what the free tier does not give you

Git export in Hex, a Looker instance at all, interactive embedding in
Metabase, embedding in self-hosted Lightdash: all paid. That is not a reason
to avoid the free tiers, but a deployment plan that assumes those features
will quietly be there is going to be surprised. `docs/adr/0003` records what
this repo shows and what it only describes.

## 7. Watch the two failure modes that actually happen

- **Silent divergence.** A column changes meaning and every downstream number
  shifts. Mitigation: contracts and tests in the warehouse, structural checks
  on the semantic layer, and a changelog on the marts.
- **Cost surprises.** Per-viewer pricing on interactive embedding and
  per-editor pricing on notebooks both scale faster than teams expect.
  Decide up front which audiences get interactive access and which get
  static, and revisit quarterly.
