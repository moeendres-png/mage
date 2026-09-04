# WS33 G3 non-AF event runtime — invalid pre-runtime successor

Classification: INVALID / NOT QUALIFICATION EVIDENCE

- RUN: `33853430763`
- JOB: `100961180376`
- SOURCE_HEAD: `b1f4181fb28e2e510a2036377472f8aefd43791e`
- SOURCE_TREE: `a8454c5f5bbf9ce16ea1fb7867e30cb921f367b9`

The workflow rewrite that bound the already-qualified principal observation/lifetime overlays accidentally truncated the immutable environment pin:

- intended `DIRECT_RUNTIME_SOURCE_HEAD`: `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`
- written invalid value: `d8af15cb879d93f272`

This was detected immediately after the commit and before this run could be used for any runtime adjudication. At checkpoint time the job had only entered checkout; the record/replay campaign had not run.

Consequences:

- this run is not eligible to qualify any path;
- no runtime or coverage conclusion may be derived from it;
- the only authorized repair is restoring the exact immutable `DIRECT_RUNTIME_SOURCE_HEAD` value in the workflow;
- the qualified observation/lifetime overlay additions themselves remain unchanged.
