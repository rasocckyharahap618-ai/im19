# Evidence tags

- `doc:path:start-end`: exact source-file lines captured by the reader.
- `cmd:command-hash`: command execution record with stdout/stderr/exit code.
- `api:provider:request-id`: provider response metadata.
- `event:run-id:sequence`: immutable run event.
- `[assume]`: explicit assumption; never confirmed.
- `[unknown]`: evidence unavailable.

A tag is valid only when its backing record exists in the persistent ledger. Ledger membership does not prove semantic entailment; reviewers must assess whether the source supports the claim.
