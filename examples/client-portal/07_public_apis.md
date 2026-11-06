# Client Portal Required External Capabilities

## Status

**Requirements baseline; no endpoints or program signatures are defined**

## Client-facing reads

For the selected project, the client must be able to obtain:

- project summary and current Registry status;
- budget summary and budget source;
- ordered Budget Section summaries;
- confirmed included and excluded Expenses, with `Other expenses` visible
  separately;
- an Expense's Document when client-visible;
- manual Work Progress and completed work value;
- Work Payment summary and work balance;
- chronological Progress Photo gallery.

An archived project exposes the same historical reads in read-only mode.

## Operator mutations

For an active project, an authorized operator must be able to:

- create one confirmed Expense with one Document reference;
- allocate or manually split an Expense;
- assign an Expense to `Other expenses`;
- correct, include, or exclude an Expense;
- update manual Work Progress;
- register a Work Payment;
- publish a Progress Photo;
- change a Progress Photo caption, section association, or visibility.

Every mutation is rejected for an unknown or archived project.

## Registry integration

Client Portal requires the existing Registry HTTP capabilities for:

- listing active projects for authorized selection contexts;
- reading current project context;
- validating a project reference.

Client Portal consumes these existing contracts and does not redefine their
transport, identity, or response fields.

## PresuPro integration

Automatic budget publication is absent from the MVP.

Future capabilities are **NOT AVAILABLE**:

- obtain the latest approved immutable snapshot for a project;
- obtain a specific approved snapshot version for a project.

No URL, HTTP method, program signature, or approval workflow is established by
this document.
