# Evidence tags
- `doc:path:start-end`: captured source lines.
- `cmd:hash`: command execution record.
- `api:provider:request-id`: provider metadata.
- `event:run-id:sequence`: immutable run event.
- `[assume]`: explicit assumption, never confirmed.
- `[unknown]`: evidence unavailable.
A tag is valid only when its backing record exists in the persistent ledger. Ledger membership does not prove semantic entailment.
