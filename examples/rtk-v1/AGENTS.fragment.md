## RTK treatment policy

This selected treatment checkout uses pinned RTK 1.1.0 OSS on its process-local
PATH. Coordinator and workers read this policy from their actual checkout.
Prefix the verified commands explicitly: `rtk npm run typecheck`, `rtk npm run
build`, `rtk npm test`, `rtk npm run test:coverage`, and `rtk npm run test:browser`.
Preserve the project's scripts and arguments. There is no automatic rewrite hook.

Bare `rtk vitest` injects a JSON reporter that writes to a file in Vitest 5.1,
leaving stdout without counts or failure locations. Use `rtk npm test`; the tested
direct alternative is `rtk vitest run --reporter=default`. The specialized
Playwright filter changes its reporter to JSON and can omit warning output; keep
the npm browser script. Use unfiltered npm installation/audit commands when their
warnings matter: the RTK npm filter strips `npm WARN` and notices.

Check exit status, counts, skips and diagnostic locations. If a recovery hint
appears, use `rtk recall HASH --full`. Successful/small outputs, retention limits
and unavailable storage can leave no usable recall. A hint is not guaranteed.
Use `rtk bypass <original command>` when diagnosis needs raw output; record the
bypass and include its complete work in usage accounting. Do not treat omitted
output as a successful check. Do not activate a proxy, model route, global hook,
custom filter, provider setting or telemetry. Preserve native hook review/trust.
