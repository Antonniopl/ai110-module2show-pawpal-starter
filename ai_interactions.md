# AI interactions log

## Agent workflow

**Request:** Build the PawPal+ exercise using the linked CodePath starter and phase instructions, and identify what the owner of the fork needs to do.

**Actions:** The assistant inspected the starter's README, UI, reflection template and diagram; drafted the four-class design; implemented and ran the CLI before wiring the interface; added scheduling rules and ran automated tests. It also kept the draft diagram and recorded the final model separately.

**Design alternative reviewed:** A plan could automatically shift a lower-priority task after a collision. This implementation keeps the owner's entered times and explains what cannot fit instead. Tests cover equal starts, partial overlaps, and back-to-back tasks.

**Verification boundary:** The CLI, backend tests and form-handler test ran in the build environment. The native Streamlit smoke test needs the Streamlit package and was not run there. A human review of the browser interface and personal reflection remains separate. No separate VS Code chat transcripts or manual student test runs are claimed.
